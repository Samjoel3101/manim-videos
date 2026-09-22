"""The whole video: one continuous 59.5-second shot along the tokenizer bench.

No cuts. The set (`tokenizer_set.py`) is built once and the camera walks it left
to right — chat, split, table, ids, model wall — then drops down the spur to the
meter and pulls all the way out, so the last shot explains itself.

Pacing is deliberate and tight. Every `run_time` below comes from the
per-animation budget in `../script.md`, the beat boundaries are fixed, and
changing one `run_time` means re-balancing its neighbours **inside the same
beat**. Each beat method carries its target timecode in a comment. Nominal total
is 59.50s against a HARD 60.0s cap.

The through-line is one payload, never destroyed, only transformed:

    a typed question → a row of characters → THE CHARACTERS GOING DARK →
    chips with no letters in them → an ordered merge list → a row of integers →
    a number on a meter → a bar beside Hindi and Burmese → one small bay in a
    plant the viewer has already walked through

**The single most important frame in the film is beat 1's wipe**, where the
characters go dark. Everything before it has letters; nothing after it does. It
gets the full 1.2s and nothing else moves during it.

Two things in here are assertions rather than choreography, and both exist
because the scripted version of this film made a false claim that every
automated gate passed:

* the `r` counter counts the WORD (3), not the sentence (4). The `r` in `r's` is
  the fourth and it does not pulse;
* the chips and the ids are ONE `TokenStrip`, built once in the set with
  explicit ids. Beat 4 flips that object. There is no second list anywhere.
"""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    FadeIn,
    FadeOut,
    Flash,
    LaggedStart,
    MoveAlongPath,
    MovingCameraScene,
    VGroup,
)

from lib import camera, motion, theme, typography
from lib.components.chat_ui import StreamingBubble
from lib.components.stacked import SegmentedBar
from lib.components.tokens import TokenChip, TokenStrip

try:  # pragma: no cover - whichever branch runs, the other is unreachable
    from .tokenizer_set import (
        BIG_CHIP_SHARE,
        CHAT_SHOT_CENTRE,
        IDS,
        QUESTION,
        SHOT_BENCH,
        SHOT_CHAT,
        SHOT_IDS,
        SHOT_METER,
        SHOT_TIGHT,
        SHOT_WIDE,
        SPLIT_PIECES,
        TOKENS,
        WORD,
        TokenizerSet,
    )
except ImportError:  # pragma: no cover
    from tokenizer_set import (
        BIG_CHIP_SHARE,
        CHAT_SHOT_CENTRE,
        IDS,
        QUESTION,
        SHOT_BENCH,
        SHOT_CHAT,
        SHOT_IDS,
        SHOT_METER,
        SHOT_TIGHT,
        SHOT_WIDE,
        SPLIT_PIECES,
        TOKENS,
        WORD,
        TokenizerSet,
    )

# ---------------------------------------------------------------------------
# Token accounting — the rule that cannot be broken.
#
# Arc 0 shipped a cut that revealed more words than it had emitted tokens, with
# every gate green. The gates compare a 16x16 luminance grid; they cannot see a
# correct-looking animation making a false claim. The scripted version of THIS
# film contained exactly that class of error twice and a pre-flight caught both.
# Each assertion below is one of them.
# ---------------------------------------------------------------------------

#: 3. The chips reconstruct the question EXACTLY. This is what fails loudly if
#:    anyone "tidies" the leading spaces — which would silently destroy the
#:    film's central claim, that the space belongs to the word.
assert "".join(TOKENS) == QUESTION, (
    "the chips no longer reconstruct the question. Leading spaces are not "
    "decoration here: ` strawberry` is one token BECAUSE of its space."
)
#: 2. The chips and the ids are one list, seven long.
assert len(TOKENS) == len(IDS) == 7
#: 4. The standalone split reconstructs the word, is three pieces, and none of
#:    them IS an `r`. ("raw" contains one; no piece is the letter on its own,
#:    which is the claim the film makes.)
assert "".join(SPLIT_PIECES) == WORD
assert len(SPLIT_PIECES) == 3
assert "r" not in SPLIT_PIECES
#: 1. The counter counts the WORD, not the sentence, and the two differ. The
#:    second of these is the trap: the sentence has four `r`s because `r's`
#:    contributes one, and the film's `3` is about `strawberry` alone.
assert WORD.count("r") == 3
assert QUESTION.lower().count("r") == 4
#: 5. The character row is derived from the question, never written down.
assert len(QUESTION) == 27

#: The cold open's wrong answer. Two, not three — the mistake the film explains.
WRONG_ANSWER = 'There are 2 r\'s in "strawberry".'

#: World units of bar per token in beat 5. Chosen so Burmese's 72 runs past the
#: right edge of the SHOT_METER frame and English's 7 is still a visible bar —
#: the overrun is the point of the beat, not an accident of scaling.
BAR_UNIT = 0.22

#: Beat 5's three medians, from the MASSIVE parallel corpus (2,033 texts) under
#: `cl100k_base`. They are MEDIANS OVER A CORPUS, not token counts for the
#: sentence on screen, and the caption at 47.0s says so. Drawing them without
#: that caption makes the film assert something false.
LANGUAGE_BARS = (("en", 7), ("hi", 32), ("my", 72))


class Tokenization(MovingCameraScene):
    def construct(self) -> None:
        theme.apply(self)

        self.set = TokenizerSet()
        self.add(self.set)
        # Not `camera.snap_to`: beat 0's caption goes UNDER the chat window and
        # the window nearly fills the frame at SHOT_CHAT. See CHAT_SHOT_CENTRE.
        self.camera.frame.move_to(
            np.array([*CHAT_SHOT_CENTRE, 0.0])
        ).set(width=SHOT_CHAT)

        self.beat_cold_open()   # 0.00 → 5.00
        self.beat_line()        # 5.00 → 11.50
        self.beat_split()       # 11.50 → 22.50
        self.beat_table()       # 22.50 → 34.00
        self.beat_ids()         # 34.00 → 40.50
        self.beat_meter()       # 40.50 → 51.00
        self.beat_pull_back()   # 51.00 → 59.50

    # ================================================= 0.00 → 5.00  cold open
    def beat_cold_open(self) -> None:
        """The question is already asked. The answer arrives, and it is wrong."""
        s = self.set
        chat = s.chat

        reply = StreamingBubble(
            WRONG_ANSWER,
            sender="assistant",
            max_width=chat.message_max_width,
        )
        chat.place(reply, "assistant")
        # `StreamingBubble` builds its text at opacity 0 and expects `reveal()`.
        # `FadeIn` animates UP TO a mobject's current opacity, so fading in a
        # word that is already at zero fades it in to zero — which is exactly
        # what shipped an empty bubble through the first draft. Reveal first,
        # then let FadeIn do the streaming.
        reply.reveal(reply.word_count)
        # The bubble is placed but NOT committed: committing attaches it to the
        # chat's transcript, which is already in the scene via the set, so it
        # would be on screen from frame 0. Nothing follows it, so nothing needs
        # to stack under it.
        self.reply = reply

        # 0.00 (1.30) — the reply streams in beside the question.
        self.play(
            FadeIn(reply.body),
            LaggedStart(
                *[FadeIn(word) for word in reply.words], lag_ratio=0.28
            ),
            run_time=1.30,
            rate_func=motion.ENTER,
        )

        # 1.30 (0.80) — the `2`. A Flash plus a colour change rather than
        # `effects.pulse`: pulse bakes its own run_time, and a second animation
        # on the same glyph in the same play is a conflict, not an emphasis.
        two = reply.words[2][0]
        self.play(
            Flash(two, color=theme.WARN, flash_radius=0.42, line_length=0.14),
            two.animate.set_color(theme.WARN),
            run_time=0.80,
            rate_func=motion.FEATURE,
        )

        # 2.10 (1.00) — complete stillness. Long enough to feel wrong.
        self.wait(1.00)

        # 3.10 (0.80)
        self.cold_caption = self._caption(
            "it is not bad at counting.",
            SHOT_CHAT,
            (CHAT_SHOT_CENTRE[0], -1.75),
        )
        self.play(
            FadeIn(self.cold_caption, shift=UP * theme.PAD_XS),
            run_time=0.80,
            rate_func=motion.ENTER,
        )

        # 3.90 (1.10)
        self.wait(1.10)

    # =================================================== 5.00 → 11.50  the line
    def beat_line(self) -> None:
        """Characters on the bench, the three r's once, and then the wipe."""
        s = self.set

        # 5.00 (1.30) — the camera pans right WITH the question flying out of
        # the bubble onto the bench. The flight is a MoveAlongPath over the
        # drawn rail, never a straight line between two centres.
        ghost = s.question_bubble.text_mob.copy()
        flight = s.question_to_split_path()
        flight.shift(ghost.get_center() - flight.get_start())
        self.add(ghost)
        self.play(
            MoveAlongPath(ghost, flight),
            camera.focus(
                self, s.split.bay, width=SHOT_BENCH, shift=UP * 1.6, run_time=1.30
            ),
            FadeOut(self.cold_caption),
            FadeOut(self.reply.body),
            *[FadeOut(w) for w in self.reply.words],
            run_time=1.30,
            rate_func=motion.MOVE,
        )
        self.remove(ghost)

        # 6.30 (0.80) — 27 character cells settle.
        self.play(
            motion.enter(s.row.cells, lag=motion.LAG * 0.25),
            run_time=0.80,
            rate_func=motion.ENTER,
        )
        # Assertion 5, checked against the thing actually on screen rather than
        # against the constant it was built from.
        assert len(s.row.cells) == len(QUESTION) == 27

        # 7.10 (1.00) — the three `r`s INSIDE `strawberry` light, and the
        # counter says 3. The `r` in `r's` is the sentence's fourth and it stays
        # dark: four in the sentence, three in the word, and the film's claim is
        # about the word.
        assert s.row.r_count == WORD.count("r") == 3
        self.play(
            LaggedStart(
                *[
                    AnimationGroup(*cell.light(theme.WARN))
                    for cell in s.row.r_cells
                ],
                lag_ratio=0.3,
            ),
            FadeIn(s.row_counter, shift=UP * theme.PAD_XS),
            run_time=1.00,
            rate_func=motion.ENTER,
        )

        # 8.10 (0.70)
        self.wait(0.70)

        # 8.80 (1.20) — THE WIPE. All 27 cells to FG_FAINT, left to right, and
        # the counter goes dark with them. Nothing else moves; do not decorate
        # this. Everything before this frame has letters in it and nothing after
        # it does, and if this does not land the film does not work.
        self.play(
            LaggedStart(*s.row.wipe_dark(), lag_ratio=0.035),
            s.row_counter.animate.set_color(theme.FG_FAINT),
            run_time=1.20,
            rate_func=motion.SHARP,
        )

        # 10.00 (0.80)
        self.line_caption = self._caption(
            "this is the last frame with letters in it.",
            SHOT_BENCH,
            (-13.0, 4.45),
        )
        self.play(
            FadeIn(self.line_caption, shift=UP * theme.PAD_XS),
            run_time=0.80,
            rate_func=motion.ENTER,
        )

        # 10.80 (0.70)
        self.wait(0.70)

    # ================================================= 11.50 → 22.50  the split
    def beat_split(self) -> None:
        """Seven chips, one of them a whole word — and what the space decides.

        The heart of the film. It carries two claims: ` strawberry` is ONE token
        in this sentence, and the leading space is what decides that. Without
        the space the same ten characters are three tokens.
        """
        s = self.set

        # 11.50 (1.20) — the dark cells collapse toward the SPLIT bay.
        self.play(
            LaggedStart(
                *[
                    FadeOut(cell, target_position=s.split.slot_center, scale=0.3)
                    for cell in s.row.cells
                ],
                lag_ratio=0.02,
            ),
            FadeOut(s.row_counter),
            FadeOut(self.line_caption),
            run_time=1.20,
            rate_func=motion.EXIT,
        )

        # 12.70 (1.20) — SEVEN chips. Not nine: ` strawberry` is one of them.
        assert len(s.strip.chips) == len(IDS) == 7
        self.play(
            LaggedStart(
                *[FadeIn(chip, scale=0.8) for chip in s.strip.chips],
                lag_ratio=0.12,
            ),
            s.glow_for(s.split).animate.set_stroke(opacity=1.0),
            run_time=1.20,
            rate_func=motion.SNAP,
        )

        # 13.90 (0.70)
        self.wait(0.70)

        # 14.60 (1.00) — the widest chip by far lifts and glows.
        self.split_caption = self._caption(
            "one word · one token", SHOT_BENCH, (-13.0, -0.15), color=theme.TOKEN
        )
        self.play(
            s.word_chip.animate.shift(UP * 0.3),
            s.strawberry_glow.animate.set_stroke(opacity=1.0),
            FadeIn(self.split_caption, shift=UP * theme.PAD_XS),
            run_time=1.00,
            rate_func=motion.FEATURE,
        )

        # 15.60 (1.20) — let it land. This is the film's central surprise.
        self.wait(1.20)

        # 16.80 (0.90) — the chip fills a third of the frame, and this is the
        # one shot in the film that says out loud what the space marker means —
        # which is the condition `lib/components/tokens.SPACE_GLYPH` sets for
        # drawing it at all.
        big = TokenChip(
            " " + WORD,
            color=theme.TOKEN,
            show_space=True,
            font_size=typography.size_for("title", SHOT_BENCH),
        )
        big.text_mob[0].set_color(theme.EMBED)
        big.scale(min(1.0, (SHOT_BENCH * BIG_CHIP_SHARE) / big.width))
        big.move_to(np.array([-13.0, 5.2, 0.0]))
        self.big_chip = big
        self.play(
            FadeIn(big, scale=0.75),
            s.word_chip.animate.set_opacity(0.0),
            s.strawberry_glow.animate.set_stroke(opacity=0.0),
            run_time=0.90,
            rate_func=motion.ENTER,
        )

        # 17.70 (0.80)
        space_caption = self._caption(
            "the space belongs to the word",
            SHOT_BENCH,
            (-13.0, 4.15),
            color=theme.EMBED,
        )
        # The outgoing line RISES away as the incoming one rises in, so the two
        # are never on the same baseline at half opacity — which is what a
        # straight cross-fade at one position looks like, and it reads as a
        # collision rather than a swap.
        self.play(
            FadeOut(self.split_caption, shift=UP * 0.45),
            FadeIn(space_caption, shift=UP * 0.45),
            run_time=0.80,
            rate_func=motion.MOVE,
        )

        # 18.50 (1.10) — the space is stripped and the chip shatters into three.
        pieces = TokenStrip(
            SPLIT_PIECES,
            color=theme.TOKEN,
            font_size=typography.size_for("heading", SHOT_BENCH),
        )
        pieces.move_to(big.get_center())
        self.pieces = pieces
        # A COPY of the space glyph flies off, so the glyph itself can leave
        # with the chip it belongs to and nothing is animated twice.
        flying_space = big.text_mob[0].copy()
        self.add(flying_space)
        self.play(
            flying_space.animate.shift(UP * 1.3 + LEFT * 0.8).set_opacity(0.0),
            FadeOut(big),
            FadeIn(pieces, scale=1.12),
            run_time=1.10,
            rate_func=motion.MOVE,
        )
        self.remove(flying_space)

        # 19.60 (1.00)
        three_caption = self._caption(
            "without it, three", SHOT_BENCH, (-13.0, 4.15), color=theme.TOKEN
        )
        self.play(
            FadeOut(space_caption, shift=UP * 0.45),
            FadeIn(three_caption, shift=UP * 0.45),
            run_time=1.00,
            rate_func=motion.MOVE,
        )

        # 20.60 (0.90)
        self.wait(0.90)

        # 21.50 (0.70) — the three go back to being one, and the beat clears its
        # own props before the camera leaves.
        # docs/slides.md rule 4: the chip is ARRIVING, so it enters with FadeIn.
        # FadeIn animates up to a mobject's CURRENT opacity, so the final state
        # is set first and the fade runs 0 -> that. The drop back into the row
        # happens while it is invisible, which is why it is not animated.
        s.word_chip.set_opacity(1.0).shift(DOWN * 0.3)
        self.play(
            FadeOut(pieces, target_position=s.word_chip.get_center(), scale=0.4),
            FadeOut(three_caption),
            FadeIn(s.word_chip),
            s.glow_for(s.split).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.70,
            rate_func=motion.EXIT,
        )

        # 22.20 (0.30)
        self.wait(0.30)

    # ================================================= 22.50 → 34.00  the table
    def beat_table(self) -> None:
        """Where the pieces come from: a wall of them, and the list that built it."""
        s = self.set

        # 22.50 (1.20) — tilt up to the wall, and the chips carry on down the
        # bench to the ids bay while the camera leaves them. Shifted per CHIP,
        # not as a group: a shared delta over a list is the idiom this repo
        # settled on after animating a container VGroup's geometry cost it a
        # session.
        to_ids = -s.strip_travel
        self.play(
            camera.focus(
                self, s.vocab.cells, width=SHOT_TIGHT, shift=UP * 0.65,
                run_time=1.20,
            ),
            *[chip.animate.shift(to_ids) for chip in s.strip.chips],
            run_time=1.20,
            rate_func=motion.MOVE,
        )

        # 23.70 (1.00) — the wall builds. Most cells are below
        # typography.MIN_READABLE at this shot and are therefore decoration, by
        # design: the wall is a quantity, not a list.
        self.play(
            LaggedStart(
                *[FadeIn(cell) for cell in s.vocab.cells], lag_ratio=0.004
            ),
            FadeIn(s.vocab.samples),
            run_time=1.00,
            rate_func=motion.ENTER,
        )

        # 24.70 (0.70)
        wall_caption = self._caption(
            "every piece the model can ever see", SHOT_TIGHT, (0.0, 12.15)
        )
        self.play(
            FadeIn(s.vocab.counter, shift=UP * theme.PAD_XS),
            FadeIn(wall_caption, shift=UP * theme.PAD_XS),
            run_time=0.70,
            rate_func=motion.ENTER,
        )

        # 25.40 (0.70)
        self.wait(0.70)

        # The wall is set furniture from here on, so it is re-parented into the
        # set: beat 6 shrinks `self.set` into the ghost node, and anything still
        # sitting at the top level of the scene would stay behind at full size.
        # Splatted: the cells were faded in one at a time, so each is its own
        # top-level entry in `scene.mobjects` and removing their VGroup — which
        # was never added — would remove nothing at all.
        self.remove(*s.vocab.cells, s.vocab.samples, s.vocab.counter)
        s.vocab.add(s.vocab.cells, s.vocab.samples, s.vocab.counter)

        # 26.10 (1.10) — back down to the table.
        self.play(
            camera.focus(self, s.table.bay, width=SHOT_TIGHT, run_time=1.10),
            FadeOut(wall_caption),
            run_time=1.10,
            rate_func=motion.MOVE,
        )

        # 27.20 (0.70) — three words as loose letters, and an empty list.
        self.play(
            FadeIn(s.merges.rows, shift=UP * theme.PAD_XS),
            FadeIn(s.merges.list_title),
            run_time=0.70,
            rate_func=motion.ENTER,
        )

        # 27.90 / 28.80 / 29.70 (0.90 each) — three worked merges. The example
        # is OURS, in the shape of the BPE paper's worked example; the film does
        # not caption it as the paper's and does not claim these are
        # o200k_base's first three merges, because they are not.
        for i in range(3):
            self.play(
                *s.merges.merge_step(i),
                FadeIn(s.merges.list_entry(i), shift=UP * theme.PAD_XS),
                run_time=0.90,
                rate_func=motion.SNAP,
            )

        # 30.60 (0.50)
        self.wait(0.50)

        # 31.10 (1.60) — the list runs away. A RAMP, not a sequence of states:
        # its shape is the content, so the deck collapses it to one click.
        self.merge_ramp()

        # 32.70 (0.80)
        table_caption = self._caption(
            "counted, not chosen", SHOT_TIGHT, (0.0, 0.05), color=theme.ATTENTION
        )
        self.play(
            FadeIn(table_caption, shift=UP * theme.PAD_XS),
            run_time=0.80,
            rate_func=motion.ENTER,
        )
        self.table_caption = table_caption

        # 33.50 (0.50)
        self.wait(0.50)

    def merge_ramp(self) -> None:
        """One play: the ordered list accelerates out of legibility.

        A separate method purely so the deck can wrap it in `no_stops()` without
        re-implementing the beat around it — the same trick
        `chatgpt_request_lifecycle`'s deck uses for its decode ramp.
        """
        s = self.set
        settled = list(s.merges.list_entries)
        tail = [
            s.merges.tail_entry(text)
            for text in ("4.  …", "5.  …", "6.  …", "…", "50,000.  …")
        ]
        # Built below the settled three, then raised so their FINAL positions
        # are the ones the settled three are vacating. Without this the tail
        # lands where it was built, which is below the bay.
        for entry in tail:
            entry.shift(UP * 1.0)
        # Per entry, never through a wrapper VGroup. Every one of these was
        # faded in individually, so each is its own top-level mobject; animating
        # a fresh VGroup around them would add that group alongside its own
        # children and draw the list twice.
        self.play(
            *[
                entry.animate.shift(UP * 1.0).set_opacity(0.25)
                for entry in settled
            ],
            s.merges.list_title.animate.shift(UP * 1.0).set_opacity(0.0),
            *[FadeIn(entry, shift=UP * 1.0) for entry in tail],
            run_time=1.60,
            rate_func=motion.ACCELERATE,
        )
        self.merge_list = [s.merges.list_title, *settled, *tail]

    # =================================================== 34.00 → 40.50  the ids
    def beat_ids(self) -> None:
        """The chips become integers, and one of them is the answer."""
        s = self.set

        # The chips were added one at a time in beat 2 and have been top-level
        # scene mobjects since. Re-parent them into the strip so the crossing at
        # 37.6s can move the whole row with one MoveAlongPath — and so the
        # integer faces travel with the chips they belong to.
        self.remove(*s.strip.chips)
        self.add(s.strip)

        # 34.00 (1.20) — the camera goes to the ids bay WITH the flip. Each
        # chip's word face goes out as its integer face comes in; this is the
        # same TokenStrip built in the set with explicit ids, not a second list.
        flips = []
        for chip, face in zip(s.strip.chips, s.id_faces):
            flips.append(
                AnimationGroup(
                    chip.text_mob.animate.set_opacity(0.0),
                    FadeIn(face),
                )
            )
        self.play(
            camera.focus(self, s.ids.bay, width=SHOT_IDS, run_time=1.20),
            LaggedStart(*flips, lag_ratio=0.1),
            FadeOut(s.merges.rows),
            *[FadeOut(entry) for entry in self.merge_list],
            FadeOut(self.table_caption),
            run_time=1.20,
            rate_func=motion.MOVE,
        )
        for chip, face in zip(s.strip.chips, s.id_faces):
            self.remove(face)
            chip.add(face)

        # 35.20 (0.70) — the seven integers settle in EMBED.
        self.play(
            *[face.animate.set_color(theme.EMBED) for face in s.id_faces],
            *[
                chip.box.animate.set_stroke(color=theme.EMBED)
                for chip in s.strip.chips
            ],
            s.glow_for(s.ids).animate.set_stroke(opacity=1.0),
            run_time=0.70,
            rate_func=motion.ENTER,
        )

        # 35.90 (0.90) — 101830 enlarges and glows. The film's punchline, and it
        # has to be legible: at 1.8x a `body` face at SHOT_IDS is comfortably
        # above the `heading` role, which is the floor the brief sets for it.
        word_face = s.id_faces[TOKENS.index(" " + WORD)]
        assert IDS[TOKENS.index(" " + WORD)] == 101830
        ids_caption = self._caption(
            "one word · one number", SHOT_IDS, (13.0, -0.55), color=theme.EMBED
        )
        self.play(
            # Scaled in place, not lifted out: at 1.8x a `body` face is 7.6% of
            # frame height, comfortably past the `heading` role the brief sets
            # as the floor for this number, and it still fits inside its own
            # chip — which lifting it out did not, leaving a blank chip in the
            # middle of the row the beat is about.
            word_face.animate.scale(1.8),
            s.id_glow.animate.set_stroke(opacity=1.0),
            FadeIn(ids_caption, shift=UP * theme.PAD_XS),
            run_time=0.90,
            rate_func=motion.FEATURE,
        )

        # 36.80 (0.80) — hold. This is the answer to the cold open.
        self.wait(0.80)

        # 37.60 (0.90) — the row crosses the model wall.
        crossing = s.ids_to_door_path()
        # Aligned to where the row actually is: the enlarged 101830 has moved
        # the strip's bounding-box centre, and MoveAlongPath drives that centre,
        # so an unshifted path would teleport the row half a unit on frame one.
        crossing.shift(s.strip.get_center() - crossing.get_start())
        self.play(
            MoveAlongPath(s.strip, crossing),
            camera.focus(self, s.door.frame, width=SHOT_IDS, run_time=0.90),
            FadeOut(ids_caption),
            s.id_glow.animate.set_stroke(opacity=0.0),
            s.glow_for(s.ids).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.90,
            rate_func=motion.MOVE,
        )

        # 38.50 (0.70) — the far side of the wall: vectors, and no text anywhere.
        self.play(
            FadeOut(s.strip),
            FadeIn(s.vectors),
            run_time=0.70,
            rate_func=motion.ENTER,
        )
        self.remove(s.vectors)
        s.door.add(s.vectors)

        # 39.20 (0.80)
        self.door_caption = self._caption(
            'nothing in 101830 is an "r"',
            SHOT_IDS,
            (24.0, -1.25),
            color=theme.ASSISTANT,
        )
        self.play(
            FadeIn(self.door_caption, shift=UP * theme.PAD_XS),
            run_time=0.80,
            rate_func=motion.ENTER,
        )

        # 40.00 (0.50)
        self.wait(0.50)

    # ================================================= 40.50 → 51.00  the meter
    def beat_meter(self) -> None:
        """What the split costs: price, context, latency — and whose language."""
        s = self.set

        # 40.50 (1.30) — swing down the consequence spur.
        self.play(
            camera.focus(self, s.meter.bay, width=SHOT_METER, run_time=1.30),
            FadeOut(self.door_caption),
            s.glow_for(s.meter).animate.set_stroke(opacity=1.0),
            run_time=1.30,
            rate_func=motion.MOVE,
        )

        # 41.80 (1.10) — three counters. No real prices anywhere: `$ / 1M tokens`
        # is a UNIT, deliberately without a figure, because real prices date a
        # film within weeks.
        self.counters = [
            self._counter_row("price", -11.45, text="$ / 1M tokens · in and out"),
            self._counter_row("context", -11.95, bar=True),
            self._counter_row(
                "latency", -12.45, text="prefill ∝ in · decode ∝ out"
            ),
        ]
        self.play(
            LaggedStart(
                *[FadeIn(row, shift=RIGHT * theme.PAD_SM) for row in self.counters],
                lag_ratio=0.25,
            ),
            run_time=1.10,
            rate_func=motion.ENTER,
        )

        # 42.90 (0.70)
        self.wait(0.70)

        # 43.60 / 44.50 / 45.60 — three bars. Burmese runs off the right-hand
        # edge of the frame and is LET to: that overrun is the beat.
        self.bars: list = []
        for i, ((code, count), run_time) in enumerate(
            zip(LANGUAGE_BARS, (0.90, 1.10, 1.40))
        ):
            label, value, bar, full_width, left_x = self._language_bar(
                code, count, -12.98 - i * 0.55
            )
            self.bars.extend([label, value, bar])
            self.play(
                FadeIn(label),
                FadeIn(value),
                bar.animate.stretch_to_fit_width(full_width).move_to(
                    np.array([left_x + full_width / 2.0, bar.get_center()[1], 0.0])
                ),
                run_time=run_time,
                rate_func=motion.ENTER,
            )

        # 47.00 (0.90) — NOT optional and NOT decoration. These are medians over
        # a parallel corpus, not token counts for the sentence on screen, and
        # drawing them without saying so makes the film assert something false.
        self.bars_caption = self._caption(
            "median tokens · 2,033 parallel texts · MASSIVE · cl100k_base",
            SHOT_METER,
            (0.0, -14.95),
        )
        self.play(
            FadeIn(self.bars_caption, shift=UP * theme.PAD_XS),
            run_time=0.90,
            rate_func=motion.ENTER,
        )

        # 47.90 (0.80)
        self.wait(0.80)

        # 48.70 (0.80) — the three counters re-read with the Burmese figure.
        # 72 / 7 is 10.3, so "× 10" is the honest rounding and it is the only
        # multiplier claimed anywhere in the beat.
        reread = [
            self._counter_row("price", -11.45, text="× 10 for the same text",
                              color=theme.WARN),
            self._counter_row("context", -11.95, text="× 10 of the window",
                              color=theme.WARN),
            self._counter_row("latency", -12.45, text="× 10 to prefill",
                              color=theme.WARN),
        ]
        self.play(
            *[FadeOut(row) for row in self.counters],
            LaggedStart(
                *[FadeIn(row, shift=RIGHT * theme.PAD_SM) for row in reread],
                lag_ratio=0.2,
            ),
            run_time=0.80,
            rate_func=motion.MOVE,
        )
        self.counters = reread

        # 49.50 (0.60)
        self.stamp = typography.text(
            "title", "10×", frame_width=SHOT_METER, color=theme.WARN, bold=True
        )
        self.stamp.rotate(-8 * np.pi / 180.0)
        self.stamp.move_to(np.array([5.6, -13.58, 0.0]))
        self.play(
            FadeIn(self.stamp, scale=1.6),
            run_time=0.60,
            rate_func=motion.FEATURE,
        )

        # 50.10 (0.90)
        self.wait(0.90)

    # ============================================== 51.00 → 59.50  the pull-back
    def beat_pull_back(self) -> None:
        """All the way out, and then the bench turns out to be one bay."""
        s = self.set

        # 51.00 (1.60) — the whole bench, named. The meter beat's props clear in
        # the same play, so one click in the deck reads "the meter clears, the
        # camera pulls back, the bays name themselves".
        self.play(
            camera.frame_all(self, [s.everything], pad=1.0, run_time=1.60),
            *s.reveal_labels(),
            *[FadeOut(row) for row in self.counters],
            *[FadeOut(part) for part in self.bars],
            FadeOut(self.bars_caption),
            FadeOut(self.stamp),
            *[
                s.glow_for(st).animate.set_stroke(opacity=s.resting_glow)
                for st in s.stations
            ],
            run_time=1.60,
            rate_func=motion.FEATURE,
        )

        # 52.60 (0.50) — complete stillness. The film is a diagram for one
        # moment, and this is it.
        self.wait(0.50)

        # 53.10 (2.20) — the BENCH shrinks into the ghost node. The camera does
        # not move: two pull-backs in eight seconds reads as a stumble, and the
        # set-shrink is the gesture that actually says *this whole machine is
        # one part of that machine*.
        self.play(
            s.animate.scale(s.bench_shrink).move_to(s.ghost.host.get_center()),
            FadeIn(s.ghost.rail),
            # Node by node, so the one that lights at 55.3s is its own top-level
            # mobject rather than a child of a group that is already in the
            # scene — which would have it drawn twice from that beat on.
            LaggedStart(
                *[FadeIn(node) for node in s.ghost.nodes], lag_ratio=0.06
            ),
            run_time=2.20,
            rate_func=motion.MOVE,
        )

        # 55.30 (0.80) — and the one node that has a name is this one.
        self.play(
            s.ghost.host.animate.set_stroke(color=theme.TOKEN, opacity=1.0),
            FadeIn(s.ghost.label, shift=UP * theme.PAD_SM),
            run_time=0.80,
            rate_func=motion.ENTER,
        )

        # 56.10 (1.00)
        # Two EXPLICIT lines. Pango lays a `Text` out against the render's own
        # pixel width, so one 45-unit line wraps at 480p and does not at 1080p —
        # a caption whose shape depends on the render profile is a caption that
        # was reviewed in a draft and shipped in something else. Breaking it
        # here makes both profiles identical.
        #
        # Placed INSIDE the ghost circuit's loop, which is the one large empty
        # region of the wide frame — and the right place for the sentence, since
        # what it names is the bay sitting in that loop.
        closing = self._caption(
            ["everything above happens",
             "before the model reads a word"],
            SHOT_WIDE,
            (-6.0, 2.2),
            role="label",
        )
        self.play(
            FadeIn(closing, shift=UP * theme.PAD_MD),
            run_time=1.00,
            rate_func=motion.ENTER,
        )

        # 57.10 (0.90)
        card = VGroup(
            typography.text(
                "label", "Arc 1 · Inside the model, just enough",
                frame_width=SHOT_WIDE, color=theme.FG, bold=True,
            ),
            typography.text(
                "label", "next — Attention and the KV cache",
                frame_width=SHOT_WIDE, color=theme.FG_MUTED,
            ),
        ).arrange(DOWN, buff=theme.PAD_LG)
        card.move_to(np.array([-6.0, -4.6, 0.0]))
        self.play(
            FadeIn(card, shift=UP * theme.PAD_MD),
            run_time=0.90,
            rate_func=motion.ENTER,
        )

        # 58.00 (1.50) — the trailing hold. The film ends on a finished frame,
        # which is also what carries the deck's last stop past the final fade.
        self.wait(1.50)

    # --------------------------------------------------------------- helpers
    def _caption(self, text, shot: float, at, *, color=None,
                 role: str = "caption"):
        """A line (or explicit lines) of narration, sized for its shot.

        Never a point size: a caption typed for the bench close-up is three
        pixels tall at the pull-back, which is the whole reason
        `lib/typography.py` exists. A list of strings becomes stacked lines —
        the break is stated rather than left to Pango, which wraps against the
        render's pixel width and therefore differently per profile.
        """
        lines = [text] if isinstance(text, str) else list(text)
        note = VGroup(
            *[
                typography.text(
                    role, line, frame_width=shot, color=color or theme.FG_MUTED
                )
                for line in lines
            ]
        )
        if len(note) > 1:
            note.arrange(DOWN, buff=theme.PAD_MD)
        note.move_to(np.array([at[0], at[1], 0.0]))
        return note

    def _counter_row(self, name: str, y: float, *, text: str | None = None,
                     bar: bool = False, color=None):
        """One line of the meter, laid out against a FIXED column origin.

        Not `next_to(label, RIGHT)`: laying a row out around its own label puts
        every row's content wherever that row's word happened to end, and three
        rows of ragged left edge is invisible to the snapshot gate and obvious
        to a viewer.
        """
        label = typography.text(
            "caption", name, frame_width=SHOT_METER, color=theme.FG_MUTED
        )
        label.move_to(np.array([-6.35 + label.width / 2.0, y, 0.0]))

        content: VGroup
        if bar:
            # A schematic window, deliberately carrying no percentage: what
            # fills a context window is not what this beat is about, and a
            # figure here would be one the film cannot source.
            window = SegmentedBar(
                [("used", 3), ("free", 2)],
                length=2.4,
                thickness=0.26,
                labels="none",
                colors=[theme.WARN, theme.SURFACE],
            )
            cap = typography.text(
                "caption", "/ 128,000", frame_width=SHOT_METER,
                color=color or theme.FG, mono=True,
            )
            content = VGroup(window, cap).arrange(RIGHT, buff=theme.PAD_SM)
        else:
            content = VGroup(
                typography.text(
                    "caption", text or "", frame_width=SHOT_METER,
                    color=color or theme.FG, mono=True,
                )
            )
        content.move_to(np.array([-4.20 + content.width / 2.0, y, 0.0]))
        return VGroup(label, content)

    def _language_bar(self, code: str, count: int, y: float):
        """One language's median, as a label, a number and a bar that may leave.

        Returns the parts plus the bar's full width and left edge, so the scene
        can grow it from nothing to its real length in one play without the
        anchor drifting.
        """
        from manim import Rectangle

        label = typography.text(
            "caption", code, frame_width=SHOT_METER, color=theme.FG_MUTED,
            mono=True,
        )
        # -6.40, not the bay's inner edge: the bay is glowing through this beat,
        # and a glow is a dozen stroked copies spreading ~0.4 outward, so a
        # label placed against the border sits in the light rather than beside
        # it.
        label.move_to(np.array([-6.40 + label.width / 2.0, y, 0.0]))
        value = typography.text(
            "caption", str(count), frame_width=SHOT_METER, color=theme.WARN,
            mono=True, bold=True,
        )
        value.move_to(np.array([-5.85 + value.width / 2.0, y, 0.0]))

        left_x = -5.40
        full_width = count * BAR_UNIT
        bar = Rectangle(
            width=0.02, height=0.30,
            fill_color=theme.WARN, fill_opacity=1.0, stroke_width=0,
        )
        bar.move_to(np.array([left_x + 0.01, y, 0.0]))
        self.add(bar)
        return label, value, bar, full_width, left_x
