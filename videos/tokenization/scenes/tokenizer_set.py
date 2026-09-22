"""The tokenizer bench: every location the camera visits, built once.

Arc 0's set was a plant — a clockwise circuit, because a request travels. This
one is a **bench**, read left to right like a line of text, because this is one
machine doing one thing to one string. One drop-down spur underneath carries the
consequences.

::

       ┌─────────────────────┐
       │  THE VOCABULARY     │   (0, +9), tall — sits over the table that
       │  WALL  ~200,000     │                  built it
       └──────────┬──────────┘
                  │
     QUESTION ──> SPLIT ──> TABLE ──> IDS ──> DOOR
     (-26,+2)   (-13,+2)   (0,+3)   (+13,+2) (+24,+2)
                              │
                              v  consequence spur
                          THE METER
                           (0,-12)
                 price · context · latency
                  en 7 │ hi 32 │ my 72

All coordinates live in this module and nowhere else, and :meth:`TokenizerSet.
validate` re-derives the extents from the drawn mobjects rather than trusting
the numbers written here.

Separated from the choreography in ``scene_tokenization.py`` on purpose: a
60-second uncut take is ~70 animations whose timings depend on each other, and
interleaving the geometry with them gives you a scene nobody can re-time.
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, VGroup

from lib import effects, routing, theme, typography, utils
from lib.components.chat_ui import ChatWindow
from lib.components.factory import Conveyor, PipelineBox, Station
from lib.components.stacked import SegmentedBar

# NOT `props`: a video's `scenes/` directory goes on `sys.path` as a flat
# namespace when a deck or `manim render <path>` loads it, and
# `chatgpt_request_lifecycle/scenes/props.py` already owns that name. A
# same-named module in a second video silently resolves to whichever was
# imported first.
try:  # pragma: no cover - whichever branch runs, the other is unreachable
    from .tokenizer_props import CharacterRow, GhostCircuit, MergeTable, VocabWall
except ImportError:
    from tokenizer_props import (  # type: ignore[no-redef]
        CharacterRow,
        GhostCircuit,
        MergeTable,
        VocabWall,
    )


# ==========================================================================
# The verified numbers. ONE block, imported everywhere — see script.md.
# ==========================================================================
ENCODING = "o200k_base"  # the encoding this film names on screen
VOCAB_SIZE = 200_019  # captioned "≈ 200,000", never the precise figure
QUESTION = "How many r's in strawberry?"
WORD = "strawberry"

# verified against tiktoken's o200k_base: the encoding file was fetched from a
# third-party mirror and authenticated against the SHA-256 `expected_hash`
# hardcoded in tiktoken_ext/openai_public.py. Provenance in script.md.
SENTENCE_TOKENS = ["How", " many", " r", "'s", " in", " strawberry", "?"]
SENTENCE_IDS = [5299, 1991, 428, 885, 306, 101830, 30]

# The three-piece split exists only for the BARE word, with no leading space.
# In the sentence above, " strawberry" is a single vocabulary entry (101830).
WORD_TOKENS = ["st", "raw", "berry"]
WORD_IDS = [302, 1618, 19772]

#: How the vocabulary counter is drawn. Derived from VOCAB_SIZE rather than
#: typed, so the number on screen and the constant cannot drift apart.
VOCAB_CAPTION = f"≈ {round(VOCAB_SIZE, -4):,}"

# Sanity, at import time rather than in a render three minutes later.
assert len(SENTENCE_TOKENS) == len(SENTENCE_IDS) == 7
assert "".join(SENTENCE_TOKENS) == QUESTION
assert "".join(WORD_TOKENS) == WORD
assert " " + WORD in SENTENCE_TOKENS
assert len(WORD_TOKENS) == len(WORD_IDS) == 3


# ==========================================================================
# Shot widths. Declared once; every label states which shot it belongs to.
# ==========================================================================
SHOT_CHAT = 13.0  # B0
SHOT_BENCH = 15.0  # B1, B2
SHOT_TIGHT = 12.0  # B3, B4 entry
SHOT_IDS = 14.0  # B4
SHOT_METER = 18.0  # B5
SHOT_WIDE = 60.0  # B6

#: Padding the closing pull-back passes to ``camera.frame_all``. Kept here so
#: :meth:`TokenizerSet.wide_frame_width` predicts the same shot the scene takes.
WIDE_PAD = 1.2

#: Largest tolerated drift between ``SHOT_WIDE`` and the width the pull-back
#: actually needs. Wide-shot type is sized against SHOT_WIDE, so letting the
#: two drift apart is what makes labels come out the wrong size.
WIDE_DRIFT = 0.12


# ==========================================================================
# World anchors
# ==========================================================================
BENCH_Y = 2.0

CHAT_POS = np.array([-26.0, BENCH_Y, 0.0])
CHAT_W, CHAT_H = 9.6, 6.0

SPLIT_POS = np.array([-13.0, BENCH_Y, 0.0])
SPLIT_W, SPLIT_H = 11.0, 4.2

TABLE_POS = np.array([0.0, 3.0, 0.0])
TABLE_W, TABLE_H = 10.0, 4.6

IDS_POS = np.array([13.0, BENCH_Y, 0.0])
IDS_W, IDS_H = 11.0, 4.2

#: The DOOR is a PipelineBox whose LEFT WALL is the model boundary. The box
#: itself runs off to the right; only its left wall and the slot in it are ever
#: framed, which is the whole point — what is past the wall is not this film.
DOOR_INNER = np.array([26.0, 1.6, 0.0])
DOOR_INNER_W, DOOR_INNER_H = 4.6, 2.2
DOOR_PAD = 1.4

VOCAB_POS = np.array([0.0, 9.0, 0.0])
VOCAB_W, VOCAB_H = 3.6, 4.6

METER_POS = np.array([0.0, -12.0, 0.0])
METER_W, METER_H = 14.0, 7.0

#: Where the character row of B1 lies: on the bench, above the SPLIT bay, in
#: the space the chips will later occupy. The row is wider than the bay, which
#: is why B2's collapse reads as the letters being swallowed by the machine.
ROW_Y = 5.6
ROW_COUNTER_Y = 6.6

#: The bars of B5. Deliberately scaled so the Burmese bar OVERRUNS the frame
#: edge at SHOT_METER — that is the point of the beat, not a layout bug.
BAR_UNIT = 0.23
BAR_X0 = -4.6
BAR_YS = (-13.4, -14.1, -14.8)
COUNTER_X = -6.2
#: Clear of the bay's own header. A top header on a 7-unit bay lands around
#: y = -9.3, and counters at -10.1 drew straight through the words.
COUNTER_YS = (-10.9, -11.8, -12.7)

#: B3's ramp out of legibility. Declared here with the rest of the film's
#: copy so the scene and the prop cannot disagree about how many steps it has.
#: `merge 50,000` is illustrative and says so on screen.
RAMP_LABELS = [
    "merge 4",
    "merge 60",
    "merge 2,400",
    "merge 50,000 · illustrative",
]

#: The closing gesture. The bench scales by this much and moves into the ghost
#: circuit's TOKENIZER node; the camera does not move.
#: Brief said ~0.11; the ghost circuit is height-bound by the wide frame (see
#: props.GhostCircuit), so the node it has to fit inside is smaller than that
#: assumed. The factor is derived from the node rather than typed — see
#: :meth:`bench_shrink`.
GHOST_CENTER = np.array([10.0, -1.0, 0.0])


class TokenizerSet(VGroup):
    """Every mobject in the film, positioned. Built once, never torn down."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # -- QUESTION: the cold open ----------------------------------------
        self.chat = ChatWindow(width=CHAT_W, height=CHAT_H, title="ChatGPT")
        self.chat.move_to(CHAT_POS)
        # A chat window is not a Station, so it carries its own wide-shot name.
        self.question_marquee = self._marquee("QUESTION", theme.USER, CHAT_W * 0.95)
        self.question_marquee.move_to(CHAT_POS)

        # -- SPLIT: the chips ------------------------------------------------
        self.split = Station(
            "Split",
            subtitle="text -> pieces",
            width=SPLIT_W,
            height=SPLIT_H,
            accent=theme.TOKEN,
            icon="binary",
            # Top header, not left: the seven chips need the bay's full width,
            # and a left-hand header caps the slot at 36% of it (HEADER_SHARE),
            # which fits the row at a size nobody can read.
            header_side="top",
            shot_width=SHOT_BENCH,
            wide_label="SPLIT",
            wide_width=SHOT_WIDE,
        )
        self.split.shift(SPLIT_POS - self.split.bay.get_center())

        # -- TABLE: the worked merges ----------------------------------------
        self.table = Station(
            "The table",
            subtitle="merges, in order",
            width=TABLE_W,
            height=TABLE_H,
            accent=theme.ATTENTION,
            icon="layers",
            header_side="left",
            shot_width=SHOT_TIGHT,
            wide_label="TABLE",
            wide_width=SHOT_WIDE,
        )
        self.table.shift(TABLE_POS - self.table.bay.get_center())

        # -- IDS: the integers -----------------------------------------------
        self.ids = Station(
            "The ids",
            subtitle="pieces -> integers",
            width=IDS_W,
            height=IDS_H,
            accent=theme.EMBED,
            icon="hash",
            header_side="top",
            shot_width=SHOT_IDS,
            wide_label="IDS",
            wide_width=SHOT_WIDE,
        )
        self.ids.shift(IDS_POS - self.ids.bay.get_center())

        # -- DOOR: the model boundary ----------------------------------------
        from manim import Rectangle

        door_inner = Rectangle(
            width=DOOR_INNER_W, height=DOOR_INNER_H, stroke_width=0, fill_opacity=0.0
        ).move_to(DOOR_INNER)
        self.door = PipelineBox(
            [door_inner],
            title="THE MODEL",
            accent=theme.ASSISTANT,
            pad=DOOR_PAD,
            title_role="heading",
            title_side="top",
            wide_width=SHOT_WIDE,
        )
        #: Past the wall there is no text anywhere — only vectors. Pre-built,
        #: hidden; B4 fades them in.
        self.door_vectors = self._vectors(DOOR_INNER)

        # -- VOCAB_WALL: the dense column ------------------------------------
        self.vocab = VocabWall(
            width=VOCAB_W,
            height=VOCAB_H,
            caption=VOCAB_CAPTION,
            shot_width=SHOT_TIGHT,
            accent=theme.ATTENTION,
        )
        self.vocab.move_to(VOCAB_POS)
        # The cells and the readout arrive in B3, so they are DETACHED from the
        # wall group rather than hidden with `set_opacity(0)`. FadeIn fades a
        # mobject to the opacity it already carries, so a prop parked at zero
        # fades in to nothing — the bug this whole pattern exists to avoid.
        self.vocab.remove(self.vocab.cells, self.vocab.readout)
        # move_to centred the WHOLE prop, readout included, which left the wall
        # itself sitting off the spur that feeds it. Re-anchor on the frame.
        recentre = VOCAB_POS - self.vocab.frame.get_center()
        for part in (self.vocab, self.vocab.cells, self.vocab.readout):
            part.shift(recentre)
        self.vocab_marquee = self._marquee(
            "VOCABULARY", theme.ATTENTION, VOCAB_W * 2.6
        )
        self.vocab_marquee.move_to(VOCAB_POS)

        # -- METER: the consequences -----------------------------------------
        self.meter = Station(
            "The meter",
            subtitle="price · context · latency",
            width=METER_W,
            height=METER_H,
            accent=theme.WARN,
            icon="gauge",
            header_side="top",
            shot_width=SHOT_METER,
            wide_label="METER",
            wide_width=SHOT_WIDE,
        )
        self.meter.shift(METER_POS - self.meter.bay.get_center())

        # -- rails, all drawn, all orthogonal --------------------------------
        self.rail_question_split = Conveyor(
            [
                self.chat.get_right() + RIGHT * theme.PAD_MD,
                self.split.bay.get_left() + LEFT * theme.PAD_MD,
            ],
            chevrons=2,
        )
        self.rail_split_table = Conveyor(
            self._step(
                self.split.bay.get_right() + RIGHT * theme.PAD_MD,
                self.table.bay.get_left() + LEFT * theme.PAD_MD,
            ),
            chevrons=1,
        )
        self.rail_table_ids = Conveyor(
            self._step(
                self.table.bay.get_right() + RIGHT * theme.PAD_MD,
                self.ids.bay.get_left() + LEFT * theme.PAD_MD,
            ),
            chevrons=1,
        )
        self.rail_ids_door = Conveyor(
            [
                self.ids.bay.get_right() + RIGHT * theme.PAD_MD,
                self.door.frame.get_left() + LEFT * theme.PAD_MD,
            ],
            chevrons=2,
        )
        self.rail_table_vocab = Conveyor(
            [
                self.table.bay.get_top() + UP * 0.05,
                self.vocab.get_bottom() + DOWN * 0.05,
            ],
            color=theme.ATTENTION,
            chevrons=1,
        )
        self.rail_table_meter = Conveyor(
            [
                self.table.bay.get_bottom() + DOWN * 0.05,
                self.meter.bay.get_top() + UP * 0.05,
            ],
            color=theme.WARN,
            chevrons=2,
        )

        #: The slot the row of integers passes through. A narrow gap in the
        #: model wall, drawn so the pass-through has something to pass through.
        self.door_slot = self._slot(self.door.frame.get_left()[0], BENCH_Y)

        # -- B1's character row ----------------------------------------------
        self.row = CharacterRow(
            QUESTION,
            width=12.4,
            shot_width=SHOT_BENCH,
            highlight_word=WORD,
        )
        self.row.move_to(np.array([SPLIT_POS[0], ROW_Y, 0.0]))
        self.row_counter = typography.text(
            "label",
            f'r in "{WORD}" — {WORD.count("r")}',
            frame_width=SHOT_BENCH,
            color=theme.WARN,
            mono=True,
        )
        self.row_counter.move_to(np.array([SPLIT_POS[0], ROW_COUNTER_Y, 0.0]))

        # -- B3's merge table -------------------------------------------------
        self.merges = MergeTable(
            ["low", "lower", "newest"],
            [("l", "o"), ("lo", "w"), ("e", "s")],
            RAMP_LABELS,
            shot_width=SHOT_TIGHT,
        )
        self.table.fit(self.merges)
        self.merges.detach_staged()

        # -- B5's counters and bars ------------------------------------------
        self.price, self.context, self.latency = self._counters()
        self.bars, self.bar_labels = self._bars()

        # -- B6's ghost circuit ----------------------------------------------
        self.ghost = GhostCircuit(
            labelled="TOKENIZER", shot_width=SHOT_WIDE, accent=theme.TOKEN
        )
        self.ghost.move_to(GHOST_CENTER)

        # -- glow halos, pre-built and invisible ------------------------------
        # Lighting a bay is the house cue for "this is running", so the
        # choreography only ever animates an opacity. Stroke only: set_opacity
        # on a halo raises the copies' FILL and they become opaque plates.
        self._glows: dict[int, VGroup] = {}
        halos = VGroup()
        for station in self.stations:
            halo = effects.glow(station.bay, station.accent)
            halo.set_stroke(opacity=0.0)
            self._glows[id(station)] = halo
            halos.add(halo)
        self.halos = halos

        #: Wide-shot labels stay dark until the pull-back — at a close-up they
        #: are several times the size of anything else on screen.
        self.wide_labels = VGroup(
            self.door.caption, self.question_marquee, self.vocab_marquee
        )
        self.wide_labels.set_opacity(0.0)

        #: Residual glow left on a bay the camera has moved past.
        self.resting_glow = 0.18

        # ONLY the standing set goes in the group. Everything a beat brings
        # in (the character row, the merge table, the wall cells, the counters,
        # the bars, the ghost circuit) stays detached until its own FadeIn, so
        # nothing has to be parked at zero opacity to stay out of frame one.
        self.add(
            halos,
            self.rail_question_split,
            self.rail_split_table,
            self.rail_table_ids,
            self.rail_ids_door,
            self.rail_table_vocab,
            self.rail_table_meter,
            self.door,
            self.door_slot,
            self.chat,
            self.question_marquee,
            self.split,
            self.table,
            self.ids,
            self.vocab,
            self.vocab_marquee,
            self.meter,
        )

        #: The props each beat stages, in beat order. Not in the group above —
        #: see the comment there — but listed so the scene has one place to
        #: address them from and `validate` can reason about the whole film.
        self.staged = VGroup(
            self.row,
            self.row_counter,
            self.vocab.cells,
            self.vocab.readout,
            self.merges,
            self.door_vectors,
            self.price,
            self.context,
            self.latency,
            self.bars,
            self.bar_labels,
        )

        self.validate()

    # --------------------------------------------------------------- pieces
    @staticmethod
    def _step(start, end, *, rise_at: float = 0.5):
        """Orthogonal three-segment rail between two points at different heights.

        ``routing.elbow`` turns one corner; the bench needs two, so the rise
        happens midway and both ends leave their bay horizontally. Diagonals
        read as sloppy in a diagram style, which is the whole reason this is
        not a straight line.
        """
        start = np.array(start, dtype=float)
        end = np.array(end, dtype=float)
        if abs(start[1] - end[1]) < 1e-6:
            return [start, end]
        mid_x = start[0] + (end[0] - start[0]) * rise_at
        return [
            start,
            np.array([mid_x, start[1], 0.0]),
            np.array([mid_x, end[1], 0.0]),
            end,
        ]

    def _marquee(self, label: str, accent, limit: float | None = None):
        """A wide-shot name for a bay that is not a ``Station``.

        Sized at the same role Station uses for its own ``wide_label``, so the
        pull-back does not come out with two sizes of bay name.
        """
        text = typography.text(
            "heading", label, frame_width=SHOT_WIDE, color=accent, bold=True
        )
        if limit is not None:
            utils.fit_text(text, limit)
        return text

    @staticmethod
    def _slot(x: float, y: float):
        """The gap in the model wall. Two stubs with a hole between them."""
        from manim import Line

        gap = 0.55
        return VGroup(
            Line(
                np.array([x, y + gap, 0.0]),
                np.array([x, y + gap + 0.9, 0.0]),
                stroke_color=theme.BG,
                stroke_width=theme.STROKE_THICK * 2,
            ),
            Line(
                np.array([x, y - gap - 0.9, 0.0]),
                np.array([x, y - gap, 0.0]),
                stroke_color=theme.BG,
                stroke_width=theme.STROKE_THICK * 2,
            ),
        )

    @staticmethod
    def _vectors(center):
        """Vectors only, no text. What the far side of the wall looks like."""
        from manim import Arrow

        group = VGroup()
        for i in range(4):
            for j in range(3):
                start = center + np.array([-1.5 + i * 1.0, 0.7 - j * 0.7, 0.0])
                angle = 0.5 + 0.7 * ((i * 3 + j) % 5)
                tip = start + np.array(
                    [0.45 * np.cos(angle), 0.45 * np.sin(angle), 0.0]
                )
                group.add(
                    Arrow(
                        start,
                        tip,
                        buff=0.0,
                        stroke_width=theme.STROKE_NORMAL,
                        color=theme.EMBED,
                        max_tip_length_to_length_ratio=0.35,
                    )
                )
        return group

    def _counters(self):
        """B5's three counters: price, context, latency.

        The price row carries the UNIT and no figures, deliberately — real
        prices date the film within weeks. The context bar's 128,000 is
        illustrative and says so on screen.
        """
        price = typography.text(
            "label",
            "price     $ / 1M tokens   in · out",
            frame_width=SHOT_METER,
            color=theme.FG,
            mono=True,
        )
        price.move_to(np.array([COUNTER_X, COUNTER_YS[0], 0.0]), aligned_edge=LEFT)

        bar = SegmentedBar(
            {"used": 38, "free": 62},
            length=3.0,
            thickness=0.26,
            colors=[theme.WARN, theme.FG_FAINT],
            labels="none",
            frame_width=SHOT_METER,
        )
        words = typography.text(
            "label",
            "context",
            frame_width=SHOT_METER,
            color=theme.FG,
            mono=True,
        )
        tail = typography.text(
            "label",
            "/ 128,000  illustrative",
            frame_width=SHOT_METER,
            color=theme.FG_MUTED,
            mono=True,
        )
        context = VGroup(words, bar, tail).arrange(RIGHT, buff=theme.PAD_MD)
        context.move_to(np.array([COUNTER_X, COUNTER_YS[1], 0.0]), aligned_edge=LEFT)

        latency = typography.text(
            "label",
            "latency   prefill ∝ in · decode ∝ out",
            frame_width=SHOT_METER,
            color=theme.FG,
            mono=True,
        )
        latency.move_to(np.array([COUNTER_X, COUNTER_YS[2], 0.0]), aligned_edge=LEFT)

        return price, context, latency

    def _bars(self):
        """Three language bars, drawn at zero width and grown by the beat.

        The lengths are a fixed number of world units per token, so the ratio
        on screen is the ratio in the figures — and the Burmese bar therefore
        leaves the frame, which is the beat's whole argument.
        """
        from manim import Rectangle

        bars = VGroup()
        labels = VGroup()
        for i, (name, count, color) in enumerate(
            [
                ("en", 7, theme.ASSISTANT),
                ("hi", 32, theme.TOKEN),
                ("my", 72, theme.ERROR),
            ]
        ):
            full = count * BAR_UNIT
            rect = Rectangle(
                width=full,
                height=0.42,
                fill_color=color,
                fill_opacity=1.0,
                stroke_width=0,
            )
            rect.move_to(np.array([BAR_X0, BAR_YS[i], 0.0]), aligned_edge=LEFT)
            rect.full_width = full
            rect.stretch_to_fit_width(1e-3)
            rect.move_to(np.array([BAR_X0, BAR_YS[i], 0.0]), aligned_edge=LEFT)
            bars.add(rect)

            label = typography.text(
                "label",
                f"{name} {count}",
                frame_width=SHOT_METER,
                color=color,
                mono=True,
            )
            label.move_to(
                np.array([COUNTER_X, BAR_YS[i], 0.0]), aligned_edge=LEFT
            )
            labels.add(label)
        return bars, labels

    # ------------------------------------------------------------ geometry
    @property
    def stations(self) -> list:
        return [self.split, self.table, self.ids, self.meter]

    @property
    def everything(self) -> VGroup:
        """What the closing pull-back has to frame."""
        return VGroup(
            self.chat,
            self.split,
            self.table,
            self.vocab,
            self.ids,
            self.door,
            self.meter,
            self.bars,
            self.rail_table_meter,
        )

    def wide_frame_width(self, pad: float = WIDE_PAD) -> float:
        """Camera width the pull-back needs, predicted the way it is taken."""
        group = self.everything
        return max(
            group.width + 2 * pad, (group.height + 2 * pad) * typography.ASPECT
        )

    def bench_shrink(self) -> float:
        """Scale factor that puts the whole bench inside the TOKENIZER node.

        Derived, not typed: the node is a circle, so what has to fit is the
        bench's half-diagonal against the node's radius. A future layout change
        moves this number rather than silently hanging the bench outside.
        """
        group = self.everything
        half_diagonal = float(np.hypot(group.width, group.height)) / 2
        return float(self.ghost.node_radius * 0.80 / half_diagonal)

    def bench_target_center(self) -> np.ndarray:
        return self.ghost.labelled_node.get_center()

    # ------------------------------------------------------------ the run
    def bench_run(self):
        """QUESTION -> SPLIT -> TABLE -> IDS -> DOOR, from the DRAWN rails.

        Built by joining the rails the viewer can see, never from bay centres —
        that is how a payload ended up flying through solid boxes in an earlier
        film in this repo.
        """
        return routing.join(
            self.rail_question_split,
            [self.split.bay.get_left(), self.split.bay.get_right()],
            self.rail_split_table,
            [self.table.bay.get_left(), self.table.bay.get_right()],
            self.rail_table_ids,
            [self.ids.bay.get_left(), self.ids.bay.get_right()],
            self.rail_ids_door,
        )

    def meter_spur(self):
        return routing.join(self.rail_table_meter)

    def ids_to_door(self):
        """The stretch B4's row of integers actually travels."""
        return routing.join(
            [self.ids.bay.get_right(), self.rail_ids_door.start],
            self.rail_ids_door,
        )

    def glow_for(self, station) -> VGroup:
        try:
            return self._glows[id(station)]
        except KeyError:
            raise KeyError(f"no glow halo built for {station}") from None

    def reveal_labels(self, opacity: float = 1.0):
        """Animations bringing every wide-shot label up for the pull-back."""
        anims = [self.wide_labels.animate.set_opacity(opacity)]
        for station in self.stations:
            anims.extend(station.reveal_wide(opacity))
        return anims

    # ---------------------------------------------------------- validation
    def validate(self) -> None:
        """Assert the geometry the choreography depends on.

        Called at construction, so a layout mistake fails here rather than in a
        render three minutes later — or, worse, in a shipped video.
        """
        # The bench run must stay clear of the two bays it is NOT on. It is
        # meant to pass THROUGH split/table/ids — a bench is read left to
        # right — so those are not obstacles; the spur's destinations are.
        run_obstacles = [
            ("the vocabulary wall", self.vocab),
            ("the meter bay", self.meter.bay),
        ]
        routing.assert_path_clears(self.bench_run(), run_obstacles, ignore_ends=0.02)

        # The spur drops straight down the middle and must not clip a bay.
        spur_obstacles = [
            ("the chat window", self.chat),
            ("the split bay", self.split.bay),
            ("the ids bay", self.ids.bay),
            ("the model wall", self.door.frame),
            ("the vocabulary wall", self.vocab),
        ]
        routing.assert_path_clears(self.meter_spur(), spur_obstacles, ignore_ends=0.05)

        actual = self.wide_frame_width()
        drift = abs(actual - SHOT_WIDE) / SHOT_WIDE
        if drift > WIDE_DRIFT:
            raise AssertionError(
                f"SHOT_WIDE is {SHOT_WIDE:.1f} but the pull-back actually needs "
                f"{actual:.1f} ({drift:.1%} drift). Wide-shot type is sized "
                "against SHOT_WIDE, so letting the two drift apart is exactly "
                "what makes labels come out the wrong size."
            )

        # The closing gesture: the bench has to end up INSIDE the node, not
        # merely near it. Checked here because the frame review cannot be run
        # by a test, and this is the arithmetic behind it.
        shrunk = self.bench_shrink()
        half_diagonal = (
            float(np.hypot(self.everything.width, self.everything.height)) / 2
        )
        if shrunk * half_diagonal > self.ghost.node_radius:
            raise AssertionError(
                "the shrunken bench does not fit inside the TOKENIZER node"
            )

        # The character row is derived from the question, never typed.
        assert len(self.row.cells) == len(QUESTION) == 27, (
            f"the character row has {len(self.row.cells)} cells for a "
            f"{len(QUESTION)}-character question"
        )
        assert self.row.r_count_in(WORD) == WORD.count("r") == 3, (
            "the r counter and the cells it counts have drifted apart"
        )


__all__ = [
    "TokenizerSet",
    "ENCODING",
    "VOCAB_SIZE",
    "VOCAB_CAPTION",
    "QUESTION",
    "WORD",
    "SENTENCE_TOKENS",
    "SENTENCE_IDS",
    "WORD_TOKENS",
    "WORD_IDS",
    "SHOT_CHAT",
    "SHOT_BENCH",
    "SHOT_TIGHT",
    "SHOT_IDS",
    "SHOT_METER",
    "SHOT_WIDE",
    "WIDE_PAD",
    "COUNTER_X",
    "COUNTER_YS",
    "RAMP_LABELS",
]
