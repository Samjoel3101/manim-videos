"""Visual regression: every registered component view must match its baseline.

This is the tier that catches "still constructs, now looks wrong". Baselines
live in tests/baselines/ and are approved deliberately, never auto-written by a
failing run.
"""

import pytest

from tests.snapshot_cases import CASES


@pytest.mark.parametrize("name", sorted(CASES))
def test_component_matches_baseline(name, snapshot):
    snapshot(name, CASES[name])
