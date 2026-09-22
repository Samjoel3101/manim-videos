"""The whole film: one continuous 59.5-second shot down the tokenizer bench.

No cuts. The set (`tokenizer_set.py`) is built once and the camera walks it left
to right, drops down the consequence spur, and pulls all the way back at the
end — where the bench itself shrinks into one node of the plant the previous
episode toured.

The through-line is one payload, never destroyed, only transformed:

    a typed question -> a row of characters -> THE CHARACTERS GOING DARK ->
    chips with no letters in them -> an ordered merge list -> a row of integers
    -> a number on a meter -> a bar beside Hindi and Burmese -> one small bay in
    a plant the viewer has already walked through

Pacing is a decision, not an outcome: every `run_time` below is part of the
59.50s budget laid out in `../script.md`, and each beat method carries its
target timecode. Changing one means re-balancing its neighbours inside the same
beat — the beat boundaries are fixed.

**The claims this film makes about numbers are asserted, not proof-read.** The
snapshot gate compares a 16x16 luminance grid and is structurally incapable of
noticing that a correct-looking animation says something false, so the token
accounting is `assert`ed in the beats that draw it. See `script.md`.
"""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    MoveAlongPath,
    MovingCameraScene,
    Transform,
    VGroup,
)

from lib import camera, motion, routing, theme, typography
from lib.components.chat_ui import StreamingBubble
from lib.components.tokens import TokenChip, TokenStrip

try:  # pragma: no cover - whichever branch runs, the other is unreachable
    from .tokenizer_set import (
        COUNTER_X,
        COUNTER_YS,
        QUESTION,
        SENTENCE_IDS,
        SENTENCE_TOKENS,
        SHOT_BENCH,
        SHOT_CHAT,
        SHOT_IDS,
        SHOT_METER,
        RAMP_LABELS,
        SHOT_TIGHT,
        SHOT_WIDE,
        WIDE_PAD,
        WORD,
        WORD_IDS,
        WORD_TOKENS,
        TokenizerSet,
    )
except ImportError:
    from tokenizer_set import (  # type: ignore[no-redef]
        COUNTER_X,
        COUNTER_YS,
        QUESTION,
        SENTENCE_IDS,
        SENTENCE_TOKENS,
        SHOT_BENCH,
        SHOT_CHAT,
        SHOT_IDS,
        SHOT_METER,
        RAMP_LABELS,
        SHOT_TIGHT,
        SHOT_WIDE,
        WIDE_PAD,
        WORD,
        WORD_IDS,
        WORD_TOKENS,
        TokenizerSet,
    )

#: The wrong answer the film opens on. It is wrong on purpose, and the film's
#: argument is that it is not a counting failure.
WRONG_ANSWER = 'There are 2 r\'s in "strawberry".'


class TheTokenizer(MovingCameraScene):
    def construct(self) -> None:
        theme.apply(self)

        self.set = TokenizerSet()
        self.add(self.set)

        #: Everything that shrinks into the ghost node in B6. The set plus every
        #: prop a beat stages, collected as it is staged — see `_stage`.
        self.bench = VGroup(self.set)

        camera.snap_to(self, self.set.chat, width=SHOT_CHAT)
        # Room under the window for B0's caption. A 9.6x6.0 window in a 13-wide
        # frame leaves 0.65 of margin, and the caption needs more than that.
        self.camera.frame.shift(DOWN * 0.6)

        self.beat_cold_open()      # 0.00 -> 5.00
        self.beat_the_line()       # 5.00 -> 11.50
        strip = self.beat_the_split()          # 11.50 -> 21.00
        self.beat_the_table()      # 21.00 -> 33.50
        self.beat_the_ids(strip)   # 33.50 -> 40.00
        self.beat_the_meter()      # 40.00 -> 51.00
        self.beat_where_it_sits()  # 51.00 -> 59.50

    # ==================================================== 0.00 -> 5.00  B0
    def beat_cold_open(self) -> None:
        """The strawberry question, a wrong answer, and stillness."""
        s = self.set
        chat = s.chat
        chat.add_message(QUESTION, "user")

        reply = StreamingBubble(WRONG_ANSWER, max_width=chat.message_max_width)
        self._fit_in_window(reply, chat)
        chat.post(reply, "assistant")
        reply.reveal(0)
        self._stage(reply)
        self.add(reply)
        reply.body.set_opacity(0.0)

        self.play(
            FadeIn(reply.body),
            reply.animate.reveal(reply.word_count),
            run_time=1.3,
            rate_func=motion.ENTER,
        )
        # The "2" is the third word. Addressed through the bubble's own word map
        # rather than by glyph index, so re-wording the answer cannot silently
        # emphasise the wrong thing.
        assert reply.word_count == len(WRONG_ANSWER.split())
        self.play(
            reply.words[2].animate.scale(1.5).set_color(theme.ERROR),
            run_time=0.8,
            rate_func=motion.SNAP,
        )

        # Complete stillness, long enough to feel wrong.
        self.wait(1.0)

        self.opening_caption = self._caption(
            "it is not bad at counting.",
            np.array([-26.0, -1.55, 0.0]),
            SHOT_CHAT,
        )
        self.play(FadeIn(self.opening_caption), run_time=0.8, rate_func=motion.ENTER)
        self.wait(1.1)

    # =================================================== 5.00 -> 11.50  B1
    def beat_the_line(self) -> None:
        """Characters on the bench, the three r's seen once, then the wipe."""
        s = self.set
        row = s.row

        # The question becomes a physical thing the moment it leaves the bubble,
        # and it travels the DRAWN rail rather than a line between two centres.
        courier = typography.text(
            "label", QUESTION, frame_width=SHOT_BENCH, color=theme.FG, mono=True
        )
        courier.move_to(s.chat.get_right() + RIGHT * theme.PAD_MD)
        flight = routing.join(
            s.rail_question_split,
            [s.rail_question_split.end, row.get_center()],
        )
        self.add(courier)
        self.play(
            MoveAlongPath(courier, flight),
            camera.focus(
                self, s.split.bay, width=SHOT_BENCH, shift=UP * 0.9, run_time=1.3
            ),
            FadeOut(self.opening_caption),
            run_time=1.3,
            rate_func=motion.MOVE,
        )

        self._stage(row, s.row_counter)
        self.play(
            motion.enter(row.cells, scale=0.8, lag=motion.LAG * 0.25),
            FadeOut(courier),
            run_time=0.8,
            rate_func=motion.ENTER,
        )

        # TOKEN ACCOUNTING 1: the row is derived from the question and counts
        # its own cells, so the copy on screen and the number under it cannot
        # drift apart. Scoped to the WORD: the question also holds a standalone
        # `r` in `r's`, which is not part of the claim and does not pulse.
        assert len(row.cells) == len(QUESTION) == 27
        assert row.r_count_in(WORD) == WORD.count("r") == 3

        self.play(
            *row.highlight_anims(theme.WARN),
            FadeIn(s.row_counter),
            run_time=1.0,
            rate_func=motion.ENTER,
        )
        self.wait(0.7)

        # THE WIPE. The single most important frame in the film: everything
        # before it has letters and nothing after it does. Full 1.2s, left to
        # right, and deliberately undecorated.
        self.play(
            LaggedStart(*row.wipe_anims(), lag_ratio=0.028),
            s.row_counter.animate.set_color(theme.FG_FAINT).set_opacity(0.35),
            run_time=1.2,
            rate_func=motion.SHARP,
        )

        self.line_caption = self._caption(
            "this is the last frame with letters in it.",
            np.array([-13.0, -0.55, 0.0]),
            SHOT_BENCH,
        )
        self.play(FadeIn(self.line_caption), run_time=0.8, rate_func=motion.ENTER)
        self.wait(0.7)

    # ================================================== 11.50 -> 21.00  B2
    def beat_the_split(self):
        """Seven chips, the leading space, and the strawberry punchline.

        Respecified against the build brief, which drew NINE chips with
        `st|raw|berry` among them. In the real sentence ` strawberry` — with its
        leading space — is one vocabulary entry, id 101830, and the sentence is
        seven tokens. The claim the brief asked to preserve survives in a
        stronger form: it is not that the r's were split across three pieces,
        it is that the whole word is one opaque integer with no piece boundary
        anywhere near them. See `script.md`.
        """
        s = self.set
        row = s.row

        self.play(
            camera.focus(
                self, s.split.bay, width=SHOT_BENCH, shift=UP * 0.35, run_time=1.2
            ),
            *[
                cell.animate.move_to(s.split.slot_center).set_opacity(0.0)
                for cell in row.cells
            ],
            FadeOut(s.row_counter),
            FadeOut(self.line_caption),
            run_time=1.2,
            rate_func=motion.MOVE,
        )
        self.remove(row)
        self.bench.remove(row, s.row_counter)

        # TOKEN ACCOUNTING 2: the chips and the ids are ONE list. The strip is
        # built once, with the verified ids passed explicitly so `fake_token_id`
        # cannot invent anything, and B4 flips this same object. There is no
        # second list of ids anywhere in this scene.
        strip = TokenStrip(SENTENCE_TOKENS, token_ids=SENTENCE_IDS)
        s.split.fit(strip)
        assert len(strip.chips) == len(strip.token_ids) == 7
        assert [c.token for c in strip.chips] == SENTENCE_TOKENS

        self.play(
            LaggedStart(
                *[FadeIn(chip, scale=0.7) for chip in strip.chips], lag_ratio=0.12
            ),
            run_time=1.2,
            rate_func=motion.SNAP,
        )
        self.add(strip)
        self._stage(strip)
        self.wait(0.7)

        # TOKEN ACCOUNTING 3: the lifted chip is the WHOLE word plus its space.
        straw = strip.chip_for(" " + WORD)
        assert straw is not None and straw.token == " " + WORD
        assert strip.token_ids[list(strip.chips).index(straw)] == 101830

        cap_word = self._caption(
            "one token. three r's inside it.",
            np.array([-13.0, -0.75, 0.0]),
            SHOT_BENCH,
            color=theme.TOKEN,
        )
        self.play(
            straw.animate.shift(UP * 0.3),
            FadeIn(cap_word),
            run_time=0.9,
            rate_func=motion.ENTER,
        )
        self.wait(0.8)

        # The leading space, said out loud. `show_space=True` is turned on for
        # exactly this shot — the glyph reads as a broken box when nothing on
        # screen explains it, which is why it is off by default.
        many = strip.chip_for(" many")
        big = TokenChip(" many", show_space=True, color=theme.TOKEN)
        big.scale(3.4 / big.width)
        big.move_to(np.array([-13.0, 5.35, 0.0]))
        big.text_mob[0].set_color(theme.EMBED)
        cap_space = self._caption(
            "the space belongs to the word after it",
            np.array([-13.0, -1.35, 0.0]),
            SHOT_BENCH,
        )
        self.play(
            FadeIn(big, scale=0.8),
            many.animate.set_opacity(0.25),
            FadeIn(cap_space),
            run_time=0.9,
            rate_func=motion.ENTER,
        )
        self._stage(big)
        self.wait(0.8)

        # Drop the space and the same ten letters are three pieces with
        # completely different numbers. The two states are on screen together,
        # which is the whole argument.
        word_strip = TokenStrip(WORD_TOKENS, token_ids=WORD_IDS, color=theme.TOKEN)
        word_strip.scale(3.6 / word_strip.width)
        word_strip.move_to(np.array([float(straw.get_center()[0]), 4.9, 0.0]))
        assert "".join(WORD_TOKENS) == WORD
        assert [c.token for c in word_strip.chips] == WORD_TOKENS
        assert list(word_strip.token_ids) == WORD_IDS

        self.play(
            FadeOut(big),
            many.animate.set_opacity(1.0),
            FadeOut(cap_space),
            LaggedStart(
                *[FadeIn(chip, scale=0.7) for chip in word_strip.chips],
                lag_ratio=0.15,
            ),
            straw.animate.set_opacity(0.35),
            run_time=1.0,
            rate_func=motion.MOVE,
        )
        self.add(word_strip)
        self._stage(word_strip)

        cap_split = self._caption(
            "drop the space and it is three pieces — different numbers entirely",
            np.array([-13.0, -1.35, 0.0]),
            SHOT_BENCH,
            color=theme.TOKEN,
        )
        self.play(FadeIn(cap_split), run_time=1.0, rate_func=motion.ENTER)

        self.play(
            *[
                chip.animate.move_to(straw.get_center()).set_opacity(0.0)
                for chip in word_strip.chips
            ],
            straw.animate.set_opacity(1.0).shift(DOWN * 0.3),
            FadeOut(cap_word),
            FadeOut(cap_split),
            run_time=0.6,
            rate_func=motion.SNAP,
        )
        self.remove(word_strip)
        self.bench.remove(word_strip, big)
        # 0.40 rather than the 0.60 the plan's table carries: that table's rows
        # sum to 9.70 against a beat that is 9.50 long, and a hold is the
        # safest thing to trim. The beat boundary is what is fixed.
        self.wait(0.4)
        return strip

    # ================================================== 21.00 -> 33.50  B3
    def beat_the_table(self) -> None:
        """The wall, then three worked merges and the ordered list."""
        s = self.set
        wall = s.vocab

        self.play(
            camera.focus(
                self, wall.frame, width=SHOT_TIGHT, shift=RIGHT * 2.1, run_time=1.2
            ),
            run_time=1.2,
            rate_func=motion.MOVE,
        )

        # Most of these cells land below `typography.MIN_READABLE` at this shot
        # and are therefore decoration, by design. The one thing on the wall the
        # viewer is meant to read is the counter beside it.
        self._stage(wall.cells, wall.readout)
        self.play(
            LaggedStart(*[FadeIn(cell) for cell in wall.cells], lag_ratio=0.004),
            run_time=1.0,
            rate_func=motion.ENTER,
        )
        self.play(FadeIn(wall.readout), run_time=0.7, rate_func=motion.ENTER)
        self.wait(1.0)

        merges = s.merges
        self.play(
            camera.focus(self, s.table.bay, width=SHOT_TIGHT, run_time=1.1),
            FadeOut(wall.readout),
            run_time=1.1,
            rate_func=motion.MOVE,
        )
        self.bench.remove(wall.readout)

        units = [unit for row in merges.cells for cell in row for unit in cell.parts]
        self._stage(merges)
        self.play(
            LaggedStart(*[FadeIn(unit) for unit in units], lag_ratio=0.03),
            FadeIn(merges.list_title),
            FadeIn(merges.counter),
            FadeIn(merges.note),
            run_time=0.7,
            rate_func=motion.ENTER,
        )
        self.add(merges)

        # Three worked merges. The pairs are found by what the cells currently
        # spell, so merge 2 locates `lo` + `w` without anybody writing an index
        # down — and a different example would still merge correctly.
        for step in range(3):
            anims, entry = merges.merge_anims(step)
            self.play(
                *anims, FadeIn(entry), run_time=0.9, rate_func=motion.SNAP
            )
        # The rows spell what the merges say they spell, derived rather than
        # asserted by eye: `low` is one run, and `newest` has become n·e·w·es·t.
        assert [cell.token for cell in merges.cells[0]] == ["low"]
        assert [cell.token for cell in merges.cells[2]] == ["n", "e", "w", "es", "t"]
        self.wait(0.8)

        # The ramp: the list accelerates out of legibility. Four plays whose
        # SHAPE is the content, not four readable states — the deck collapses
        # them into one click by recognising the ticker they animate.
        ticker = merges.counter
        for i, label in enumerate(RAMP_LABELS):
            nxt = merges.ticker(label)
            self.play(
                FadeOut(ticker),
                FadeIn(nxt),
                merges.entries.animate.shift(UP * (0.35 + 0.3 * i)).set_opacity(
                    max(0.0, 0.75 - 0.25 * i)
                ),
                run_time=0.4,
                rate_func=motion.EXIT,
            )
            self._stage(nxt)
            ticker = nxt
        #: The face left on screen, cleared by B4 with the rest of the table.
        self.merge_ticker = ticker

        self.table_caption = self._caption(
            "counted, not chosen",
            # Off the midline: the meter spur runs down x = 0 and drew straight
            # through the words.
            np.array([3.0, 0.2, 0.0]),
            SHOT_TIGHT,
            color=theme.ATTENTION,
        )
        self.play(FadeIn(self.table_caption), run_time=0.8, rate_func=motion.ENTER)
        self.wait(0.9)

    # ================================================== 33.50 -> 40.00  B4
    def beat_the_ids(self, strip) -> None:
        """Seven integers — not nine — and the model wall they pass through."""
        s = self.set

        # The faces are built from the strip's OWN id list. There is no second
        # list of ids in this scene, which is the point of the accounting rule.
        delta = s.ids.slot_center - strip.get_center()
        faces = VGroup()
        for chip, token_id in zip(strip.chips, strip.token_ids):
            face = typography.text(
                "body", str(token_id), frame_width=SHOT_IDS, color=theme.FG, mono=True
            )
            limit = chip.box.width * 0.84
            if face.width > limit:
                face.scale(limit / face.width)
            face.move_to(chip.box.get_center() + delta)
            faces.add(face)
        assert len(faces) == len(strip.token_ids) == 7

        self.play(
            camera.focus(self, s.ids.bay, width=SHOT_IDS, run_time=1.2),
            *[chip.box.animate.shift(delta) for chip in strip.chips],
            LaggedStart(
                *[
                    FadeOut(chip.text_mob, shift=delta + UP * 0.3)
                    for chip in strip.chips
                ],
                lag_ratio=0.06,
            ),
            LaggedStart(
                *[FadeIn(face, shift=UP * 0.3) for face in faces], lag_ratio=0.06
            ),
            FadeOut(s.merges),
            FadeOut(s.merges.entries),
            FadeOut(self.merge_ticker),
            FadeOut(self.table_caption),
            run_time=1.2,
            rate_func=motion.MOVE,
        )
        for chip in strip.chips:
            chip.remove(chip.text_mob)
        self.bench.remove(s.merges, s.merges.entries, self.merge_ticker)
        self._stage(faces)

        self.play(
            *[
                chip.box.animate.set_stroke(theme.EMBED, width=theme.STROKE_THICK)
                for chip in strip.chips
            ],
            *[face.animate.set_color(theme.EMBED) for face in faces],
            s.glow_for(s.ids).animate.set_stroke(opacity=1.0),
            run_time=0.8,
            rate_func=motion.ENTER,
        )
        self.wait(0.7)

        # Through the slot in the model wall, along the drawn rail.
        convoy = VGroup(*[chip.box for chip in strip.chips], *faces)
        landing = s.door.frame.get_left() + RIGHT * 1.2
        path = routing.join(
            [convoy.get_center(), s.rail_ids_door.start],
            s.rail_ids_door,
            [s.rail_ids_door.end, np.array([landing[0], 2.0, 0.0])],
        )
        self.play(
            MoveAlongPath(convoy, path),
            camera.focus(self, s.door_slot, width=SHOT_IDS, run_time=1.0),
            s.glow_for(s.ids).animate.set_stroke(opacity=s.resting_glow),
            run_time=1.0,
            rate_func=motion.MOVE,
        )

        # Past the wall there is no text anywhere. Only vectors.
        s.door_vectors.move_to(convoy.get_center())
        self._stage(s.door_vectors)
        self.play(
            LaggedStart(
                *[FadeOut(face) for face in faces],
                *[FadeOut(chip.box) for chip in strip.chips],
                lag_ratio=0.03,
            ),
            FadeIn(s.door_vectors),
            run_time=0.7,
            rate_func=motion.MOVE,
        )
        self.bench.remove(strip, faces)

        # The word that started it, struck through, with the integer that
        # actually crossed the wall underneath it.
        index = list(strip.chips).index(strip.chip_for(" " + WORD))
        ghost_chip = TokenChip(
            " " + WORD,
            token_id=strip.token_ids[index],
            show_id=True,
            color=theme.TOKEN,
        )
        ghost_chip.move_to(np.array([float(convoy.get_center()[0]), 3.8, 0.0]))
        strike = Line(
            ghost_chip.box.get_left() + LEFT * 0.1,
            ghost_chip.box.get_right() + RIGHT * 0.1,
            stroke_color=theme.ERROR,
            stroke_width=theme.STROKE_THICK,
        )
        ghost_chip.set_opacity(0.25)
        self.ghost_word = VGroup(ghost_chip, strike)
        self._stage(self.ghost_word)
        self.play(FadeIn(self.ghost_word), run_time=0.8, rate_func=motion.ENTER)

        self.ids_caption = self._caption(
            "no letters went through",
            np.array([22.3, -1.0, 0.0]),
            SHOT_IDS,
            color=theme.EMBED,
        )
        self.play(FadeIn(self.ids_caption), run_time=0.7, rate_func=motion.ENTER)
        self.wait(0.6)

    # ================================================== 40.00 -> 51.00  B5
    def beat_the_meter(self) -> None:
        """Price, context, latency — then en 7 / hi 32 / my 72."""
        s = self.set

        self.play(
            camera.focus(self, s.meter.bay, width=SHOT_METER, run_time=1.3),
            FadeOut(self.ghost_word),
            FadeOut(self.ids_caption),
            run_time=1.3,
            rate_func=motion.MOVE,
        )
        self.bench.remove(self.ghost_word)

        counters = [s.price, s.context, s.latency]
        self._stage(*counters)
        self.play(
            LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in counters], lag_ratio=0.18),
            s.glow_for(s.meter).animate.set_stroke(opacity=1.0),
            run_time=1.1,
            rate_func=motion.ENTER,
        )
        self.wait(0.8)

        # Three bars, one per language, at a fixed number of world units per
        # token. The Burmese bar therefore leaves the shot — that is the beat's
        # argument, not a layout bug.
        for i, run_time in enumerate((0.9, 1.1, 1.4)):
            bar = s.bars[i]
            label = s.bar_labels[i]
            anchor = bar.get_left()
            self._stage(bar, label)
            self.add(bar)
            self.play(
                bar.animate.stretch_to_fit_width(bar.full_width).move_to(
                    anchor, aligned_edge=LEFT
                ),
                FadeIn(label),
                run_time=run_time,
                rate_func=motion.ENTER,
            )

        self.meter_caption = self._caption(
            "median tokens · 2,033 parallel texts · MASSIVE · cl100k_base",
            np.array([0.0, -16.3, 0.0]),
            SHOT_METER,
        )
        self.play(FadeIn(self.meter_caption), run_time=0.9, rate_func=motion.ENTER)
        self.wait(0.9)

        # The counters re-read with the Burmese figure. Same sentence, same
        # meaning, ten times the bill.
        rereads = VGroup(
            self._counter_line("price     72 tokens, not 7 — same sentence", 0),
            self._counter_line("context   ten times less of it fits", 1),
            self._counter_line("latency   prefill is ten times the work", 2),
        )
        self._stage(rereads)
        self.play(
            LaggedStart(*[FadeIn(line) for line in rereads], lag_ratio=0.12),
            *[FadeOut(c) for c in counters],
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.bench.remove(*counters)

        stamp = typography.text(
            "title", "10×", frame_width=SHOT_METER, color=theme.WARN, bold=True
        )
        stamp.move_to(np.array([6.0, -11.6, 0.0]))
        self._stage(stamp)
        #: What the pull-back dims so the bay's wide-shot name can be read.
        self.meter_readout = VGroup(rereads, stamp)
        self.play(
            FadeIn(stamp, scale=1.6),
            FadeOut(self.meter_caption),
            run_time=0.7,
            rate_func=motion.FEATURE,
        )
        self.wait(1.0)

    # ================================================== 51.00 -> 59.50  B6
    def beat_where_it_sits(self) -> None:
        """Pull back, then the bench shrinks into one bay of the Arc 0 plant."""
        s = self.set

        # The meter's read-out dims with the bay labels. A `Station` fades its
        # own `content` at the pull-back; these counters were placed in world
        # space rather than loaded into the bay, so they are dimmed by hand or
        # the METER marquee lands on top of them.
        self.play(
            camera.frame_all(self, [s.everything], pad=WIDE_PAD, run_time=1.6),
            *s.reveal_labels(),
            self.meter_readout.animate.set_opacity(0.2),
            run_time=1.6,
            rate_func=motion.FEATURE,
        )
        # Complete stillness. The film is a diagram for one moment.
        self.wait(0.5)

        # The SET scales, not the camera. Two pull-backs in 8.5s reads as a
        # stumble, and the set-shrink is the gesture that says "this whole
        # machine is one part of that machine".
        #
        # `Transform` against a copy rather than `self.bench.animate.scale(...)`:
        # a VGroup carries its own transparent rgba and animating one drags
        # every child's opacity down. A copy has the SAME rgba at every node, so
        # the interpolation is a no-op on colour and a pure move on geometry.
        target = self.bench.copy()
        target.scale(s.bench_shrink(), about_point=self.bench.get_center())
        target.move_to(s.bench_target_center())
        self.play(
            Transform(self.bench, target),
            FadeIn(s.ghost.wires),
            FadeIn(s.ghost.nodes),
            run_time=2.2,
            rate_func=motion.MOVE,
        )

        self.play(
            s.ghost.labelled_node.animate.set_stroke(
                theme.TOKEN, width=theme.STROKE_THICK, opacity=1.0
            ),
            FadeIn(s.ghost.label),
            run_time=0.8,
            rate_func=motion.ENTER,
        )

        closing = self._caption(
            "everything above happens\nbefore the model reads a word",
            np.array([-18.5, 2.0, 0.0]),
            SHOT_WIDE,
            color=theme.FG,
        )
        self.play(FadeIn(closing), run_time=1.0, rate_func=motion.ENTER)

        # A step down from the caption above it, and kept clear of the ghost
        # circuit's left column at x = 0 — at `label` it ran under the nodes.
        card = VGroup(
            typography.text(
                "caption",
                "Arc 1 · Inside the model, just enough",
                frame_width=SHOT_WIDE,
                color=theme.FG_MUTED,
            ),
            typography.text(
                "caption",
                "next — Attention and the KV cache",
                frame_width=SHOT_WIDE,
                color=theme.TOKEN,
            ),
        ).arrange(DOWN, buff=theme.PAD_MD, aligned_edge=LEFT)
        card.move_to(np.array([-17.0, -5.0, 0.0]))
        self.play(FadeIn(card, shift=UP * 0.4), run_time=0.9, rate_func=motion.ENTER)
        # A trailing wait, so the last stop of the deck rests past the final
        # fade rather than on it.
        self.wait(1.5)

    # ------------------------------------------------------------- helpers
    def _stage(self, *mobjects) -> None:
        """Adopt props into the bench, so B6's shrink takes them with it."""
        self.bench.add(*mobjects)

    def _caption(self, text: str, position, shot_width: float, *, color=None):
        """A caption sized for the shot it is read in. Never a raw font size."""
        caption = typography.text(
            "label",
            text,
            frame_width=shot_width,
            color=color if color is not None else theme.FG_MUTED,
        )
        caption.move_to(position)
        self._stage(caption)
        return caption

    def _counter_line(self, text: str, index: int):
        """One of B5's counter rows, re-read with the Burmese figure."""
        line = typography.text(
            "label", text, frame_width=SHOT_METER, color=theme.WARN, mono=True
        )
        line.move_to(
            np.array([COUNTER_X, COUNTER_YS[index], 0.0]), aligned_edge=LEFT
        )
        return line

    @staticmethod
    def _fit_in_window(bubble, chat) -> None:
        """Shrink a bubble until the chat window can actually show it.

        The window has no clipping mask: a bubble taller than the message area
        is drawn straight through the composer, or scrolled out of sight. The
        bubble yields, not the window.
        """
        room = chat.message_area_height
        if bubble.height > room:
            bubble.scale(room / bubble.height)
