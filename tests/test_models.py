import pytest

from sgat.models import SemanticTarget, UINode


def test_semantic_target_requires_id_and_a_hint():
    with pytest.raises(ValueError):
        SemanticTarget(id="")
    with pytest.raises(ValueError):
        SemanticTarget(id="blank")  # no locator hints at all
    SemanticTarget(id="ok", text="OK")  # valid: one hint is enough


def test_ui_node_roundtrip_and_flatten():
    tree = UINode(
        node_id="root",
        class_name="Frame",
        bounds=(0, 0, 100, 200),
        children=[UINode(node_id="child", text="hi", bounds=(0, 0, 50, 50))],
    )
    restored = UINode.from_dict(tree.to_dict())
    assert restored.children[0].text == "hi"
    assert restored.children[0].bounds == (0, 0, 50, 50)
    assert [n.node_id for n in tree.walk()] == ["root", "child"]
    assert tree.children[0].center() == (25, 25)
