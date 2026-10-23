import pytest

from sgat.assertions import AssertionFailed, ElementExpectation, assert_element
from sgat.batch import batch_execute, summarize
from sgat.models import ActionResult, UINode


def test_assert_element_expectations():
    node = UINode(node_id="b", text="Submit", clickable=True, bounds=(0, 0, 10, 10))
    assert_element(node, ElementExpectation(text_contains="subm"))  # case-insensitive
    assert_element(node, ElementExpectation(clickable=True))

    with pytest.raises(AssertionFailed):
        assert_element(None, ElementExpectation())  # expected to exist
    with pytest.raises(AssertionFailed):
        assert_element(node, ElementExpectation(text_equals="submit"))  # case matters here


def test_batch_isolates_errors():
    def ok():
        return ActionResult(action="ok", success=True)

    def boom():
        raise RuntimeError("device lost")

    results = batch_execute([ok, boom, ok])
    assert [r.success for r in results] == [True, False, True]
    assert "RuntimeError: device lost" in results[1].error
    assert summarize(results)["failed"] == 1

    early = batch_execute([ok, boom, ok], stop_on_error=True)
    assert len(early) == 2
