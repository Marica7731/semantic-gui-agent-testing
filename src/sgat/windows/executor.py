"""Windows executor: UI Automation via pywinauto, imported lazily.

Uses the ``uia`` backend so every element exposes AutomationId / ControlType,
which is what makes semantic (coordinate-free) localization possible.
"""

from __future__ import annotations

from ..executor import GUIExecutor
from ..models import Screen, UINode

CLICKABLE_CONTROL_TYPES = {
    "Button",
    "MenuItem",
    "Hyperlink",
    "CheckBox",
    "RadioButton",
    "ListItem",
    "TabItem",
    "ComboBox",
    "SplitButton",
}


class WindowsExecutor(GUIExecutor):
    platform = "windows"

    def __init__(self, window_title: str = "", backend: str = "uia") -> None:
        super().__init__()
        self.window_title = window_title
        self.backend = backend
        self._window = None

    def connect(self) -> None:
        try:
            from pywinauto import Desktop
        except ImportError as exc:
            raise RuntimeError(
                "pywinauto is not installed. "
                "Install with: pip install 'semantic-gui-agent-testing[windows]'"
            ) from exc
        desktop = Desktop(backend=self.backend)
        if self.window_title:
            self._window = desktop.window(title_re=self.window_title)
        else:
            self._window = desktop.top_window()
        self._window.set_focus()

    def disconnect(self) -> None:
        self._window = None

    def dump_screen(self) -> Screen:
        if self._window is None:
            raise RuntimeError("WindowsExecutor is not connected; call connect() first")
        info = self._window.element_info()
        return Screen(root=self._convert(info), package=info.name or "")

    def _convert(self, info) -> UINode:
        rect = info.rectangle
        control_type = info.control_type or ""
        node = UINode(
            node_id=f"win-{info.automation_id or control_type or 'window'}",
            class_name=control_type,
            text=info.rich_text or info.name or "",
            content_desc=info.help_text or "",
            resource_id=info.automation_id or "",
            bounds=(rect.left, rect.top, rect.right, rect.bottom),
            clickable=control_type in CLICKABLE_CONTROL_TYPES,
            enabled=bool(info.enabled),
        )
        node.children = [self._convert(child) for child in info.children()]
        return node

    def tap_point(self, x: int, y: int) -> None:
        from pywinauto import mouse

        mouse.click(button="left", coords=(x, y))

    def type_text(self, text: str) -> None:
        from pywinauto import keyboard

        keyboard.send_keys(text)

    def press_back(self) -> None:
        from pywinauto import keyboard

        keyboard.send_keys("%{LEFT}")  # Alt+Left: the common "back" navigation
