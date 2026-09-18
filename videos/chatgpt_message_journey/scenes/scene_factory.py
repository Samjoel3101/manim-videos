"""The whole video: one continuous 30-second shot through the factory.

No cuts. The set (`factory_set.py`) is built once and the camera flies through
it, diving into each station in turn and pulling all the way back at the end so
the viewer sees the machine they have just walked through as a single circuit.

Pacing is deliberate and tight — every `run_time` below is part of a 30s budget
laid out in `../script.md`. Changing one means re-balancing its neighbours, so
the beats are grouped and commented with their target timecodes.

The through-line is a single payload that never disappears: typed text becomes a
packet, becomes token chips, becomes vectors, becomes an activation in the
stack, becomes a probability bar, becomes one token, becomes a word on screen.
"""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    RIGHT,
    UP,
    AnimationGroup,
    Dot,
    FadeIn,
    FadeOut,
    Flash,
    LaggedStart,
    MoveAlongPath,
    MovingCameraScene,
    VGroup,
)

from lib import camera, effects, motion, theme, utils
from lib.components.chat_ui import StreamingBubble
from lib.components.factory import Conveyor
from lib.components.probability import ProbabilityChart
from lib.components.tokens import TokenStrip
from lib.components.transformer import TransformerStack
from lib.components.vectors import VectorColumn, stable_vector

# Works both ways: `manim render <path>` loads this file as a top-level script
# (no package context), while the Evaluator imports it as a package module.
try:  # pragma: no cover - whichever branch runs, the other is unreachable
    from .factory_set import FactorySet
except ImportError:
    from factory_set import FactorySet

QUESTION = "How does ChatGPT work?"
ANSWER = "It turns your words into numbers, then predicts the next one."

#: Frame widths for each shot size, so the zoom language stays consistent.
#: A tight shot must clear the 5.2-tall station bay *and* the caption beneath
#: it: at 16:9 a width of 12 gives 6.75 of frame height, which is the minimum
#: that does not clip. Anything smaller crops the bottom row of content.
# Must clear a 9.6-wide bay with margin; kept in step with the set's SHOT_TIGHT,
# which is what the in-bay type is sized against.
W_TIGHT = 13.6
W_CHAT = 11.0
W_MEDIUM = 17.0
W_WIDE = 26.0


def s_glow(scene, station):
    """Shorthand for the pre-built halo belonging to a station."""
    return scene.set.glow_for(station)


class TheFactory(MovingCameraScene):
    def construct(self) -> None:
        theme.apply(self)

        self.set = FactorySet()
        self.add(self.set)
        camera.snap_to(self, self.set.chat, width=W_CHAT)

        self.beat_type_and_send()      # 0.0 → 3.0
        self.beat_leave_the_device()   # 3.0 → 6.2
        payload = self.beat_tokenize() # 6.2 → 10.0
        payload = self.beat_embed(payload)        # 10.0 → 13.6
        payload = self.beat_transform(payload)    # 13.6 → 17.8
        token = self.beat_sample(payload)         # 17.8 → 21.2
        self.beat_return(token)        # 21.2 → 24.6
        self.beat_pull_back()          # 24.6 → 30.0

    # ================================================== 0.0 → 3.0  the screen
    def beat_type_and_send(self) -> None:
        chat = self.set.chat
        chat.input.type_animation(self, QUESTION, cps=13)  # ~1.7s

        ghost = chat.input.text_mob.copy()
        self.add(ghost)
        bubble = chat.commit(chat.make_message(QUESTION, "user"))
        bubble.set_opacity(0)

        self.play(
            ghost.animate.move_to(bubble).set_opacity(0),
            bubble.animate.set_opacity(1),
            run_time=0.5,
            rate_func=motion.ENTER,
        )
        self.remove(ghost)
        chat.input.clear()

        # The message becomes a physical thing the moment it is sent.
        self.packet = Dot(radius=0.13, color=theme.USER)
        self.packet.move_to(bubble.get_right())
        self.play(FadeIn(self.packet, scale=0.4), run_time=0.3, rate_func=motion.ENTER)

    # ============================================ 3.0 → 6.2  out over the wire
    def beat_leave_the_device(self) -> None:
        s = self.set

        # Camera and packet move together — the shot never stops to wait.
        self.play(
            self.packet.animate.move_to(s.rail_chat_to_server.end),
            camera.focus(self, s.server.tile, width=W_MEDIUM, run_time=1.3),
            run_time=1.3,
            rate_func=motion.MOVE,
        )
        self.play(
            s.glow_for(s.server).animate.set_stroke(opacity=1.0),
            self.packet.animate.move_to(s.server.tile.get_center()),
            run_time=0.5,
            rate_func=motion.SNAP,
        )
        self.play(
            self.packet.animate.move_to(s.rail_server_to_model.end),
            camera.focus(self, s.llm, width=W_WIDE + 12, run_time=0.9),
            s.glow_for(s.server).animate.set_stroke(opacity=0.3),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        # Dive into the machine.
        self.play(
            camera.focus(self, s.tokenizer.bay, width=W_TIGHT, run_time=0.5),
            run_time=0.5,
            rate_func=motion.FEATURE,
        )

    # ============================================== 6.2 → 10.0  tokenization
    def beat_tokenize(self):
        station = self.set.tokenizer
        strip = TokenStrip(QUESTION, per_line=3, show_ids=True)
        station.fit(strip)

        self.play(
            s_glow(self, station).animate.set_stroke(opacity=1.0),
            run_time=0.25,
            rate_func=motion.ENTER,
        )
        self.packet.move_to(station.slot_center)
        self.play(
            FadeOut(self.packet, scale=2.0),
            motion.enter(strip.chips, scale=0.7),
            run_time=1.5,
            rate_func=motion.ENTER,
        )
        self.add(strip)

        note = self._note(station, "words → pieces the model knows")
        self.play(FadeIn(note, shift=UP * theme.PAD_XS), run_time=0.35, rate_func=motion.ENTER)
        self.play(
            AnimationGroup(
                *[chip.animate.highlight(theme.EMBED) for chip in strip.chips],
                lag_ratio=0.12,
            ),
            run_time=0.9,
        )
        self.play(
            FadeOut(note),
            s_glow(self, station).animate.set_stroke(opacity=0.3),
            run_time=0.3,
            rate_func=motion.EXIT,
        )
        return strip

    # ================================================= 10.0 → 13.6  embedding
    def beat_embed(self, strip):
        station = self.set.embedder
        columns = VGroup(
            *[
                VectorColumn(
                    stable_vector(chip.token, 10),
                    label=chip.token.strip() or "␣",
                    truncate_at=5,
                )
                for chip in strip.chips
            ]
        ).arrange(RIGHT, buff=theme.PAD_XS)
        station.fit(columns)

        self.play(
            camera.focus(self, station.bay, width=W_TIGHT, run_time=0.7),
            s_glow(self, station).animate.set_stroke(opacity=1.0),
            run_time=0.7,
            rate_func=motion.MOVE,
        )
        # Each chip flies over and becomes its vector — the same payload, changed.
        self.play(
            AnimationGroup(
                *[
                    AnimationGroup(
                        chip.animate.move_to(col).set_opacity(0),
                        FadeIn(col, shift=RIGHT * 0.3),
                    )
                    for chip, col in zip(strip.chips, columns)
                ],
                lag_ratio=0.16,
            ),
            run_time=1.8,
            rate_func=motion.MOVE,
        )
        self.remove(strip)
        self.add(columns)

        note = self._note(station, "every token becomes a direction in meaning-space")
        self.play(FadeIn(note, shift=UP * theme.PAD_XS), run_time=0.3, rate_func=motion.ENTER)
        self.play(
            FadeOut(note),
            s_glow(self, station).animate.set_stroke(opacity=0.3),
            run_time=0.4,
            rate_func=motion.EXIT,
        )
        return columns

    # ============================================== 13.6 → 17.8  the stack
    def beat_transform(self, columns):
        station = self.set.transformer
        stack = TransformerStack(n_layers=96, shown=4, width=2.9, block_height=0.5)
        out = VectorColumn(stable_vector("answer", 10), label="prediction", truncate_at=5)

        # Lay the stack and its output out together and fit the pair, so the
        # prediction column cannot end up hanging outside the bay.
        pair = VGroup(stack, out).arrange(RIGHT, buff=theme.PAD_SM)
        station.fit(pair)
        out.set_opacity(0.0)

        self.play(
            camera.focus(self, station.bay, width=W_TIGHT, run_time=0.7),
            s_glow(self, station).animate.set_stroke(opacity=1.0),
            columns.animate.move_to(station.slot_center).set_opacity(0.0),
            FadeIn(stack),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.remove(columns)

        # Activation climbs the stack; the elided middle keeps 96 layers honest.
        # Stroke-based, not glow: twelve halo layers per block, four blocks, at
        # 0.17s each is a lot of render for a beat the viewer reads as a pulse.
        for block in stack.blocks:
            self.play(block.animate.activate(), run_time=0.17, rate_func=motion.SNAP)
            self.play(block.animate.deactivate(), run_time=0.17, rate_func=motion.EXIT)

        note = self._note(station, "each layer lets every token look at the others")
        self.play(FadeIn(note, shift=UP * theme.PAD_XS), run_time=0.3, rate_func=motion.ENTER)
        self.play(out.animate.set_opacity(1.0), run_time=0.5, rate_func=motion.ENTER)
        self.play(
            FadeOut(note),
            FadeOut(stack),
            s_glow(self, station).animate.set_stroke(opacity=0.3),
            run_time=0.4,
            rate_func=motion.EXIT,
        )
        return out

    # ================================================ 17.8 → 21.2  sampling
    def beat_sample(self, vector):
        station = self.set.sampler
        chart = ProbabilityChart(
            {" It": 3.2, " Your": 1.9, " The": 1.5, " When": 0.6},
            logits=True,
            bar_length=2.0,
        )
        station.fit(chart)

        self.play(
            camera.focus(self, station.bay, width=W_TIGHT, run_time=0.7),
            s_glow(self, station).animate.set_stroke(opacity=1.0),
            vector.animate.move_to(station.slot_center).set_opacity(0.0),
            FadeIn(chart),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.remove(vector)

        note = self._note(station, "a score for every word it knows")
        self.play(FadeIn(note, shift=UP * theme.PAD_XS), run_time=0.3, rate_func=motion.ENTER)
        self.play(chart.animate.select(" It"), run_time=0.6, rate_func=motion.FEATURE)

        winner = TokenStrip([" It"])
        station.fit(winner)
        winner.scale(1.4)
        self.play(
            FadeOut(chart),
            FadeOut(note),
            FadeIn(winner, scale=0.6),
            run_time=0.6,
            rate_func=motion.FEATURE,
        )
        self.play(Flash(winner, color=theme.ASSISTANT, line_length=0.2), run_time=0.3)
        self.play(
            s_glow(self, station).animate.set_stroke(opacity=0.3),
            run_time=0.2,
            rate_func=motion.EXIT,
        )
        return winner

    # =========================================== 21.2 → 24.6  back to the user
    def beat_return(self, token) -> None:
        s = self.set

        # Sized for the finished sentence and placed in the assistant gutter, so
        # it never reflows as words land — the same thing a real streaming UI does.
        self.answer = StreamingBubble(ANSWER, max_width=4.0)
        self.answer.next_to(s.chat.messages[-1], DOWN, buff=theme.PAD_MD)
        self.answer.shift(
            RIGHT * ((s.chat.frame.get_left()[0] + theme.PAD_MD) - self.answer.get_left()[0])
        )
        self.answer.body.set_opacity(0.0)
        self.add(self.answer)

        courier = Dot(radius=0.13, color=theme.ASSISTANT).move_to(token.get_center())
        self.play(
            FadeOut(token, scale=1.6),
            FadeIn(courier, scale=0.5),
            run_time=0.35,
            rate_func=motion.SNAP,
        )

        # Same rule as the loop below: put the courier on the rail first, then
        # attach the trail, or its first segment is a chord from wherever it was.
        courier.move_to(s.rail_out_of_column.end)
        trail = effects.comet(courier, color=theme.ASSISTANT, dissipating_time=0.22)
        self.add(trail)
        self.play(
            MoveAlongPath(courier, s.return_rail.path, run_time=1.9),
            camera.focus(self, s.return_rail, width=W_WIDE + 8, run_time=1.9),
            run_time=1.9,
            rate_func=motion.MOVE,
        )
        self.remove(trail)
        self.play(
            camera.focus(self, s.chat, width=W_CHAT, run_time=0.75),
            FadeOut(courier, scale=0.3),
            self.answer.body.animate.set_opacity(1.0),
            run_time=0.75,
            rate_func=motion.ENTER,
        )
        # Three words, not one: a bubble sized for eleven looks broken holding one.
        self.play(self.answer.animate.reveal(3), run_time=0.4, rate_func=motion.ENTER)

    # ============================================= 24.6 → 30.0  the whole plant
    def beat_pull_back(self) -> None:
        s = self.set
        loop = s.circuit()

        self.play(
            camera.frame_all(self, [s.everything], pad=1.0, run_time=1.4),
            *s.reveal_labels(),
            run_time=1.4,
            rate_func=motion.FEATURE,
        )

        # Three more tokens run the entire circuit. Same machine, seen whole.
        # Each node reacts as the token reaches it, rather than sitting lit.
        passes = 2
        words_per_pass = max(1, (self.answer.word_count - 3) // passes)
        for i in range(passes):
            # Place the runner on the path BEFORE attaching its trail. A comet
            # traces get_center from the frame it is added, so a dot still
            # sitting at the origin draws one long chord across the set on its
            # first frame — which is what made the trail appear to cut through
            # the machines.
            runner = Dot(radius=0.22, color=theme.TOKEN)
            runner.move_to(loop.point_from_proportion(0))
            # Short dissipation: at this speed a long tail stops reading as a
            # comet and starts reading as a line drawn through the machines.
            spark = effects.comet(runner, color=theme.TOKEN, width=9,
                                  dissipating_time=0.14)
            self.add(spark, runner)
            self.play(
                MoveAlongPath(runner, loop, run_time=1.7),
                # Glow only — no scale pop. Animating a node's geometry here
                # meant animating a VGroup, which interpolates the group's own
                # (transparent) rgba onto its children and blanked every label
                # in the bay. The light alone reads as the machine reacting.
                LaggedStart(
                    *[
                        s.glow_for(node).animate.set_stroke(opacity=1.0)
                        for node in s.nodes
                    ],
                    lag_ratio=0.22,
                ),
                run_time=1.7,
                rate_func=motion.MOVE,
            )
            self.remove(runner, spark)
            self.play(
                LaggedStart(
                    *[
                        s.glow_for(node).animate.set_stroke(opacity=s.resting_glow)
                        for node in s.nodes
                    ],
                    lag_ratio=0.12,
                ),
                self.answer.animate.reveal(3 + (i + 1) * words_per_pass),
                run_time=0.28,
            )

        self.play(self.answer.animate.reveal(self.answer.word_count), run_time=0.3)
        self.wait(0.6)

    # ------------------------------------------------------------- helpers
    def _note(self, station, text: str):
        """A caption under a station bay. Local: only this scene needs it."""
        note = utils._text(text, theme.SIZE_CAPTION, theme.FG_MUTED, theme.FONT_BODY)
        utils.fit_text(note, station.bay_width * 1.25)
        note.next_to(station.bay, DOWN, buff=theme.PAD_SM)
        return note
