"""Android executor: adb + uiautomator2, both imported lazily.

The XML hierarchy parser is pure and unit-tested without a device; only the
``connect``/act primitives require a real device and the ``android`` extra.
"""

from __future__ import annotations

import itertools
import xml.etree.ElementTree as ET

from ..executor import GUIExecutor
from ..models import Screen, UINode


def parse_bounds(raw: str) -> tuple[int, int, int, int]:
    """Parse uiautomator bounds like ``[100,200][300,260]``."""
    left, top, right, bottom = (int(v) for v in raw.replace("][", ",").strip("[]").split(","))
    return left, top, right, bottom


def parse_uiautomator_xml(xml_text: str, package: str = "") -> Screen:
    """Convert a ``uiautomator dump`` XML hierarchy into a UINode tree."""
    counter = itertools.count()
    root_elem = ET.fromstring(xml_text)
    if root_elem.tag == "hierarchy":
        node_elems = root_elem.findall("node")
        if len(node_elems) != 1:
            raise ValueError(f"unexpected hierarchy layout with {len(node_elems)} root nodes")
        root_elem = node_elems[0]

    def convert(elem: ET.Element) -> UINode:
        attrib = elem.attrib
        node = UINode(
            node_id=f"n{next(counter)}",
            class_name=attrib.get("class", ""),
            text=attrib.get("text", ""),
            content_desc=attrib.get("content-desc", ""),
            resource_id=attrib.get("resource-id", ""),
            bounds=parse_bounds(attrib.get("bounds", "[0,0][0,0]")),
            clickable=attrib.get("clickable", "false").lower() == "true",
            enabled=attrib.get("enabled", "true").lower() == "true",
        )
        node.children = [convert(child) for child in elem.findall("node")]
        return node

    return Screen(root=convert(root_elem), package=package or root_elem.attrib.get("package", ""))


class AndroidExecutor(GUIExecutor):
    """Drives real Android devices through uiautomator2."""

    platform = "android"

    def __init__(self, serial: str | None = None, package: str = "") -> None:
        super().__init__()
        self.serial = serial
        self.package = package
        self._device = None

    def connect(self) -> None:
        try:
            import uiautomator2 as u2
        except ImportError as exc:
            raise RuntimeError(
                "uiautomator2 is not installed. "
                "Install with: pip install 'semantic-gui-agent-testing[android]'"
            ) from exc
        self._device = u2.connect(self.serial or "")

    def disconnect(self) -> None:
        self._device = None

    def dump_screen(self) -> Screen:
        if self._device is None:
            raise RuntimeError("AndroidExecutor is not connected; call connect() first")
        xml_text = self._device.dump_hierarchy()
        return parse_uiautomator_xml(xml_text, package=self.package)

    def tap_point(self, x: int, y: int) -> None:
        self._device.click(x, y)

    def type_text(self, text: str) -> None:
        self._device.send_keys(text, clear=True)

    def press_back(self) -> None:
        self._device.press("back")
