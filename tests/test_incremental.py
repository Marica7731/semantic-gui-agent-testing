from sgat.models import UINode
from sgat.semantic.incremental import UITreeCache


def _tree():
    return UINode(
        node_id="root",
        class_name="Frame",
        bounds=(0, 0, 100, 200),
        children=[
            UINode(node_id="a", text="alpha", bounds=(0, 0, 50, 50)),
            UINode(node_id="b", text="beta", bounds=(50, 0, 100, 50)),
        ],
    )


def test_unchanged_tree_is_a_cache_hit():
    cache = UITreeCache()
    first = cache.update(_tree())
    second = cache.update(_tree())
    assert first == second
    assert cache.stats.hits == 1
    assert cache.stats.full_rebuilds == 1
    assert cache.stats.partial_updates == 0


def test_changed_subtree_counts_partial_update_with_reuse():
    cache = UITreeCache()
    cache.update(_tree())
    changed = _tree()
    changed.children[1].text = "gamma"
    cache.update(changed)
    assert cache.stats.partial_updates == 1
    assert cache.stats.reused_subtrees >= 1
