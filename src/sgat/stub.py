"""In-memory scriptable executor: no device required.

Used by unit tests, MCP smoke tests and benchmark dry runs. ``tap_behavior``
controls whether tapping a clickable element changes its text, simulating a
UI state transition.
"""

from __future__ import annotations

from .executor import GUIExecutor
from .models import Screen, UINode


def _default_root() -> UINode:
    return UINode(
        node_id="root",
        class_name="android.widget.FrameLayout",
        bounds=(0, 0, 1080, 2400),
        children=[
            UINode(node_id="title", class_name="android.widget.TextView", text="Settings", bounds=(0, 100, 1080, 200)),
            UINode(
                node_id="ok",
                class_name="android.widget.Button",
                text="OK",
                resource_id="com.example:id/ok",
                bounds=(100, 300, 400, 380),
                clickable=True,
            ),
            UINode(
                node_id="cancel",
                class_name="android.widget.Button",
                text="Cancel",
                resource_id="com.example:id/cancel",
                bounds=(500, 300, 800, 380),
                clickable=True,
            ),
            UINode(
                node_id="search",
                class_name="android.widget.EditText",
                resource_id="com.example:id/search",
                bounds=(0, 500, 1080, 600),
                clickable=True,
            ),
        ],
    )


class StubExecutor(GUIExecutor):
    platform = "stub"

    def __init__(self, root: UINode | None = None, package: str = "stub.app", tap_behavior: str = "move") -> None:
        super().__init__()
        self._root = root or _default_root()
        self.package = package
        self.tap_behavior = tap_behavior
        self.connected = False
        self.taps: list[tuple[int, int]] = []
        self.typed: list[str] = []
        self.back_count = 0

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def dump_screen(self) -> Screen:
        return Screen(root=self._root, package=self.package)

    def tap_point(self, x: int, y: int) -> None:
        self.taps.append((x, y))
        if self.tap_behavior == "move":
            for node in self._root.walk():
                if node.clickable and node.center() == (x, y):
                    node.text = f"{node.text} (tapped)"

    def type_text(self, text: str) -> None:
        self.typed.append(text)

    def press_back(self) -> None:
        self.back_count += 1
