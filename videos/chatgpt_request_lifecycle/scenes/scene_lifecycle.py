"""The whole video: one continuous 45-second shot through the request lifecycle.

No cuts. The set (`lifecycle_set.py`) is built once and the camera flies through
it — out along the top band, down the right into the inference stack, back along
the bottom, and all the way out at the end so the viewer recognises the plant
they have just walked through as a single closed circuit.

Pacing is deliberate and tight: every `run_time` below is part of a 45s budget
laid out in `../script.md`, and changing one means re-balancing its neighbours.
The beats are grouped with their target timecodes in the `# ===` comments. Those
are the arithmetic sum of the `run_time`s below — what a re-timer needs — and the
shipped cut runs a little longer than their total, because Manim rounds every
play up to a whole frame and there are about seventy of them. The measured figure
is in `scenes.json`.

The through-line is a single payload that is never destroyed, only transformed:

    typed text → a request with metadata → a stamped packet → a traced packet →
    a sliver at the bottom of a 3,900-token prompt → token chips with ids →
    a cached prefix plus a short new tail → one row in a running batch →
    a bar in a distribution → one token → SSE chunks → words in the bubble →
    a row in a ledger

Two structural choices worth knowing before editing anything:

* **The packet waits at a band station's door rather than sitting in its slot.**
  The plan for this film had it stop at `slot_center`; that is where the
  CheckList and the meters go, and a dot on top of a tick list reads as a
  rendering mistake. Stopping it on the incoming rail, right at the bay's left
  edge, says "the request is at the Edge tier" just as clearly and leaves the
  slot to the thing the beat is about.
* **Each beat clears its own content before the camera leaves.** Ten bays still
  holding their close-up props at the pull-back is ten pieces of litter
  competing with the wide labels that are supposed to name them.
"""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
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

from lib import camera, effects, motion, routing, theme, typography
from lib.components.chat_ui import StreamingBubble, TypingIndicator
from lib.components.checks import CheckList
from lib.components.glyph import Glyph
from lib.components.network import PacketStream
from lib.components.probability import ProbabilityBar, ProbabilityChart
from lib.components.stacked import SegmentedBar
from lib.components.tokens import TokenStrip
from lib.components.transformer import TransformerStack

# Works both ways: `manim render <path>` loads this file as a top-level script
# (no package context), while the Evaluator imports it as a package module.
try:  # pragma: no cover - whichever branch runs, the other is unreachable
    from . import props
    from .lifecycle_set import LOOP_RUN_TIME, SHOT_TIGHT, SHOT_TIGHT_OUTER, LifecycleSet
except ImportError:  # pragma: no cover
    import props
    from lifecycle_set import LOOP_RUN_TIME, SHOT_TIGHT, SHOT_TIGHT_OUTER, LifecycleSet

QUESTION = "What happens when I hit send?"
#: Eleven words, and it starts with "A" — which is the token the sampler beat
#: picks out of its distribution. Keep the two consistent: a winner that does
#: not match the reply is exactly the kind of single-token error the snapshot
#: gate is documented as unable to see.
ANSWER = "A dozen machines touch it before the first word comes back."

#: Frame widths for each shot size, so the zoom language stays consistent.
#: `lib/components/chat_ui` is sized in absolute theme points against a full
#: 14-unit frame, so this is the width at which its type comes out the size it
#: was drawn for — and at 16:9 it gives 7.87 of frame height, which clears the
#: 9.6x7.0 window with margin.
W_CHAT = 14.0
#: The chat plus the request card beside it.
W_REQ = 18.0
#: A 10.0-wide band bay with its neighbour's edge in frame. Kept in step with
#: the set's SHOT_TIGHT_OUTER, which is what the bay type is sized against.
W_SERVICE = SHOT_TIGHT_OUTER
#: An in-box bay, in step with the set's SHOT_TIGHT.
W_TIGHT = SHOT_TIGHT
#: Following the reply along the long climb home. Wide enough to hold the whole
#: return rail AND the chat window it ends at: at 40 the rail fits but the top
#: of the chat is sliced off by the frame edge, which reads as a rendering
#: mistake rather than as a camera move. Framed against both, not just the rail.
W_TRAVEL = 45.0
#: The epilogue bay. Wider than a band close-up, and framed 2.0 to the LEFT of
#: the bay, for one reason: the swing from the chat down to the after bay is 25
#: units of empty world, and at W_SERVICE the camera spent about half a second
#: looking at nothing at all — a black frame in the middle of an uncut take,
#: which reads as a dropped shot. At 20 with the frame pushed left, the return
#: rail at x=-30.5 stays in shot for the whole move, so the camera is visibly
#: travelling down something rather than through a void.
W_AFTER = 20.0


class TheLifecycle(MovingCameraScene):
    def construct(self) -> None:
        theme.apply(self)

        self.set = LifecycleSet()
        self.add(self.set)
        camera.snap_to(self, self.set.chat, width=W_CHAT)

        #: Everything currently riding along with the packet — the dot plus the
        #: stamps machines have put on it. Moved with `_carry`, never as a
        #: VGroup: animating a container VGroup's geometry interpolates the
        #: group's own (transparent) rgba onto its children.
        self.parcel: list = []

        self.beat_client()             # 0.00 → 4.59
        self.beat_edge()               # 4.59 → 8.79
        self.beat_gateway()            # 8.79 → 12.59
        self.beat_orchestrator()       # 12.59 → 17.79
        strip = self.beat_tokenize()   # 17.79 → 21.59
        self.beat_prefill(strip)       # 21.59 → 25.44
        self.beat_decode()             # 25.44 → 29.44
        token = self.beat_sample()     # 29.44 → 32.84
        self.beat_stream(token)        # 32.84 → 36.74
        self.beat_after()              # 36.74 → 39.24
        self.beat_pull_back()          # 39.24 → 44.34

    # ==================================================== 0.00 → 4.59  client
    def beat_client(self) -> None:
        """Type it, send it, and watch the browser build a whole document."""
        chat = self.set.chat
        chat.input.type_animation(self, QUESTION, cps=17)  # ~1.71s

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

        # The optimistic UI: the spinner appears before anything has left the
        # machine, which is the whole point of the next ten seconds.
        #
        # `TypingIndicator.pulse` is not used: it calls `scene.play` without a
        # rate function, and a bare default easing anywhere in this film is a
        # bug (AGENTS rule 4). The dots are staggered here instead.
        spinner = TypingIndicator(color=theme.ASSISTANT)
        chat.place(spinner, "assistant")
        self.play(FadeIn(spinner, scale=0.6), run_time=0.2, rate_func=motion.ENTER)
        self.play(
            LaggedStart(
                *[dot.animate.set_opacity(1.0) for dot in spinner.dots],
                lag_ratio=0.4,
            ),
            run_time=0.28,
            rate_func=motion.SNAP,
        )
        self.spinner = spinner

        # What "hitting send" actually posts. A close-up-only prop: it is faded
        # out at the end of this beat, which is also why it is not part of
        # `LifecycleSet.everything` — a prop nobody can see must not be able to
        # widen the pull-back.
        card = props.RequestCard(
            [
                ("message", '"What happens when I hit send?"'),
                ("conversation", "new"),
                ("model", "gpt-5"),
                ("locale", "en-GB · Europe/London"),
                ("accept", "text/event-stream"),
            ],
            frame_width=W_REQ,
        )
        # Placed clear of every rail and high enough that widening to W_REQ can
        # hold it and the whole chat window at once — the camera keeps the chat
        # centred and drifts right and down to make room.
        card.move_to(np.array([-16.0, 5.5, 0.0]))
        self.play(
            FadeIn(card, shift=UP * theme.PAD_SM),
            camera.focus(
                self, self.set.chat, width=W_REQ,
                shift=RIGHT * 4.0 + DOWN * 0.7, run_time=0.9,
            ),
            run_time=0.9,
            rate_func=motion.ENTER,
        )

        # The message becomes a physical thing the moment it is posted.
        self.packet = Dot(radius=0.13, color=theme.USER)
        self.packet.move_to(bubble.get_right() + RIGHT * theme.PAD_SM)
        self.parcel = [self.packet]
        self.play(
            FadeIn(self.packet, scale=0.4), run_time=0.4, rate_func=motion.ENTER
        )
        # The card collapses into the packet rather than merely vanishing: the
        # payload is not replaced at any point in this film, only transformed.
        #
        # This is the ONE place this scene scales a container VGroup, which is
        # normally a bug — interpolating a group's own (transparent) rgba drags
        # every child's opacity down with it. Here that side effect IS the
        # intent: the card is on its way to opacity 0 and is removed on the next
        # line. Anywhere the thing has to survive the animation, animate the
        # shape instead (see `_carry`, which shifts each member by one delta
        # rather than moving a group).
        self.play(
            card.animate.move_to(self.packet).scale(0.05).set_opacity(0.0),
            run_time=0.6,
            rate_func=motion.MOVE,
        )
        self.remove(card)

    # ================================================= 4.59 → 8.79  edge tier
    def beat_edge(self) -> None:
        """Prove you are not a bot, then get scored by the edge."""
        s = self.set

        self.play(
            *self._carry(s.bot_check.tile.get_left() + LEFT * 0.45),
            camera.focus(self, s.bot_check.tile, width=W_SERVICE, run_time=1.0),
            run_time=1.0,
            rate_func=motion.MOVE,
        )
        # A stamp, not a new packet. Each machine leaves evidence on the same
        # payload; that accumulation is what makes the first third read as one
        # journey rather than five unrelated diagrams.
        stamp = props.StampChip("pow ✓", color=theme.WARN, frame_width=W_SERVICE)
        stamp.next_to(self.packet, UP, buff=theme.PAD_XS)
        self.play(
            s.glow_for(s.bot_check).animate.set_stroke(opacity=1.0),
            FadeIn(stamp, scale=0.6),
            run_time=0.6,
            rate_func=motion.SNAP,
        )
        self.parcel.append(stamp)

        checks = CheckList(
            ["WAF", ("bot score", "0.02"), ("rate limit", "12 / 60")],
            color=theme.NETWORK,
            frame_width=W_SERVICE,
        )
        s.edge.fit(checks)
        self.play(
            *self._carry(s.edge.bay.get_left() + LEFT * 0.35),
            camera.focus(self, s.edge.bay, width=W_SERVICE, run_time=0.9),
            s.glow_for(s.bot_check).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.play(
            s.glow_for(s.edge).animate.set_stroke(opacity=1.0),
            FadeIn(checks, shift=UP * theme.PAD_XS),
            run_time=0.4,
            rate_func=motion.ENTER,
        )
        self.play(
            LaggedStart(*checks.pass_all(), lag_ratio=0.35),
            run_time=0.7,
            rate_func=motion.ENTER,
        )

        note = self._note(s.edge, "proxied to the nearest healthy region", W_SERVICE)
        self.play(
            FadeIn(note, shift=UP * theme.PAD_XS), run_time=0.3, rate_func=motion.ENTER
        )
        self.play(
            FadeOut(note),
            FadeOut(checks),
            s.glow_for(s.edge).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.3,
            rate_func=motion.EXIT,
        )

    # =================================================== 8.79 → 12.59  gateway
    def beat_gateway(self) -> None:
        """Who are you, what have you paid for, and how much is left."""
        s = self.set

        checks = CheckList(
            ["session", ("plan", "pro → gpt-5")],
            color=theme.WARN,
            frame_width=W_SERVICE,
        )
        meter = self._meter("tokens/min", "{:.0%}", theme.WARN, scale=1.35)
        content = VGroup(checks, meter).arrange(
            DOWN, buff=theme.PAD_SM, aligned_edge=LEFT
        )
        s.gateway.fit(content)

        self.play(
            *self._carry(s.gateway.bay.get_left() + LEFT * 0.35),
            camera.focus(self, s.gateway.bay, width=W_SERVICE, run_time=0.9),
            s.glow_for(s.gateway).animate.set_stroke(opacity=1.0),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.play(
            FadeIn(content, shift=UP * theme.PAD_XS),
            run_time=0.35,
            rate_func=motion.ENTER,
        )
        self.play(
            LaggedStart(*checks.pass_all(), lag_ratio=0.4),
            run_time=0.65,
            rate_func=motion.ENTER,
        )
        # `.animate.set_value` on a ProbabilityBar is the risky path — the
        # method replaces `value_mob`, so the submobject list changes and Manim
        # has to align two unequal glyph trees. It was probed on a throwaway
        # scene before being used here and it interpolates cleanly; the number
        # morphs rather than ticking, which at 0.9s reads as a meter filling.
        self.play(
            meter.animate.set_value(0.62), run_time=0.9, rate_func=motion.FEATURE
        )

        trace = props.StampChip("trace 7f3a…", color=theme.NETWORK, frame_width=W_SERVICE)
        trace.next_to(self.parcel[-1], UP, buff=theme.PAD_XS)
        self.play(FadeIn(trace, scale=0.6), run_time=0.5, rate_func=motion.SNAP)
        self.parcel.append(trace)

        self.play(
            FadeOut(content),
            s.glow_for(s.gateway).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.5,
            rate_func=motion.EXIT,
        )

    # ============================================== 12.59 → 17.79  orchestrator
    def beat_orchestrator(self) -> None:
        """The biggest beat: the part that is not the model at all."""
        s = self.set
        station = s.orchestrator

        sources = VGroup(
            *[
                self._chip(icon, name)
                for icon, name in (
                    ("database", "conversation"),
                    ("sparkles", "memory"),
                    ("file-text", "files"),
                )
            ]
        ).arrange(RIGHT, buff=theme.PAD_MD)

        bar = SegmentedBar(
            {
                "system prompt": 2400,
                "tool definitions": 1150,
                "memory + prefs": 380,
                "your message": 7,
            },
            # Sized to fill the bay's slot exactly (4.9 wide, of which the bar
            # takes 2.3, a PAD_MD gutter 0.5 and the legend 2.0). This is the
            # film's key beat and the first version, at length=2.0, left the bar
            # looking incidental beside its own legend.
            length=2.3,
            thickness=0.4,
            labels="legend",
            legend_width=2.0,
            # 7 of 3,937 is 0.18% of the bar: sub-pixel, i.e. invisible, i.e.
            # the beat fails. The drawn slice is floored; the legend still
            # prints 7. See lib/components/stacked.py.
            min_segment=0.035,
            colors=[theme.NETWORK, theme.ATTENTION, theme.EMBED, theme.USER],
            frame_width=W_SERVICE,
        )
        content = VGroup(sources, bar).arrange(DOWN, buff=theme.PAD_SM)
        # margin=1.0, not the 0.92 default: the content is already built to the
        # slot's exact width, and the default margin would shrink it by 8% for
        # no reason and take the legend under the readability floor with it.
        station.fit(content, margin=1.0)
        bar.set_shown(0)

        self.play(
            *self._carry(station.bay.get_left() + LEFT * 0.35),
            camera.focus(self, station.bay, width=W_SERVICE, run_time=0.9),
            s.glow_for(station).animate.set_stroke(opacity=1.0),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.play(motion.enter(sources, scale=0.7), run_time=1.0, rate_func=motion.ENTER)
        self.add(bar)
        # Grown a segment at a time so the prompt visibly *assembles*. Opacity
        # only, so the submobject list is constant and `.animate` interpolates.
        for shown in range(1, len(bar) + 1):
            self.play(
                bar.animate.set_shown(shown), run_time=0.35, rate_func=motion.MOVE
            )

        note = self._note(
            station,
            "your 7 tokens · ~3,900 of scaffolding",
            W_SERVICE,
            sub="new conversation — no history yet",
        )
        # Pushed off the midline. This is the one band station with a rail
        # leaving its BOTTOM edge, and that rail comes down the bay's centre —
        # exactly where a centred caption sits. The words won (they are drawn
        # later) but the line showed through every gap between them, which reads
        # as a stray stroke rather than as a conveyor.
        note.shift(LEFT * 3.4)
        self.play(
            # dim_others=0.45 rather than the 0.35 default: the caption is
            # pointing AT the other segments ("~3,900 of scaffolding"), so their
            # names have to stay readable while the sliver is highlighted.
            bar.animate.emphasise("your message", dim_others=0.45),
            FadeIn(note, shift=UP * theme.PAD_XS),
            run_time=0.9,
            rate_func=motion.FEATURE,
        )

        badges = VGroup(
            props.StampChip(
                "route → gpt-5 · low effort", color=theme.ASSISTANT,
                frame_width=W_SERVICE,
            ),
            props.StampChip(
                "input classifier ✓", color=theme.ASSISTANT, frame_width=W_SERVICE
            ),
        ).arrange(RIGHT, buff=theme.PAD_SM)
        badges.next_to(note, DOWN, buff=theme.PAD_SM)
        self.play(motion.enter(badges, scale=0.8), run_time=0.6, rate_func=motion.ENTER)

        # The packet drops to the bay's bottom edge, which is where the rail
        # into the machine starts. Doing it here rather than at the top of the
        # next beat means the descent can be one uninterrupted MoveAlongPath.
        self.play(
            FadeOut(note),
            FadeOut(badges),
            FadeOut(content),
            *[m.animate.set_opacity(0.0) for m in self.parcel[1:]],
            self.packet.animate.move_to(station.bay.get_bottom()),
            s.glow_for(station).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.4,
            rate_func=motion.EXIT,
        )
        self.remove(*self.parcel[1:])
        self.parcel = [self.packet]

    # ================================================= 17.79 → 21.59  tokenize
    def beat_tokenize(self):
        """Into the machine, and out of language."""
        s = self.set
        station = s.tokenizer

        # Built from the DRAWN rails, never from centres — that is the whole
        # reason routing.join exists (AGENTS rule 5).
        descent = routing.join(s.rail_orch_to_box, s.rail_into_column)
        self.packet.move_to(descent.point_from_proportion(0))
        self.play(
            MoveAlongPath(self.packet, descent, run_time=1.2),
            camera.focus(self, station.bay, width=W_TIGHT, run_time=1.2),
            s.glow_for(station).animate.set_stroke(opacity=1.0),
            run_time=1.2,
            rate_func=motion.MOVE,
        )

        # Broken over three lines rather than fitted down: the chat template is
        # the point, and a single 60-character line scaled into a 4.6-wide slot
        # is a grey smear.
        template = typography.text(
            "micro",
            "<|system|> … <|user|>\nWhat happens when I hit send?\n<|assistant|>",
            frame_width=W_TIGHT,
            color=theme.FG_MUTED,
            mono=True,
        )
        station.fit(template, margin=1.0)
        self.packet.move_to(station.slot_center)
        self.play(
            FadeOut(self.packet, scale=2.0),
            FadeIn(template, shift=UP * theme.PAD_XS),
            run_time=0.7,
            rate_func=motion.ENTER,
        )

        # per_line=4, not 3: seven chips in three rows is 2.3 tall and the slot
        # is 1.6, so `fit` would shrink the ids below the readability floor.
        # Two rows fit at full size.
        strip = TokenStrip(QUESTION, per_line=4, show_ids=True)
        station.fit(strip, margin=1.0)
        # Two plays, not one. The first cut ran the template's fade-out and the
        # chips' staggered entrance in a single 1.2s play, and because both
        # occupy the same slot the middle two-thirds of the beat was a line of
        # mono text showing through a row of chips — legible as neither. The
        # template leaves first, quickly, and then the chips arrive.
        self.play(
            FadeOut(template, shift=UP * theme.PAD_XS),
            run_time=0.3,
            rate_func=motion.EXIT,
        )
        self.play(
            motion.enter(strip.chips, scale=0.7),
            run_time=0.9,
            rate_func=motion.ENTER,
        )
        self.add(strip)

        note = self._note(station, "sub-word pieces → integer ids", W_TIGHT, tight=True)
        self.play(
            FadeIn(note, shift=UP * theme.PAD_XS), run_time=0.4, rate_func=motion.ENTER
        )
        self.play(
            FadeOut(note),
            s.glow_for(station).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.3,
            rate_func=motion.EXIT,
        )
        return strip

    # ============================================== 21.59 → 25.44  prefill / KV
    def beat_prefill(self, strip) -> None:
        """Most of this prompt has been computed before, for somebody else."""
        s = self.set
        station = s.prefill

        bar = SegmentedBar(
            {"cached prefix": 3900, "new tail": 37},
            length=3.4,
            thickness=0.4,
            labels="inline",
            min_segment=0.05,
            colors=[theme.FG_FAINT, theme.TOKEN],
            frame_width=W_TIGHT,
        )
        station.fit(bar, margin=1.0)

        self.play(
            camera.focus(self, station.bay, width=W_TIGHT, run_time=0.9),
            s.glow_for(station).animate.set_stroke(opacity=1.0),
            AnimationGroup(
                *[
                    chip.animate.move_to(station.slot_center).set_opacity(0.0)
                    for chip in strip.chips
                ],
                lag_ratio=0.06,
            ),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.remove(strip)
        self.play(
            FadeIn(bar, shift=UP * theme.PAD_XS), run_time=0.85, rate_func=motion.ENTER
        )

        # This caption NAMES the highlighted segment on purpose. The inline
        # label rule in SegmentedBar drops any label narrower than 12% of the
        # bar, and "new tail" is 5% — so without the caption the viewer is shown
        # an emphasised amber sliver with nothing anywhere saying what it is.
        note = self._note(
            station, "only the new tail is computed", W_TIGHT, tight=True
        )
        self.play(
            bar.animate.emphasise("new tail"),
            FadeIn(note, shift=UP * theme.PAD_XS),
            run_time=0.8,
            rate_func=motion.FEATURE,
        )
        after = self._note(
            station,
            "the prefix is identical for everyone — its keys and values are reused",
            W_TIGHT,
            tight=True,
        )
        self.play(FadeOut(note), run_time=0.25, rate_func=motion.EXIT)
        self.play(
            FadeIn(after, shift=UP * theme.PAD_XS),
            run_time=0.35,
            rate_func=motion.ENTER,
        )
        self.play(
            FadeOut(after),
            FadeOut(bar),
            s.glow_for(station).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.7,
            rate_func=motion.EXIT,
        )

    # ================================================ 25.44 → 29.44  decode loop
    def beat_decode(self) -> None:
        """One token per step — and you are sharing the machine."""
        s = self.set
        station = s.decode

        # shown=2 rather than the reference film's 4: this bay is 2.1 tall where
        # that one was 2.4, so four blocks would be `fit`-scaled to about 0.66
        # and the layer captions would land under typography.MIN_READABLE.
        stack = TransformerStack(n_layers=96, shown=2, width=2.2, block_height=0.62)
        lanes = props.BatchLanes(lanes=4, mine=1, steps=3, frame_width=W_TIGHT)
        pair = VGroup(stack, lanes).arrange(RIGHT, buff=theme.PAD_MD)
        station.fit(pair, margin=1.0)

        self.play(
            camera.focus(self, station.bay, width=W_TIGHT, run_time=0.9),
            s.glow_for(station).animate.set_stroke(opacity=1.0),
            FadeIn(pair, shift=UP * theme.PAD_XS),
            run_time=0.9,
            rate_func=motion.MOVE,
        )

        # Stroke-based activation, not a glow. Twelve halo layers per block per
        # step is a lot of render for something the viewer reads as a pulse —
        # the same call the reference film's transformer beat makes.
        for _ in range(3):
            self.play(
                stack.blocks[0].animate.activate(),
                lanes.animate.step(),
                run_time=0.32,
                rate_func=motion.SNAP,
            )
            self.play(
                stack.blocks[0].animate.deactivate(),
                run_time=0.18,
                rate_func=motion.EXIT,
            )

        # The caption and the meter SHARE the 0.6-unit gap below the bay, side by
        # side. The slot (4.6 x 1.6) is already full of the stack and the lanes,
        # and the first cut put both of these under the bay independently — they
        # landed on top of each other and the caption read "one token per step —
        # your request rides in a b[atch 0%]". They are laid out as one row now,
        # which is also why the caption is short enough to leave the meter room.
        note = self._note(
            station, "one token per step — you ride in a batch",
            W_TIGHT, tight=True,
        )
        meter = self._meter("batch", "{:.0%}", theme.ATTENTION, scale=1.15)
        gutter = VGroup(note, meter).arrange(RIGHT, buff=theme.PAD_MD)
        gutter.next_to(station.bay, DOWN, buff=0.11)
        self.play(
            FadeIn(note, shift=UP * theme.PAD_XS),
            FadeIn(meter, shift=UP * theme.PAD_XS),
            run_time=0.45,
            rate_func=motion.ENTER,
        )
        self.play(meter.animate.set_value(0.83), run_time=0.65, rate_func=motion.MOVE)

        self.play(
            FadeOut(note),
            FadeOut(meter),
            FadeOut(pair),
            s.glow_for(station).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.5,
            rate_func=motion.EXIT,
        )

    # =================================================== 29.44 → 32.84  sampling
    def beat_sample(self):
        """A score for every word it knows. One gets picked."""
        s = self.set
        station = s.sampler

        chart = ProbabilityChart(
            {" A": 3.2, " Your": 1.9, " It": 1.5, " When": 0.6},
            logits=True,
            bar_length=1.7,
            gap=theme.PAD_XS,
        )
        station.fit(chart, margin=1.0)

        self.play(
            camera.focus(self, station.bay, width=W_TIGHT, run_time=0.9),
            s.glow_for(station).animate.set_stroke(opacity=1.0),
            FadeIn(chart, shift=UP * theme.PAD_XS),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        note = self._note(station, "temperature · top-p · top-k", W_TIGHT, tight=True)
        self.play(
            FadeIn(note, shift=UP * theme.PAD_XS), run_time=0.4, rate_func=motion.ENTER
        )
        # " A", because the answer starts "A dozen machines…".
        self.play(chart.animate.select(" A"), run_time=0.6, rate_func=motion.FEATURE)

        winner = TokenStrip([" A"])
        station.fit(winner, margin=1.0)
        winner.scale(0.8)
        self.play(
            FadeOut(chart),
            FadeOut(note),
            FadeIn(winner, scale=0.6),
            run_time=0.8,
            rate_func=motion.SNAP,
        )
        self.play(
            Flash(winner, color=theme.ASSISTANT, line_length=0.15),
            run_time=0.4,
            rate_func=motion.SNAP,
        )
        self.play(
            s.glow_for(station).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.3,
            rate_func=motion.EXIT,
        )
        return winner

    # ================================================ 32.84 → 36.74  stream back
    def beat_stream(self, token) -> None:
        """Detokenise, check, and push it down the wire as it is written."""
        s = self.set

        # Sized for the finished sentence up front — the same thing a real
        # streaming UI does — and handed to the chat window to PLACE. Positioning
        # a bubble by hand near the window is how a reply once drew itself across
        # the composer and everything below it.
        self.answer = StreamingBubble(ANSWER, max_width=s.chat.message_max_width)
        self._fit_in_window(self.answer, s.chat)
        s.chat.post(self.answer, "assistant")
        # `post` → `commit` → `_scroll_into_view` → `_hide_scrolled_off`, which
        # calls `set_opacity(1.0)` on every message that is still in view — and
        # that undoes the hidden state a StreamingBubble is built in. Without
        # the `reveal(0)` here the whole answer is legible from the moment the
        # bubble is posted, ten seconds before the reply is supposed to arrive,
        # and every later `reveal(n)` is a no-op the viewer cannot see. It is
        # invisible to the test suite: the bubble is correctly positioned, the
        # right size, and never leaves the window.
        self.answer.reveal(0)
        self.answer.body.set_opacity(0.0)
        self.add(self.answer)

        courier = Dot(radius=0.13, color=theme.ASSISTANT).move_to(token.get_center())
        self.play(
            FadeOut(token, scale=1.6),
            FadeIn(courier, scale=0.5),
            run_time=0.35,
            rate_func=motion.SNAP,
        )

        # Place the dot on the path BEFORE attaching its trail. A comet traces
        # `get_center` from the frame it is added, so a dot still sitting where
        # it was draws one long chord across the whole set on its first frame —
        # which looks exactly like a routing bug and is not one.
        out = routing.join(s.rail_out_of_column, s.rail_box_to_stream)
        courier.move_to(out.point_from_proportion(0))
        trail = effects.comet(
            courier, color=theme.ASSISTANT, dissipating_time=0.12
        )
        self.add(trail, courier)
        self.play(
            MoveAlongPath(courier, out, run_time=1.0),
            camera.focus(self, s.stream.bay, width=W_SERVICE, run_time=1.0),
            run_time=1.0,
            rate_func=motion.MOVE,
        )
        self.remove(trail)

        checks = CheckList(
            ["detokenise", ("output safety", "✓"), ("tool call?", "no")],
            color=theme.ASSISTANT,
            frame_width=W_SERVICE,
        )
        s.stream.fit(checks)
        self.play(
            s.glow_for(s.stream).animate.set_stroke(opacity=1.0),
            FadeIn(checks, shift=UP * theme.PAD_XS),
            FadeOut(courier, scale=0.4),
            run_time=0.4,
            rate_func=motion.ENTER,
        )
        self.play(
            LaggedStart(*checks.pass_all(), lag_ratio=0.35),
            run_time=0.6,
            rate_func=motion.ENTER,
        )

        # Four chunks, staggered, so the reply reads as arriving in pieces.
        stream = PacketStream(count=4, color=theme.ASSISTANT, radius=0.1)
        home = s.rail_stream_home.path
        for packet in stream.packets:
            packet.move_to(home.get_start())
        self.add(stream)
        self.play(
            LaggedStart(
                *[
                    MoveAlongPath(packet, home, run_time=0.9)
                    for packet in stream.packets
                ],
                lag_ratio=0.18,
            ),
            # Framed against the rail AND the chat, not the rail alone: the rail
            # tops out at y=+9 and the chat at +12.2, so a shot fitted to the
            # rail slices the top off the window the packets are flying towards.
            camera.focus(
                self, VGroup(s.rail_stream_home, s.chat), width=W_TRAVEL,
                run_time=0.9,
            ),
            FadeOut(checks),
            s.glow_for(s.stream).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.9,
            rate_func=motion.MOVE,
        )
        self.remove(stream)

        # The bubble's frame and its first words are two plays, not one. They
        # would otherwise be two `.animate` builders over the same family —
        # `self.answer.body` inside `self.answer` — and Manim resolves that by
        # letting one silently win.
        self.play(
            camera.focus(self, s.chat, width=W_CHAT, run_time=0.45),
            FadeOut(self.spinner),
            self.answer.body.animate.set_opacity(1.0),
            run_time=0.45,
            rate_func=motion.ENTER,
        )
        # Three words, not one: a bubble sized for eleven looks broken holding
        # one.
        self.play(
            self.answer.animate.reveal(3), run_time=0.2, rate_func=motion.ENTER
        )

    # ==================================================== 36.74 → 39.24  after
    def beat_after(self) -> None:
        """And a copy goes somewhere else entirely."""
        s = self.set

        # Spawned AT THE FORK, not wherever it is convenient. A dot placed
        # elsewhere and then given a trail draws one long chord across the whole
        # set on its first frame — the stray diagonal bug, again.
        fork = s.rail_after_spur.path
        copy_dot = Dot(radius=0.11, color=theme.FG_MUTED)
        copy_dot.move_to(fork.get_start())
        trail = effects.comet(
            copy_dot, color=theme.FG_MUTED, width=5, dissipating_time=0.12
        )
        self.add(trail, copy_dot)
        self.play(
            MoveAlongPath(copy_dot, fork, run_time=1.1),
            camera.focus(
                self, s.after.bay, width=W_AFTER, shift=LEFT * 2.0, run_time=1.1
            ),
            s.glow_for(s.after).animate.set_stroke(opacity=1.0),
            run_time=1.1,
            rate_func=motion.MOVE,
        )
        self.remove(trail)

        # Typed for W_AFTER, not W_SERVICE: type is sized against the shot it is
        # read in, and a list built for a 16-wide frame lands under
        # typography.MIN_READABLE when the camera holds at 20.
        checks = CheckList(
            [
                "stored",
                ("tokens", "3,974 in · 12 out"),
                ("queued", "title · memory"),
            ],
            color=theme.NETWORK,
            frame_width=W_AFTER,
        )
        s.after.fit(checks)
        self.play(
            FadeIn(checks, shift=UP * theme.PAD_XS),
            FadeOut(copy_dot, scale=0.4),
            run_time=0.35,
            rate_func=motion.ENTER,
        )
        self.play(
            LaggedStart(*checks.pass_all(), lag_ratio=0.35),
            run_time=0.65,
            rate_func=motion.ENTER,
        )
        self.play(
            FadeOut(checks),
            s.glow_for(s.after).animate.set_stroke(opacity=s.resting_glow),
            run_time=0.4,
            rate_func=motion.EXIT,
        )

    # =============================================== 39.24 → 44.34  whole plant
    def beat_pull_back(self) -> None:
        """All the way out. The viewer has stood inside every part of this."""
        s = self.set
        loop = s.circuit()

        self.play(
            camera.frame_all(self, [s.everything], pad=1.0, run_time=1.3),
            *s.reveal_labels(),
            run_time=1.3,
            rate_func=motion.FEATURE,
        )

        passes = 2
        words_per_pass = max(1, (self.answer.word_count - 3) // passes)
        for i in range(passes):
            # On the path BEFORE the comet is attached — see beat_stream.
            runner = Dot(radius=0.22, color=theme.TOKEN)
            runner.move_to(loop.point_from_proportion(0))
            # Short dissipation: at this speed a long tail stops reading as a
            # comet and starts reading as a line drawn through the machines,
            # and its straight per-frame chords cut the corners visibly.
            spark = effects.comet(
                runner, color=theme.TOKEN, width=9, dissipating_time=0.08
            )
            self.add(spark, runner)
            self.play(
                MoveAlongPath(runner, loop, run_time=LOOP_RUN_TIME),
                # Glow only — no scale pop. Animating a node's geometry means
                # animating a VGroup, which interpolates the group's own
                # transparent rgba onto its children and blanks every label in
                # the bay. The light alone reads as the machine reacting.
                LaggedStart(
                    *[
                        s.glow_for(node).animate.set_stroke(opacity=1.0)
                        for node in s.nodes
                    ],
                    lag_ratio=0.16,
                ),
                run_time=LOOP_RUN_TIME,
                rate_func=motion.MOVE,
            )
            self.remove(runner, spark)
            self.play(
                LaggedStart(
                    *[
                        s.glow_for(node).animate.set_stroke(opacity=s.resting_glow)
                        for node in s.nodes
                    ],
                    lag_ratio=0.1,
                ),
                self.answer.animate.reveal(3 + (i + 1) * words_per_pass),
                run_time=0.2,
                rate_func=motion.EXIT,
            )

        self.play(
            self.answer.animate.reveal(self.answer.word_count),
            run_time=0.3,
            rate_func=motion.ENTER,
        )
        self.wait(0.4)

    # --------------------------------------------------------------- helpers
    def _carry(self, target) -> list:
        """Animations moving the packet and everything stamped on it.

        The parcel is a plain list, not a ``VGroup``, and every member is
        shifted by the same delta. Animating a container ``VGroup``'s geometry
        interpolates the group's own rgba — transparent by default — onto its
        children, which dims or blanks everything inside it. That has cost this
        repo a session; a list and a shared delta costs nothing.
        """
        delta = np.array(target, dtype=float) - self.packet.get_center()
        return [member.animate.shift(delta) for member in self.parcel]

    def _chip(self, icon: str, name: str) -> VGroup:
        """A tiny icon+word badge — one of the things the orchestrator loads."""
        glyph = Glyph(icon, color=theme.ASSISTANT, height=0.24, stroke_width=2.0)
        label = typography.text(
            "micro", name, frame_width=W_SERVICE, color=theme.FG_MUTED
        )
        return VGroup(glyph, label).arrange(RIGHT, buff=theme.PAD_XS)

    @staticmethod
    def _meter(label: str, value_format: str, color, *, scale: float):
        """A quota-style meter: a ProbabilityBar with a different number format.

        Scaled up by the caller because ``lib/components/probability.py``
        predates ``lib/typography.py`` and still sizes its text in absolute
        theme points. At the widths this film uses, an unscaled bar's value
        text lands just under ``typography.MIN_READABLE``. Scaling the whole
        widget is the honest fix from a scene; moving probability.py onto the
        type system is a /lib change with twenty baselines behind it, and is
        noted in claude-progress.txt rather than smuggled in here.
        """
        bar = ProbabilityBar(
            label,
            0.0,
            max_value=1.0,
            bar_length=1.2,
            label_width=1.1,
            color=color,
            value_format=value_format,
        )
        return bar.scale(scale)

    def _note(self, station, text: str, shot: float, *, sub: str | None = None,
              tight: bool = False):
        """A caption under a station bay, sized for the shot it is read in.

        ``tight`` is for the four in-box bays: they are 0.6 apart, so a caption
        at the band stations' size and spacing would land on the next bay's top
        edge. The smaller role plus a smaller buff sits the line in the middle
        of that gap.
        """
        role = "micro" if tight else "caption"
        lines = VGroup(
            typography.text(role, text, frame_width=shot, color=theme.FG_MUTED)
        )
        if sub is not None:
            lines.add(
                typography.text("micro", sub, frame_width=shot, color=theme.FG_FAINT)
            )
            lines.arrange(DOWN, buff=theme.PAD_XS)
        for line in lines:
            if line.width > station.bay_width:
                line.scale(station.bay_width / line.width)
        lines.next_to(
            station.bay, DOWN, buff=0.16 if tight else theme.PAD_SM
        )
        return lines

    @staticmethod
    def _fit_in_window(bubble, chat) -> None:
        """Shrink ``bubble`` until the chat window can actually show it.

        The window has no clipping mask: a bubble too tall for the message area
        is either drawn straight through the composer and out of the frame, or
        scrolled far enough up that the window hides it. Either way the reply
        the whole film builds to is unreadable, so the bubble yields, not the
        window. Taken verbatim from the reference scene — this is a solved
        problem and re-solving it is how it comes back.
        """
        room = chat.message_area_height
        if bubble.height > room:
            bubble.scale(room / bubble.height)
