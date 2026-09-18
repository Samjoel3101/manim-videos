"""Structural contracts for every /lib component.

Cheap, deterministic, no rendering. Every component in lib/components must be
represented here — a component with no structural test is not done.
"""

import numpy as np
import pytest
from manim import Dot

from lib import theme
from lib.components.chat_ui import (
    ChatBubble,
    ChatInput,
    ChatWindow,
    StreamingBubble,
    TypingIndicator,
)
from lib.components.checks import CheckList, CheckRow
from lib.components.factory import Conveyor, PipelineBox, Station, rail_between
from lib.components.network import (
    DeviceNode,
    Link,
    Packet,
    PacketStream,
    RequestPath,
    ServerRack,
)
from lib.components.probability import ProbabilityBar, ProbabilityChart, softmax
from lib.components.stacked import INLINE_MIN_FRACTION, SegmentedBar
from lib.components.tokens import (
    TokenChip,
    TokenStrip,
    display_token,
    fake_token_id,
    simple_tokenize,
)
from lib.components.transformer import (
    AttentionLines,
    AttentionMatrix,
    LayerBlock,
    ResidualStream,
    TransformerStack,
)
from lib.components.vectors import (
    EmbeddingGrid,
    SemanticSpace,
    VectorArrow,
    VectorColumn,
    stable_vector,
)


# ---------------------------------------------------------------- chat_ui
def test_chat_bubble_rejects_unknown_sender():
    with pytest.raises(ValueError):
        ChatBubble("hi", "robot")


def test_chat_bubble_accent_follows_sender():
    assert ChatBubble("hi", "user").accent.to_hex() == theme.USER.to_hex()
    assert ChatBubble("hi", "assistant").accent.to_hex() == theme.ASSISTANT.to_hex()


def test_chat_bubble_wraps_to_max_width():
    bubble = ChatBubble("word " * 40, "user", max_width=4.0)
    assert bubble.width <= 4.0 + 1e-6


def test_chat_window_stacks_and_aligns_messages(in_frame):
    win = ChatWindow(width=6.0, height=5.5)
    first = win.add_message("Hello", "user")
    second = win.add_message("Hi there", "assistant")
    assert len(win.messages) == 2
    assert second.get_top()[1] < first.get_top()[1], "messages must stack downward"
    assert first.get_center()[0] > second.get_center()[0], "user right, assistant left"
    in_frame(win)


def test_chat_window_keeps_bubbles_clear_of_chrome():
    """A window sized for its transcript must not collide with divider/composer."""
    win = ChatWindow(width=6.0, height=6.2)
    first = win.add_message("How do you actually work?", "user")
    last = win.add_message("Let me walk you through it.", "assistant")
    assert first.get_top()[1] < win.divider.get_bottom()[1]
    assert last.get_bottom()[1] > win.input.get_top()[1]


def test_chat_window_scrolls_when_the_transcript_overflows():
    win = ChatWindow(width=6.0, height=4.0)
    first = win.add_message("one", "user")
    top_before = first.get_top()[1]
    win.add_message("two", "assistant")
    last = win.add_message("three", "user")
    assert first.get_top()[1] > top_before, "overflowing transcript must scroll upward"
    assert last.get_bottom()[1] > win.input.get_top()[1], "newest must clear the composer"
    # Anything pushed past the top of the message area is hidden, not drawn over
    # the title bar — manim has no clipping mask.
    assert first not in win.visible_messages()
    assert first.get_fill_opacity() == pytest.approx(0.0)


def test_chat_window_can_hide_the_composer():
    assert ChatWindow(show_input=False).input is None
    assert isinstance(ChatWindow(show_input=True).input, ChatInput)


def test_chat_input_clear_resets_to_placeholder():
    box = ChatInput(typed="hello there")
    assert box.full_text == "hello there"
    box.clear()
    assert box.full_text == ""
    assert box.text_mob.text.startswith("Message")
    # The caret returns to the left gutter, not to the end of the old text.
    assert box.caret.get_center()[0] < box.box.get_center()[0]


def test_streaming_bubble_hides_every_word_until_revealed():
    bubble = StreamingBubble("one two three four")
    assert bubble.word_count == 4
    assert all(w.get_fill_opacity() == pytest.approx(0.0) for w in bubble.words)


def test_streaming_bubble_reveals_a_prefix_in_order():
    bubble = StreamingBubble("one two three four")
    bubble.reveal(2)
    opacities = [w.get_fill_opacity() for w in bubble.words]
    assert opacities[:2] == pytest.approx([1.0, 1.0])
    assert opacities[2:] == pytest.approx([0.0, 0.0])
    bubble.reveal_next()
    assert bubble.revealed == 3


def test_streaming_bubble_clamps_out_of_range_reveals():
    bubble = StreamingBubble("one two")
    assert bubble.reveal(99).revealed == 2
    assert bubble.reveal(-5).revealed == 0


def test_streaming_bubble_wraps_within_max_width_and_does_not_reflow():
    bubble = StreamingBubble("alpha beta gamma delta epsilon zeta eta", max_width=3.0)
    assert len(bubble.lines) > 1, "long text must wrap"
    assert bubble.width <= 3.0 + 1e-6
    # Size is fixed up front: revealing words must not change the layout.
    before = (bubble.width, bubble.height, bubble.get_center()[0])
    bubble.reveal(bubble.word_count)
    after = (bubble.width, bubble.height, bubble.get_center()[0])
    assert before == pytest.approx(after)


def test_streaming_bubble_keeps_words_on_a_common_baseline():
    """Per-word mobjects get centred by arrange; a shared Text keeps baselines.

    Regression: "your" used to float above its neighbours because its bounding
    box includes a descender and arrange centres on the box, not the baseline.
    """
    bubble = StreamingBubble("noon noon noon", max_width=12.0)
    bottoms = [w.get_bottom()[1] for w in bubble.words]
    assert bottoms == pytest.approx([bottoms[0]] * len(bottoms), abs=1e-6)


def test_streaming_bubble_lets_descenders_drop_below_the_baseline():
    bubble = StreamingBubble("noon your", max_width=12.0)
    assert bubble.words[1].get_bottom()[1] < bubble.words[0].get_bottom()[1]


def test_streaming_bubble_rejects_empty_text():
    with pytest.raises(ValueError):
        StreamingBubble("   ")


def test_streaming_bubble_rejects_unknown_sender():
    with pytest.raises(ValueError):
        StreamingBubble("hi", sender="robot")


def test_typing_indicator_has_three_dots():
    assert len(TypingIndicator().dots) == 3


# ----------------------------------------------------------------- tokens
def test_simple_tokenize_keeps_leading_space_with_the_word():
    assert simple_tokenize("How does it work?") == ["How", " does", " it", " work", "?"]


def test_simple_tokenize_splits_long_words():
    pieces = simple_tokenize("tokenization")
    assert len(pieces) > 1
    assert "".join(pieces) == "tokenization"


def test_display_token_hides_the_space_marker_unless_asked():
    """The marker reads as a broken glyph on screen, so it is opt-in.

    Review note, not a preference: a chip showing "␣It" was read as a half-drawn
    box in front of the word rather than as "this token owns its leading space".
    """
    assert display_token(" the") == "the"
    assert display_token(" the", show_space=True) == "␣the"


def test_a_whitespace_only_token_still_draws_something():
    """Trimming to nothing would give a chip with an empty box in it."""
    assert display_token(" ") == "␣"


def test_chips_carry_the_full_token_even_when_it_is_not_shown():
    """The leading space belongs to the token; only the drawing drops it."""
    chip = TokenChip(" the")
    assert chip.token == " the"
    assert chip.text_mob.text == "the"
    assert TokenStrip([" the"], show_space=True)[0].text_mob.text == "␣the"


def test_fake_token_id_is_stable_and_in_vocab_range():
    assert fake_token_id(" the") == fake_token_id(" the")
    assert 0 <= fake_token_id(" the") < 50257


def test_token_strip_wraps_into_rows(in_frame):
    strip = TokenStrip("one two three four five six", per_line=3)
    assert len(strip.rows) == 2
    assert len(strip) == 6
    in_frame(strip)


def test_token_chip_highlight_round_trips():
    chip = TokenChip("hi")
    base = chip.box.get_stroke_width()
    chip.highlight()
    assert chip.box.get_stroke_width() > base
    chip.reset_highlight()
    assert chip.box.get_stroke_width() == pytest.approx(base)


def test_token_strip_shows_ids_when_asked():
    strip = TokenStrip("hi there", show_ids=True)
    assert strip.token_ids is not None
    assert all(chip.id_mob is not None for chip in strip.chips)


# ---------------------------------------------------------------- vectors
def test_stable_vector_is_deterministic_and_bounded():
    a, b = stable_vector("token", 8), stable_vector("token", 8)
    assert np.allclose(a, b)
    assert a.shape == (8,)
    assert a.min() >= -1.0 and a.max() <= 1.0
    assert not np.allclose(a, stable_vector("other", 8))


def test_vector_column_truncates_long_vectors():
    col = VectorColumn(stable_vector("x", 64), truncate_at=6)
    assert col.dimension == 64
    assert len(col.rows) == 6, "long vectors must elide, not draw 64 rows"


def test_embedding_grid_shape_matches_input():
    grid = EmbeddingGrid(np.zeros((3, 5)))
    assert len(grid.cells) == 3 and len(grid.cells[0]) == 5
    with pytest.raises(ValueError):
        EmbeddingGrid(np.zeros(4))


def test_vector_arrow_angle():
    assert VectorArrow(1, 0).angle == pytest.approx(0.0, abs=1e-6)
    assert VectorArrow(0, 1).angle == pytest.approx(np.pi / 2, abs=1e-6)


def test_semantic_space_pairs_dots_with_labels():
    space = SemanticSpace({"king": (0, 0), "queen": (1, 0)})
    assert len(space.dots) == len(space.labels) == 2


# ---------------------------------------------------------------- network
def test_request_path_orders_client_hop_server(in_frame):
    path = RequestPath()
    xs = [path.client.get_x(), path.hop.get_x(), path.server.get_x()]
    assert xs == sorted(xs)
    assert len(path.links) == 2
    in_frame(path)


def test_packet_flight_returns_an_animation():
    path = RequestPath()
    anim = Packet().flight(path.link_out)
    assert hasattr(anim, "begin")


def test_packet_stream_count():
    assert len(PacketStream(5).packets) == 5


def test_server_rack_slot_count():
    assert len(ServerRack(slots=6).slots) == 6


def test_link_label_is_optional():
    a, b = DeviceNode("a"), DeviceNode("b").shift(np.array([4.0, 0, 0]))
    assert Link(a, b).label_mob is None
    assert Link(a, b, label="POST").label_mob is not None


# ------------------------------------------------------------ probability
def test_softmax_normalises_and_respects_temperature():
    probs = softmax([2.0, 1.0, 0.0])
    assert sum(probs) == pytest.approx(1.0)
    assert probs[0] > probs[1] > probs[2]
    hot = softmax([2.0, 1.0, 0.0], temperature=10.0)
    assert max(hot) < max(probs), "higher temperature must flatten"
    with pytest.raises(ValueError):
        softmax([1.0], temperature=0)


def test_probability_chart_sorts_descending_and_truncates():
    chart = ProbabilityChart({"a": 0.1, "b": 0.6, "c": 0.3}, top_k=2)
    assert [k for k, _ in chart.items] == ["b", "c"]
    assert len(chart) == 2


def test_probability_chart_select_emphasises_one_bar():
    chart = ProbabilityChart({"a": 0.5, "b": 0.5})
    chosen = chart.select("a")
    assert chosen is chart.bar_for("a")
    assert chart.bar_for("b").bar.get_fill_opacity() < 1.0


def test_probability_bar_width_tracks_value():
    bar = ProbabilityBar("t", 0.5, bar_length=4.0)
    half = bar.bar.width
    bar.set_value(1.0)
    assert bar.bar.width > half


def test_label_width_reserves_a_column_so_bars_share_a_left_edge():
    """The shipped bug: rows laid out around their own text.

    ``label_width`` caps the label but the track was placed `next_to` it, so
    every row put its bar wherever that row's word happened to end and the chart
    came out with a ragged left edge.
    """
    short = ProbabilityBar("It", 0.6, label_width=1.3)
    long = ProbabilityBar("When", 0.6, label_width=1.3)
    assert short.track.get_left()[0] == pytest.approx(long.track.get_left()[0])
    assert short.label_mob.get_left()[0] == pytest.approx(long.label_mob.get_left()[0])


def test_every_row_in_a_chart_lines_up():
    """What the viewer actually sees: one left edge for the labels, one for the
    bars, and one for the values."""
    chart = ProbabilityChart(
        {" It": 3.2, " Your": 1.9, " The": 1.5, " When": 0.6}, logits=True
    )
    for attr in ("label_mob", "track", "value_mob"):
        edges = [getattr(bar, attr).get_left()[0] for bar in chart.bars]
        assert edges == pytest.approx([edges[0]] * len(edges)), f"{attr} is ragged"


# ------------------------------------------------------------ transformer
def test_transformer_stack_elides_the_middle(in_frame):
    stack = TransformerStack(n_layers=96, shown=4)
    assert len(stack) == 4
    assert stack.ellipsis is not None
    assert stack.blocks[-1].title_mob.text.endswith("96")
    in_frame(stack)


def test_transformer_stack_rejects_too_few_blocks():
    with pytest.raises(ValueError):
        TransformerStack(shown=1)


def test_layer_block_activation_round_trips():
    block = LayerBlock("Layer 1")
    base = block.box.get_stroke_width()
    block.activate()
    assert block.box.get_stroke_width() > base
    block.deactivate()
    assert block.box.get_stroke_width() == pytest.approx(base)


def test_attention_lines_encode_weight_and_validate_length():
    strip = TokenStrip("a b c d")
    lines = AttentionLines(strip[3], list(strip.chips)[:3], [0.7, 0.2, 0.1])
    widths = [ln.get_stroke_width() for ln in lines.lines]
    assert widths[0] > widths[1] > widths[2]
    assert lines.strongest() == 0
    with pytest.raises(ValueError):
        AttentionLines(strip[3], list(strip.chips)[:3], [0.5, 0.5])


def test_attention_matrix_is_causal_and_row_normalised():
    matrix = AttentionMatrix(["a", "b", "c"]).matrix
    assert matrix[0, 1] == pytest.approx(0.0), "causal mask must zero the future"
    assert matrix.sum(axis=1) == pytest.approx(np.ones(3))


def test_residual_stream_points_upward():
    arrow = ResidualStream(height=2.0).arrow
    assert arrow.get_end()[1] > arrow.get_start()[1]


# ---------------------------------------------------------------- factory
def test_station_fit_shrinks_oversized_content_into_the_bay():
    station = Station("Tokenizer", width=6.6, height=5.4)
    strip = TokenStrip("How does tokenization actually work here?")
    assert strip.width > station.slot_size[0], "test needs content wider than the slot"
    station.load(strip)
    assert strip.width <= station.slot_size[0] + 1e-6
    assert strip.height <= station.slot_size[1] + 1e-6


def test_station_fit_never_scales_content_up():
    station = Station("Tiny")
    dot = Dot(radius=0.05)
    before = dot.width
    station.fit(dot)
    assert dot.width == pytest.approx(before)


def test_station_content_lands_below_the_title():
    station = Station("Tokenizer", subtitle="text to ids")
    strip = TokenStrip("a b")
    station.load(strip)
    assert strip.get_top()[1] < station.subtitle_mob.get_bottom()[1] + 1e-6


def test_station_entry_and_exit_are_opposite_edges():
    station = Station("S")
    assert station.entry[0] < station.exit[0]
    assert station.entry[0] == pytest.approx(station.bay.get_left()[0])


def test_station_marquee_starts_invisible_and_reveals():
    station = Station("S", marquee="SAMPLE")
    assert station.marquee.get_fill_opacity() == pytest.approx(0.0)
    station.reveal_marquee()
    assert station.marquee.get_fill_opacity() == pytest.approx(1.0)
    # A station without a marquee must tolerate the same call.
    Station("S").reveal_marquee()


def test_station_marquee_is_large_enough_for_the_wide_shot():
    station = Station("Tokenizer", marquee="TOKENIZE")
    assert station.marquee.height > station.title_mob.height * 2


def test_station_marquee_is_clamped_to_the_bay_width():
    """Adjacent stations must never have colliding marquees."""
    station = Station("Tokenizer", width=6.4, marquee="DETOKENIZATION")
    assert station.marquee.width <= 6.4 + 1e-6


def test_station_marquee_sits_below_the_bay():
    """Below, so it cannot collide with an enclosing PipelineBox title."""
    station = Station("S", marquee="SAMPLE")
    assert station.marquee.get_top()[1] < station.bay.get_bottom()[1]


def test_station_activation_round_trips():
    station = Station("S")
    base = station.bay.get_stroke_width()
    station.activate()
    assert station.bay.get_stroke_width() > base
    station.deactivate()
    assert station.bay.get_stroke_width() == pytest.approx(base)


def test_station_clear_content_empties_the_slot():
    station = Station("S")
    station.load(TokenStrip("a b"))
    assert len(station.content) == 1
    station.clear_content()
    assert len(station.content) == 0


def test_pipeline_box_encloses_its_contents():
    left = Station("A")
    right = Station("B").shift(np.array([9.0, 0, 0]))
    box = PipelineBox([left, right], title="LLM")
    assert box.frame.get_left()[0] < left.get_left()[0]
    assert box.frame.get_right()[0] > right.get_right()[0]
    assert box.frame.get_bottom()[1] < left.get_bottom()[1]


def test_pipeline_box_rejects_empty_contents():
    with pytest.raises(ValueError):
        PipelineBox([], title="LLM")


def test_pipeline_box_rejects_an_unknown_title_side():
    with pytest.raises(ValueError):
        PipelineBox([Station("A")], title="LLM", title_side="underneath")


def test_a_side_title_leaves_the_top_midline_clear():
    """A tall box fed from above cannot wear its name across the top.

    The rail comes down the column's centre, and a title sized to be read at the
    pull-back is about as wide as the box, so a top title sits exactly where the
    rail has to arrive. Stopping the rail short of it is what made the machine
    look unconnected for the whole film.
    """
    top = Station("A")
    bottom = Station("B").shift(np.array([0, -9.0, 0]))
    box = PipelineBox([top, bottom], title="THE MODEL", title_side="side")

    midline = box.frame.get_center()[0]
    assert not (
        box.caption.get_left()[0] <= midline <= box.caption.get_right()[0]
    ), "the title still straddles the midline the rail comes down"
    assert box.caption.get_right()[0] <= box.frame.get_left()[0], "beside the box"
    # And it stays legible: a side title trades width for the height a tall box
    # has to spare, so it must not have been clamped into nothing.
    assert box.caption.height > box.frame.height * 0.4


def test_conveyor_path_is_traversable_end_to_end():
    rail = Conveyor([[0, 0, 0], [4, 0, 0], [4, -3, 0]])
    assert rail.point_at(0.0) == pytest.approx(np.array([0, 0, 0]), abs=1e-6)
    assert rail.point_at(1.0) == pytest.approx(np.array([4, -3, 0]), abs=1e-6)
    # Clamped, not wrapped or extrapolated.
    assert rail.point_at(2.0) == pytest.approx(rail.point_at(1.0))


def test_conveyor_chevrons_sit_on_the_rail():
    rail = Conveyor([[0, 0, 0], [6, 0, 0]], chevrons=3)
    assert len(rail.chevrons) == 3
    for mark in rail.chevrons:
        assert mark.get_center()[1] == pytest.approx(0.0, abs=0.05)


def test_conveyor_rejects_a_single_point():
    with pytest.raises(ValueError):
        Conveyor([[0, 0, 0]])


def test_rail_between_spans_the_gap_between_two_mobjects():
    a = Station("A")
    b = Station("B").shift(np.array([12.0, 0, 0]))
    rail = rail_between(a, b)
    assert rail.start[0] > a.get_right()[0]
    assert rail.end[0] < b.get_left()[0]


def test_chat_window_places_an_externally_built_bubble_in_the_transcript():
    """A StreamingBubble is built by the caller but must still flow in the window.

    Hand-positioning one relative to the last message is what let the final
    reply hang out of the bottom of the frame, drawn across the composer and
    everything beneath the window.
    """
    win = ChatWindow(width=9.6, height=7.0)
    first = win.add_message("How does it work?", "user")
    reply = StreamingBubble("Like this, roughly.", max_width=win.message_max_width)
    win.post(reply, "assistant")

    assert reply in win.messages
    assert reply.get_top()[1] < first.get_bottom()[1], "must stack below"
    assert reply.get_left()[0] >= win.frame.get_left()[0], "inside the left gutter"
    assert reply.get_right()[0] <= win.frame.get_right()[0]
    assert reply.get_bottom()[1] > win.input.get_top()[1], "must clear the composer"


def test_chat_window_reports_the_room_a_bubble_actually_has():
    win = ChatWindow(width=9.6, height=7.0)
    room = win.message_area_height
    assert room > 0
    # A bubble exactly that tall is the largest one the window can show: it
    # sits between the divider and the composer with nothing to spare.
    assert room == pytest.approx(
        win.divider.get_bottom()[1]
        - theme.PAD_MD
        - win.input.get_top()[1]
        - theme.PAD_MD
    )


def test_chat_window_place_rejects_an_unknown_sender():
    with pytest.raises(ValueError):
        ChatWindow().place(ChatBubble("hi"), "operator")


def test_station_cross_fades_its_two_labels_without_filling_the_icon():
    """The wide label starts hidden and comes up as an outline, not a blob."""
    station = Station(
        "Embedding",
        subtitle="ids \u2192 vectors",
        icon="grid-3x3",
        width=9.6,
        height=2.4,
        header_side="left",
        shot_width=13.6,
        wide_label="Embedding",
        wide_width=48.0,
    )
    assert station.wide_label is not None
    assert station.wide_label_words.get_fill_opacity() == pytest.approx(0.0)

    station.set_wide_opacity(1.0)
    assert station.wide_label_words.get_fill_opacity() == pytest.approx(1.0)
    outlines = [
        p
        for p in station.wide_label_icon.parts
        if not getattr(p, "_is_indicator_dot", False)
    ]
    assert all(p.get_fill_opacity() == pytest.approx(0.0) for p in outlines)

    # One animation per fading piece of each label, on the channel it uses.
    assert len(station.reveal_wide(1.0)) == 4


def test_station_header_leaves_the_slot_most_of_a_wide_bay():
    """The content is the subject of a close-up; the header only names it."""
    station = Station(
        "Transformer",
        subtitle="96 layers",
        icon="layers",
        width=9.6,
        height=2.4,
        header_side="left",
        shot_width=13.6,
    )
    slot_width, _ = station.slot_size
    assert station.header.width <= 9.6 * 0.4
    assert slot_width > station.header.width


# ----------------------------------------------------------------- checks
def test_check_rows_share_all_three_column_edges():
    """The ragged-row bug again, in a new component.

    Rows laid out around their own label put every marker wherever that row's
    word happened to start. The columns are reserved instead, so a list of
    "WAF" and "rate limit" lines up. Invisible to the snapshot gate — a 16x16
    luminance signature cannot see a marker move a third of a unit — so it is
    asserted here or not at all.
    """
    checks = CheckList(
        ["WAF", ("bot score", "0.02"), ("rate limit", "12 / 60")], width=3.4
    )
    markers = [row.marker.get_left()[0] for row in checks.rows]
    labels = [row.label_mob.get_left()[0] for row in checks.rows]
    assert markers == pytest.approx([markers[0]] * len(markers), abs=1e-6)
    assert labels == pytest.approx([labels[0]] * len(labels), abs=1e-6)


def test_check_row_detail_column_is_right_aligned():
    """Details of different lengths must end on the same edge, not start on one."""
    checks = CheckList([("a", "0.02"), ("bbbbbb", "12 / 60")], width=3.4)
    rights = [row.detail_mob.get_right()[0] for row in checks.rows]
    assert rights == pytest.approx([rights[0]] * len(rights), abs=1e-6)
    # And the reserved column is what fixes it, so the edge is at `width`.
    assert rights[0] == pytest.approx(checks[0].get_left()[0] + 3.4, abs=1e-6)


def test_a_pending_tick_is_invisible_on_stroke_not_on_fill():
    """The tick is two Lines. It has no fill, and must never be given one.

    A blanket `set_opacity` would raise fill opacity as well and draw the tick
    as a pair of filled slivers — the same fill-vs-stroke trap as the glow
    halos (session 5) and the Lucide icons (session 6).
    """
    row = CheckRow("WAF")
    assert row.state == "pending"
    for line in row.tick:
        assert line.get_stroke_opacity() == pytest.approx(0.0)
        assert line.get_fill_opacity() == pytest.approx(0.0)


def test_mark_pass_lights_the_tick_without_touching_the_submobject_list():
    """`row.animate.mark_pass()` only interpolates if the tree stays the same."""
    row = CheckRow("bot score", detail="0.02")
    before = len(row.submobjects)
    row.mark_pass()
    assert row.state == "passed"
    assert all(line.get_stroke_opacity() == pytest.approx(1.0) for line in row.tick)
    assert all(line.get_fill_opacity() == pytest.approx(0.0) for line in row.tick)
    assert len(row.submobjects) == before


def test_a_passed_row_takes_its_accent_from_the_theme():
    default = CheckRow("WAF").mark_pass()
    assert default.marker.get_fill_color().to_hex() == theme.ASSISTANT.to_hex()
    warned = CheckRow("quota", color=theme.WARN).mark_pass()
    assert warned.marker.get_fill_color().to_hex() == theme.WARN.to_hex()


def test_mark_fail_uses_the_error_colour_and_the_cross_not_the_tick():
    """A red tick would read as "passed, but bad". A failure needs its own mark."""
    row = CheckRow("rate limit").mark_fail()
    assert row.state == "failed"
    assert row.marker.get_fill_color().to_hex() == theme.ERROR.to_hex()
    assert all(line.get_stroke_opacity() == pytest.approx(1.0) for line in row.cross)
    assert all(line.get_stroke_opacity() == pytest.approx(0.0) for line in row.tick)


def test_check_row_reset_round_trips():
    row = CheckRow("session")
    row.mark_pass().reset()
    assert row.state == "pending"
    assert all(line.get_stroke_opacity() == pytest.approx(0.0) for line in row.tick)
    assert row.marker.get_stroke_color().to_hex() == theme.FG_FAINT.to_hex()


def test_check_list_addresses_rows_by_label_and_by_index():
    checks = CheckList(["session", ("plan", "pro")])
    assert len(checks) == 2
    assert checks.row_for("plan") is checks[1]
    assert checks.row_for("nope") is None


def test_check_list_pass_all_yields_one_builder_per_row():
    checks = CheckList(["a", "b", "c"])
    anims = checks.pass_all()
    assert len(anims) == 3
    # Returned, not played: the choreography owns the lag and the easing.
    assert all(hasattr(a, "build") for a in anims)


def test_check_list_rejects_an_empty_list():
    with pytest.raises(ValueError):
        CheckList([])


# ---------------------------------------------------------------- stacked
def test_segmented_bar_drawn_widths_fill_the_bar():
    bar = SegmentedBar({"a": 3, "b": 1}, length=5.0, labels="none")
    assert sum(seg.width for seg in bar.segments) == pytest.approx(5.0, abs=1e-6)


def test_a_sliver_is_clamped_to_min_segment_so_the_beat_can_happen():
    """7 tokens in 3,937 is 0.18% of the bar: sub-pixel, i.e. the beat fails.

    The clamp is the component's reason to exist, so it is asserted rather than
    trusted.
    """
    bar = SegmentedBar(
        {"prompt": 3930, "yours": 7}, length=5.0, min_segment=0.05, labels="none"
    )
    assert bar.segments[1].width >= 0.05 * 5.0 - 1e-6
    assert sum(seg.width for seg in bar.segments) == pytest.approx(5.0, abs=1e-6)


def test_fractions_report_the_unclamped_truth():
    """Legibility wins the drawing; the model keeps the real number."""
    bar = SegmentedBar(
        {"prompt": 3930, "yours": 7}, length=5.0, min_segment=0.05, labels="none"
    )
    assert bar.fractions[1] == pytest.approx(7 / 3937)
    assert sum(bar.fractions) == pytest.approx(1.0)
    assert bar.drawn_fractions[1] > bar.fractions[1], "the DRAWN slice is lifted"


def test_min_segment_zero_draws_the_honest_bar():
    bar = SegmentedBar(
        {"prompt": 3930, "yours": 7}, length=5.0, min_segment=0.0, labels="none"
    )
    assert bar.drawn_fractions == pytest.approx(bar.fractions)


def test_the_clamp_holds_when_several_segments_are_slivers():
    """Lifting the small ones shrinks the big ones, which can push another
    under the floor. The redistribution iterates for exactly that reason."""
    bar = SegmentedBar(
        {"a": 1000, "b": 2, "c": 2, "d": 2}, length=6.0, min_segment=0.1,
        labels="none",
    )
    assert all(seg.width >= 0.1 * 6.0 - 1e-6 for seg in bar.segments)
    assert sum(seg.width for seg in bar.segments) == pytest.approx(6.0, abs=1e-6)


def test_segmented_bar_refuses_an_impossible_floor():
    with pytest.raises(ValueError):
        SegmentedBar({"a": 1, "b": 1, "c": 1}, min_segment=0.5)


def test_segmented_bar_rejects_an_unknown_label_mode_and_an_empty_bar():
    with pytest.raises(ValueError):
        SegmentedBar({"a": 1}, labels="sideways")
    with pytest.raises(ValueError):
        SegmentedBar({})


def test_legend_rows_share_a_left_edge_and_a_value_edge():
    bar = SegmentedBar(
        {"system prompt": 2400, "tool definitions": 1150, "your message": 7},
        length=5.0,
        labels="legend",
    )
    swatches = [row[0].get_left()[0] for row in bar.legend]
    names = [row[1].get_left()[0] for row in bar.legend]
    values = [row[2].get_right()[0] for row in bar.legend]
    assert swatches == pytest.approx([swatches[0]] * 3, abs=1e-6)
    assert names == pytest.approx([names[0]] * 3, abs=1e-6)
    assert values == pytest.approx([values[0]] * 3, abs=1e-6)


def test_legend_prints_the_true_value_not_the_drawn_one():
    bar = SegmentedBar({"prompt": 3930, "yours": 7}, min_segment=0.2)
    assert bar.legend[1][2].text == "7"


def test_set_shown_hides_by_opacity_and_never_by_removal():
    """The choreography grows the bar with `.animate.set_shown(k)`, which only
    interpolates if the submobject tree is constant."""
    bar = SegmentedBar({"a": 1, "b": 1, "c": 1}, labels="legend")
    counts = (len(bar.submobjects), len(bar.segments), len(bar.legend))
    bar.set_shown(1)
    assert bar.segments[0].get_fill_opacity() == pytest.approx(1.0)
    assert bar.segments[2].get_fill_opacity() == pytest.approx(0.0)
    assert (len(bar.submobjects), len(bar.segments), len(bar.legend)) == counts
    bar.set_shown(3)
    assert bar.segments[2].get_fill_opacity() == pytest.approx(1.0)


def test_emphasise_dims_the_others_and_leaves_hidden_segments_hidden():
    bar = SegmentedBar({"a": 1, "b": 1, "c": 1}, labels="legend")
    bar.set_shown(2).emphasise("a", dim_others=0.3)
    assert bar.segments[0].get_fill_opacity() == pytest.approx(1.0)
    assert bar.segments[1].get_fill_opacity() == pytest.approx(0.3)
    assert bar.segments[2].get_fill_opacity() == pytest.approx(0.0), "still unrevealed"


def test_emphasise_names_the_alternatives_when_it_cannot_find_the_segment():
    bar = SegmentedBar({"a": 1, "b": 1})
    with pytest.raises(KeyError):
        bar.emphasise("c")


def test_inline_labels_are_dropped_for_segments_too_narrow_to_hold_them():
    """A name squeezed into 5% of the bar is a smear, not a label."""
    bar = SegmentedBar(
        {"cached prefix": 3900, "new tail": 37},
        length=5.0,
        labels="inline",
        min_segment=0.02,
    )
    assert bar.drawn_fractions[1] < INLINE_MIN_FRACTION
    assert len(bar.label_groups[0]) == 1, "the wide segment keeps its label"
    assert len(bar.label_groups[1]) == 0, "the sliver does not"
    # Parallel to the segments either way, so index arithmetic never branches.
    assert len(bar.label_groups) == len(bar.segments)


# ------------------------------------------- probability: value_format kwarg
def test_probability_bar_value_format_is_backwards_compatible():
    """The default must be byte-identical to the f-string it replaced, or the
    20 approved baselines silently become wrong."""
    assert ProbabilityBar("t", 0.5).value_mob.text == f"{0.5:.2f}"
    assert ProbabilityBar("t", 0.5).value_format == "{:.2f}"


def test_probability_bar_renders_the_value_in_the_given_format():
    """A quota meter is a ProbabilityBar with a different number format — a
    keyword argument, not a second class (AGENTS rule 1)."""
    meter = ProbabilityBar("tokens/min", 0.62, value_format="{:.0%}")
    assert meter.value_mob.text == "62%"


def test_probability_bar_keeps_its_format_across_set_value():
    meter = ProbabilityBar("batch", 0.1, value_format="{:.0%}")
    meter.set_value(0.83)
    assert meter.value_mob.text == "83%"
