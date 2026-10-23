from sgat.models import Screen, SemanticTarget, UINode
from sgat.semantic.matcher import SemanticMatcher


def _screen():
    return Screen(
        root=UINode(
            node_id="root",
            class_name="Frame",
            bounds=(0, 0, 1080, 2400),
            children=[
                UINode(
                    node_id="submit",
                    class_name="android.widget.Button",
                    text="Submit",
                    resource_id="com.app:id/submit",
                    bounds=(0, 0, 200, 80),
                    clickable=True,
                ),
                UINode(
                    node_id="label",
                    class_name="android.widget.TextView",
                    text="Submit your form below",
                    bounds=(0, 100, 1080, 160),
                ),
            ],
        )
    )


def test_exact_resource_id_wins():
    result = SemanticMatcher().match(_screen(), SemanticTarget(id="t", resource_id="com.app:id/submit"))
    assert result.best.node.node_id == "submit"
    assert result.best.matched_via == "resource_id"
    assert result.best.score == 1.0
    assert not result.ambiguous


def test_substring_text_match_scores_partial():
    result = SemanticMatcher().match(_screen(), SemanticTarget(id="t", text="your form"))
    assert result.best.node.node_id == "label"
    assert 0.5 <= result.best.score < 1.0


def test_identical_candidates_are_flagged_ambiguous():
    screen = Screen(
        root=UINode(
            node_id="root",
            class_name="Frame",
            bounds=(0, 0, 100, 100),
            children=[
                UINode(node_id="ok1", class_name="Button", text="OK", bounds=(0, 0, 40, 40), clickable=True),
                UINode(node_id="ok2", class_name="Button", text="OK", bounds=(60, 0, 100, 40), clickable=True),
            ],
        )
    )
    result = SemanticMatcher().match(screen, SemanticTarget(id="t", text="OK"))
    assert result.ambiguous
    assert result.best is not None
