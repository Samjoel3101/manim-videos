"""Structural contracts for every /lib component.

Cheap, deterministic, no rendering. Every component in lib/components must be
represented here — a component with no structural test is not done.
"""

import numpy as np
import pytest

from lib import theme
from lib.components.chat_ui import ChatBubble, ChatInput, ChatWindow, TypingIndicator
from lib.components.network import (
    DeviceNode,
    Link,
    Packet,
    PacketStream,
    RequestPath,
    ServerRack,
)
from lib.components.probability import ProbabilityBar, ProbabilityChart, softmax
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


def test_typing_indicator_has_three_dots():
    assert len(TypingIndicator().dots) == 3


# ----------------------------------------------------------------- tokens
def test_simple_tokenize_keeps_leading_space_with_the_word():
    assert simple_tokenize("How does it work?") == ["How", " does", " it", " work", "?"]


def test_simple_tokenize_splits_long_words():
    pieces = simple_tokenize("tokenization")
    assert len(pieces) > 1
    assert "".join(pieces) == "tokenization"


def test_display_token_makes_whitespace_visible():
    assert display_token(" the") == "␣the"


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
