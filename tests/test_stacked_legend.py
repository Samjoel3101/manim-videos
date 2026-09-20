"""The legend is a table, and both of its columns are one type size.

The bug this file exists to stop shipping again: in ``labels="legend"`` mode the
NAME was run through ``utils.fit_text`` and the VALUE never was, so a legend too
narrow for its names came out with the numbers at full size and the words at a
third of it. Measured on the orchestrator beat of ``chatgpt_request_lifecycle``,
after ``station.fit`` at a 16-unit shot: names at 0.0066-0.0077 of frame height
against ``typography.MIN_READABLE`` of 0.020, values at 0.0208-0.0251. Every
number readable, not one word readable.

That is the same "drawn and unreadable" failure ``_build_inline`` already guards
against, one column over, and neither gate could see it: the row edges stayed
perfectly aligned (so the structural alignment test passed) and a 16x16
luminance signature cannot tell small type from large (so the snapshot passed).
"""

import pytest

from lib import theme, typography
from lib.components.stacked import SegmentedBar

#: Names far too long for the legend widths below — the condition under which
#: the old code shrank the names and left the numbers alone.
LONG = {
    "system prompt": 2400,
    "tool definitions": 1150,
    "memory + prefs": 380,
    "your message": 7,
}

FRAME = 16.0


def _columns(bar):
    """(name, value) mobject pairs, one per legend row."""
    return [(list(row)[1], list(row)[2]) for row in bar.legend]


def _type_scale(mob, string: str, *, mono: bool) -> float:
    """How much this drawn label was shrunk from its natural size."""
    natural = typography.text("micro", string, frame_width=FRAME, mono=mono)
    return float(mob.height) / float(natural.height)


def test_a_cramped_legend_shrinks_names_and_values_by_the_same_factor():
    """The headline contract: one type size for the whole table.

    Fails against the pre-fix component, where only the name column went
    through ``fit_text``: the names came back at ~0.3x and the values at 1.0x.
    """
    bar = SegmentedBar(
        LONG, length=2.3, thickness=0.4, labels="legend", legend_width=2.0,
        min_segment=0.035, frame_width=FRAME,
    )
    name_scales = [
        _type_scale(name, bar.names[i], mono=False)
        for i, (name, _) in enumerate(_columns(bar))
    ]
    value_scales = [
        _type_scale(value, bar._value_text(i), mono=True)
        for i, (_, value) in enumerate(_columns(bar))
    ]
    assert max(name_scales) - min(name_scales) < 0.02, name_scales
    assert max(value_scales) - min(value_scales) < 0.02, value_scales
    assert abs(name_scales[0] - value_scales[0]) < 0.02, (name_scales, value_scales)


def test_the_legend_fits_under_the_bar_at_the_bars_own_width():
    """``legend_side="below"`` is what buys these names a readable size.

    Beside a 2.3-long bar a name has ~0.6 units and "tool definitions" needs
    2.10. Under it, it has the bar's full width, so nothing is shrunk at all and
    both columns land above the readability floor.
    """
    bar = SegmentedBar(
        LONG, length=4.9, thickness=0.4, labels="legend", legend_side="below",
        min_segment=0.035, frame_width=FRAME,
    )
    for i, (name, value) in enumerate(_columns(bar)):
        shares = (
            typography.measure(name, FRAME),
            typography.measure(value, FRAME),
        )
        assert min(shares) >= typography.MIN_READABLE, (bar.names[i], shares)
    assert bar.legend.get_top()[1] < bar.segments.get_bottom()[1], "below the bar"
    assert bar.legend.get_left()[0] == pytest.approx(
        bar.segments.get_left()[0], abs=1e-6
    ), "and sharing its left edge"
    # Sized against the bar, so the numbers right-align with the bar's end.
    assert bar.legend.width == pytest.approx(bar.bar_length, abs=0.01)


def test_the_value_column_stays_right_aligned_across_rows():
    """The column discipline the previous fix established, still holding.

    Scaling both columns together must not reintroduce a ragged number edge.
    """
    bar = SegmentedBar(
        LONG, length=4.9, thickness=0.4, labels="legend", legend_side="below",
        min_segment=0.035, frame_width=FRAME,
    )
    rights = [float(value.get_right()[0]) for _, value in _columns(bar)]
    lefts = [float(name.get_left()[0]) for name, _ in _columns(bar)]
    assert max(rights) - min(rights) < 1e-6, rights
    assert max(lefts) - min(lefts) < 1e-6, lefts


def test_strict_legend_refuses_a_width_that_would_be_illegible():
    """Follows the constructor's inline precedent: refuse, and say how to fix it.

    Without ``strict_legend`` the same call still draws — existing callers are
    not broken by the guard — but anything whose legibility matters opts in.
    """
    with pytest.raises(typography.UnreadableTextError) as excinfo:
        SegmentedBar(
            LONG, length=2.3, thickness=0.4, labels="legend", legend_width=2.0,
            min_segment=0.035, frame_width=FRAME, strict_legend=True,
        )
    message = str(excinfo.value)
    assert "MIN_READABLE" in message
    assert "legend_side='below'" in message, "the message must name a way out"
    # And it draws, loudly-unset, when the caller has not asked for the guard.
    SegmentedBar(
        LONG, length=2.3, thickness=0.4, labels="legend", legend_width=2.0,
        min_segment=0.035, frame_width=FRAME,
    )


def test_legend_side_is_validated_like_every_other_mode_argument():
    # Imported here, not at module scope, so the headline test above still
    # runs (and fails) against a component that predates this constant.
    from lib.components.stacked import LEGEND_SIDES

    assert LEGEND_SIDES == ("right", "below")
    with pytest.raises(ValueError):
        SegmentedBar({"a": 1}, labels="legend", legend_side="underneath")


def test_a_legend_with_room_to_spare_is_never_scaled_up():
    """``fit_text`` never scaled up and neither does the shared factor."""
    bar = SegmentedBar(
        {"a": 1, "b": 2}, length=6.0, labels="legend", legend_width=6.0,
        frame_width=FRAME,
    )
    for i, (name, _) in enumerate(_columns(bar)):
        assert _type_scale(name, bar.names[i], mono=False) == pytest.approx(1.0)


def test_the_orchestrator_beats_legend_is_readable_after_the_station_fits_it():
    """The end-to-end claim, at the shot and the slot the film actually uses.

    ``Station.fit`` scales the whole content group down to the bay's slot, so a
    legend measured on a bare bar proves nothing: this is the measurement that
    decides whether a viewer can read the words.
    """
    from manim import DOWN, RIGHT, VGroup

    from lib.components.factory import Station
    from lib.components.glyph import Glyph

    station = Station(
        "Orchestrator", subtitle="context · prompt · routing", icon="database",
        accent=theme.ASSISTANT, width=10.0, height=3.2, header_side="left",
    )
    bar = SegmentedBar(
        LONG, length=4.9, thickness=0.4, labels="legend", legend_side="below",
        strict_legend=True, min_segment=0.035, frame_width=FRAME,
    )
    # The chips row belongs in this test, because the chips are what set the
    # fit factor. Measured while fixing the legend: at PAD_MD between them the
    # row came out 5.207 against a 4.90 slot, so `fit` was WIDTH-bound on three
    # badges and was shrinking the bar and the legend to suit them. A version
    # of this test that fitted `VGroup(bar)` alone therefore proved the one
    # thing it was written to prove only by accident, and would have stayed
    # green if a later edit to the chips put the names back under the floor.
    def chip(icon: str, name: str) -> VGroup:
        return VGroup(
            Glyph(icon, color=theme.ASSISTANT, height=0.24, stroke_width=2.0),
            typography.text(
                "micro", name, frame_width=FRAME, color=theme.FG_MUTED
            ),
        ).arrange(RIGHT, buff=theme.PAD_XS)

    sources = VGroup(
        chip("database", "conversation"),
        chip("sparkles", "memory"),
        chip("file-text", "files"),
    ).arrange(RIGHT, buff=theme.PAD_SM)
    content = VGroup(sources, bar).arrange(DOWN, buff=theme.PAD_XS)
    station.fit(content, margin=1.0)

    for i, (name, value) in enumerate(_columns(bar)):
        n = typography.measure(name, FRAME)
        v = typography.measure(value, FRAME)
        assert n >= typography.MIN_READABLE, (bar.names[i], n)
        assert v >= typography.MIN_READABLE, (bar.names[i], v)
    assert bar.segments.width >= 2.0, "the bar stays expressive"
    # The 7-token sliver is held up by min_segment and must still be drawn.
    assert bar.segments[-1].width > 0.1, bar.segments[-1].width


def test_strict_legend_does_not_refuse_a_legend_with_room_to_spare():
    """The guard fires on the type SIZE, never on which glyphs are in the name.

    ``typography.measure`` is a bounding box, so a name with no ascender, no
    descender and no capital measures its x-height — 0.0174 at role ``micro``,
    under MIN_READABLE at scale 1.0 however wide the legend is. A guard built
    on it refused this bar: eight units of legend for a row needing under two,
    nothing scaled, and an error message advising the caller to widen a legend
    that was already four times wider than it had to be. Two of its three
    escapes could not help and the third was to turn the guard off.

    Every name here is x-height-only on purpose. If this test ever fails, the
    guard has gone back to measuring glyphs instead of type size.
    """
    bar = SegmentedBar(
        {"sources": 1, "runs": 2, "errors": 3},
        length=8.0, labels="legend", legend_side="below",
        strict_legend=True, frame_width=FRAME,
    )
    shares = [typography.measure(name, FRAME) for name, _ in _columns(bar)]
    assert min(shares) < typography.MIN_READABLE, (
        "this test is pointless unless these names really do measure below the "
        f"floor by bounding box: {shares}"
    )


def test_strict_legend_still_refuses_a_legend_that_really_is_crushed():
    """The other half: the guard must not have been defanged by the fix.

    Long names in a 1.2-unit legend are genuinely scaled far below the floor,
    and that is the case the guard exists for.
    """
    with pytest.raises(typography.UnreadableTextError) as excinfo:
        SegmentedBar(
            LONG, length=2.3, labels="legend", legend_width=1.2,
            strict_legend=True, min_segment=0.035, frame_width=FRAME,
        )
    message = str(excinfo.value)
    # The message has to name the scale it applied and the room it needed,
    # because "too narrow" without a number is not actionable.
    assert "scaled to" in message
    assert "units and has" in message
