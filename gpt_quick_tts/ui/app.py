from __future__ import annotations

"""Prompt-toolkit based console UI."""

import shutil
import threading
from typing import Callable, List, Optional

from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.mouse_events import MouseButton, MouseEventType
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea

from ..engine import TTSEngine, TTSCallbacks
from ..state import ConsoleState
from ..styles import StyleDefinition


class ConsoleApp:
    """Thin UI layer that wires keyboard/mouse events to the engine and state."""

    def __init__(self, state: ConsoleState, engine: TTSEngine, on_shutdown: Optional[Callable[[], None]] = None):
        self.state = state
        self.engine = engine
        self.on_shutdown = on_shutdown
        self._workers: List[threading.Thread] = []
        self._quit_confirm = False
        self._app: Optional[Application] = None

    # ------------------------------------------------------------------ UI rendering
    def _style_label(self, definition: StyleDefinition, active: bool) -> str:
        hotkey = definition.hotkey.upper() if definition.hotkey else "-"
        state_text = "ON" if active else "OFF"
        return f"[{definition.name} ({hotkey}) {state_text}]"

    def _render_header(self):
        fragments = []

        def add(text: str, style: Optional[str] = None, handler=None):
            cls = f"class:{style}" if style else ""
            if handler:
                fragments.append((cls, text, handler))
            else:
                fragments.append((cls, text))

        # Helpers
        try:
            cols = get_app().output.get_size().columns
        except Exception:
            cols = shutil.get_terminal_size((80, 20)).columns

        add("=" * 50 + "\n")
        add("TTS Console - GPT Quick TTS\n", "title")
        add("Styles: Ctrl+(Key) — click labels to toggle\n", "info")

        cur_len = 0
        first_in_line = True

        for definition, active in self.state.styles.display_items():
            label = self._style_label(definition, active)

            def handler_factory(name: str):
                def handler(mouse_event):
                    try:
                        if (
                            getattr(mouse_event, "event_type", None) == MouseEventType.MOUSE_UP
                            and getattr(mouse_event, "button", None) == MouseButton.LEFT
                        ):
                            self._toggle_style(name)
                            return None
                        return NotImplemented
                    except Exception:
                        return NotImplemented

                return handler

            handler = handler_factory(definition.name)
            label_len = len(label) + (0 if first_in_line else 1)
            if cur_len + label_len > max(10, cols - 10):
                add("\n")
                cur_len = 0
                first_in_line = True

            if not first_in_line:
                add(" ")
                cur_len += 1

            style_class = "style_on" if active else "style_off"
            add(label, style_class, handler)
            cur_len += len(label)
            first_in_line = False

        add("\n")
        voice_line = f"Voice: [{self.state.voice}] ({len(self.state.voices)} available) - Ctrl+V to cycle | Streaming: {'ON' if self.state.streaming else 'OFF'} (Ctrl+S)\n"
        add(voice_line, "info")
        add(f"Status: [{self.state.status}]\n", "status")
        add("-" * 42 + "\n")
        return fragments

    def _render_log(self):
        log_lines = self.state.logs()
        if log_lines:
            content = "\n".join(f"<log>{line}</log>" for line in log_lines)
        else:
            content = "<log>(no messages yet)</log>"
        return HTML(f"\n<info>Log:</info>\n{content}\n")

    def _invalidate(self):
        try:
            if self._app:
                self._app.invalidate()
        except Exception:
            pass

    # ------------------------------------------------------------------ Actions
    def _toggle_style(self, name: str):
        active = self.state.toggle_style(name)
        state_text = "ON" if active else "OFF"
        self.state.add_log(f"{name} style toggled {state_text}")
        self._invalidate()

    def _cycle_voice(self):
        new_voice = self.state.cycle_voice()
        self.state.add_log(f"Voice changed to {new_voice}")
        self._invalidate()

    def _toggle_streaming(self):
        new_state = self.state.toggle_streaming()
        self.state.add_log(f"Streaming mode toggled {'ON' if new_state else 'OFF'}")
        self._invalidate()

    def _set_status(self, status: str):
        self.state.set_status(status)
        self._invalidate()

    def _submit_text(self, text: str):
        if not text:
            return

        callbacks = TTSCallbacks(on_status=self._set_status, on_log=self.state.add_log)

        def worker():
            try:
                self.engine.speak(text, self.state.voice, self.state.styles, self.state.streaming, callbacks)
            finally:
                self._invalidate()

        thread = threading.Thread(target=worker, daemon=False)
        thread.start()
        self._workers.append(thread)

    def _confirm_quit(self, app: Application):
        if self._quit_confirm:
            app.exit()
            return

        active_workers = [t for t in self._workers if t.is_alive()]
        if self.state.streaming or active_workers:
            self.state.add_log("Quit requested — active streaming/workers detected. Press Ctrl+Q again to confirm exit.")
        else:
            self.state.add_log("Press Ctrl+Q again within 2s to quit")
        self._invalidate()
        self._quit_confirm = True

        def _reset():
            self._quit_confirm = False
            self._invalidate()

        timer = threading.Timer(2.0, _reset)
        timer.daemon = True
        timer.start()

    # ------------------------------------------------------------------ App lifecycle
    def run(self):
        text_area = TextArea(prompt="TTS> ", multiline=False, wrap_lines=False)

        header_control = FormattedTextControl(text=self._render_header, focusable=False, show_cursor=False)
        header_window = Window(content=header_control, dont_extend_height=True)

        log_control = FormattedTextControl(text=self._render_log, focusable=False)
        log_window = Window(content=log_control, height=13, dont_extend_height=True)

        separator = Window(content=FormattedTextControl(text=HTML("<info>================</info>")), height=1, dont_extend_height=True)

        root_container = HSplit([header_window, log_window, separator, Window(height=1), text_area])
        layout = Layout(root_container)

        kb = KeyBindings()

        # Primary controls
        @kb.add("c-q")
        def _(event):
            self._confirm_quit(event.app)

        @kb.add("c-v")
        def _(event):
            self._cycle_voice()

        @kb.add("c-s")
        def _(event):
            self._toggle_streaming()

        # Style bindings
        used_ctrl_keys = {"q", "v", "s", "enter"}
        blacklist = {"h", "m"}  # avoid common terminal navigation bindings
        for hotkey, name in self.state.styles.hotkey_lookup().items():
            if hotkey in used_ctrl_keys or hotkey in blacklist:
                continue

            @kb.add(f"c-{hotkey}")
            def _style_toggle(event, _name=name):
                self._toggle_style(_name)

        @kb.add("enter")
        def _(event):
            text = text_area.text.strip()
            if not text:
                return
            text_area.text = ""
            if text == ":q":
                event.app.exit()
                return
            self._submit_text(text)
            self._invalidate()

        style = Style.from_dict(
            {
                "title": "#ffffff bold",
                "info": "#ffffff",
                "style_on": "#00ff00 bold",
                "style_off": "#ff0000",
                "status": "#ffffff",
                "log": "#808080",
            }
        )

        self._app = Application(layout=layout, key_bindings=kb, style=style, full_screen=True, mouse_support=True)

        try:
            self._app.run()
        finally:
            self._cleanup()

    def _cleanup(self):
        try:
            for thread in list(self._workers):
                try:
                    thread.join(timeout=2.0)
                except Exception:
                    pass
            if self.engine and getattr(self.engine, "audio", None):
                try:
                    self.engine.audio.close()
                except Exception:
                    pass
            if self.on_shutdown:
                try:
                    self.on_shutdown()
                except Exception:
                    pass
        finally:
            pass
