"""The tokenizer set: every location the camera visits, built once.

Split from the choreography in `scene_tokenization.py` for the reason the house
format always splits them — *where things are* and *when the camera goes there*
are separate concerns, and a 59-second uncut take is ~75 animations whose
timings all depend on each other. Every coordinate in this film lives in this
module and nowhere else.

Arc 0's set was a plant: a clockwise circuit, because a request travels. This
one is a **bench**, read left to right like a line of text, because this is one
machine doing one thing to one string. One drop-down spur underneath carries the
consequences.

```
                     ┌─────────────────────┐
                     │  THE VOCABULARY     │   (0, +9)
                     │  WALL   ≈ 200,000   │   sits over the table that built it
                     └──────────┬──────────┘
                                │
 QUESTION ──▶ SPLIT ──▶      TABLE      ──▶ IDS ──▶ DOOR
 (−26,+2)   (−13,+2)         (0,+3)        (+13,+2) (+24,+2)
                                │
                                ▼  consequence spur
                            THE METER
                             (0,−12)
                    price · context · latency
                     en 7 │ hi 32 │ my 72
```

Three things about this shape are decisions, not accidents:

* **It is a straight line.** The film's claim is that one string goes in one end
  and a row of integers comes out the other, and a bench says that before a word
  is spoken. A circuit would say the text comes back, which it never does.
* **The wall sits directly above the table**, sharing the `ATTENTION` accent.
  That repeat is the one intended one in the set: it is what says *the wall is
  the output of the table*. Every other accent repeat in this set is between
  bays that are never on screen together.
* **`ASSISTANT` on the `DOOR` and `TOKEN` on the `SPLIT` are exactly Arc 0's
  inference-stack accents, in the same roles.** A returning viewer should
  recognise the chips in beat 2 as the same chips that flew past in four seconds
  of the last film, now slowed down enough to read. Do not change them, and do
  not change `chatgpt_request_lifecycle` to match anything here.
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, FadeIn, VGroup

from lib import effects, routing, theme, typography
from lib.components.chat_ui import ChatWindow
from lib.components.factory import Conveyor, PipelineBox, Station
from lib.components.tokens import TokenStrip
from lib.components.vectors import EmbeddingGrid

# Two import routes, and the second one needs care. The Evaluator imports this
# as `videos.tokenization.scenes.tokenizer_set`, where the relative import is
# right. `manim render <path>` and `videos/<slug>/slides.py` instead put the
# video's `scenes/` directory on a FLAT `sys.path` — and every video in this repo
# has a `scenes/props.py`, so whichever one is imported first wins the name
# `props` for the whole process. `tests/test_slides_convention.py` builds all
# three films in one pytest session, so a bare `import props` here resolves to
# `chatgpt_request_lifecycle`'s and this module fails with a name error about a
# class it can see on disk. Loading THIS file's props by location under a unique
# module name is what makes both routes agree.
try:  # pragma: no cover - one branch is always unreachable
    from .props import CharacterRow, GhostCircuit, MergeTable, VocabWall
except ImportError:  # pragma: no cover
    import importlib.util as _ilu
    import pathlib as _pathlib

    _spec = _ilu.spec_from_file_location(
        "tokenization_props", _pathlib.Path(__file__).with_name("props.py")
    )
    _props = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_props)
    CharacterRow = _props.CharacterRow
    GhostCircuit = _props.GhostCircuit
    MergeTable = _props.MergeTable
    VocabWall = _props.VocabWall

# --- the string this whole film is about -----------------------------------
#: Verified against `o200k_base` in a pre-flight; the ids are baked in as
#: literals so the render needs neither network access nor `tiktoken`.
QUESTION = "How many r's in strawberry?"
TOKENS = ["How", " many", " r", "'s", " in", " strawberry", "?"]
IDS = [5299, 1991, 428, 885, 306, 101830, 30]
#: `strawberry` tokenized STANDALONE — ids 302, 1618, 19772. With its leading
#: space it is one token, id 101830; that difference is beat 2.
SPLIT_PIECES = ["st", "raw", "berry"]
WORD = "strawberry"
WORD_SPAN = (QUESTION.index(WORD), QUESTION.index(WORD) + len(WORD))

# --- shot sizes this set is designed for ------------------------------------
SHOT_CHAT = 13.0    # B0
SHOT_BENCH = 15.0   # B1, B2
SHOT_TIGHT = 12.0   # B3, B4 entry
SHOT_IDS = 14.0     # B4
SHOT_METER = 18.0   # B5
SHOT_WIDE = 60.0    # B6

# --- world anchors ----------------------------------------------------------
BENCH_Y = 2.0
QUESTION_POS = (-26.0, BENCH_Y)
SPLIT_POS = (-13.0, BENCH_Y)
TABLE_POS = (0.0, 3.0)
WALL_POS = (0.0, 8.6)
IDS_POS = (13.0, BENCH_Y)
DOOR_POS = (24.0, BENCH_Y)
METER_POS = (0.0, -12.0)

CHAT_W, CHAT_H = 9.6, 6.0
#: Where the camera sits for beat 0. NOT the chat's own centre: at SHOT_CHAT the
#: frame is 7.3 tall against a 6.0-tall window, and the beat's caption has to fit
#: UNDER the window. Centring on the window leaves 0.16 of a unit down there and
#: the caption is cropped — so the frame is dropped just far enough to open that
#: gap while keeping the window's title bar inside the top edge.
CHAT_SHOT_CENTRE = (-26.0, 1.45)
#: Wide and short, so both chip bays take a top header — there is vertical room
#: for one here, and a left header (which a 2.8-tall Arc 0 band bay needs) would
#: eat 36% of the width the seven chips have to fit across.
CHIP_BAY_W, CHIP_BAY_H = 11.0, 3.6
TABLE_W, TABLE_H = 10.0, 5.0
METER_W, METER_H = 14.0, 5.0

#: The character row spans the bench rather than sitting in a bay: 27 cells at a
#: legible size is 13 units wide, wider than any bay in this set. It rides above
#: the SPLIT bay, which is where beat 2 then collapses it to.
ROW_WIDTH = 13.2
ROW_Y = 5.6

#: How much of the frame the enlarged ` strawberry` chip fills in beat 2.
BIG_CHIP_SHARE = 0.34


class TokenizerSet(VGroup):
    """Every mobject in the film, positioned. Built once, never torn down."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # -- the bays ---------------------------------------------------------
        self.chat = ChatWindow(width=CHAT_W, height=CHAT_H, title="ChatGPT")
        self.chat.move_to(np.array([*QUESTION_POS, 0.0]))
        #: Present in the very first frame. The film opens on a question that
        #: has already been asked; beat 0 is the answer arriving beside it.
        self.question_bubble = self.chat.add_message(QUESTION, "user")

        def bench_station(title, subtitle, accent, icon, *, w, h, shot):
            return Station(
                title,
                subtitle=subtitle,
                width=w,
                height=h,
                accent=accent,
                icon=icon,
                header_side="top",
                shot_width=shot,
                wide_label=title,
                wide_width=SHOT_WIDE,
            )

        self.split = bench_station(
            "Split", "one string → pieces", theme.TOKEN, "binary",
            w=CHIP_BAY_W, h=CHIP_BAY_H, shot=SHOT_BENCH,
        )
        self.table = bench_station(
            "Merge table", "pairs, by frequency", theme.ATTENTION, "layers",
            w=TABLE_W, h=TABLE_H, shot=SHOT_TIGHT,
        )
        self.ids = bench_station(
            "Ids", "pieces → integers", theme.EMBED, "hash",
            w=CHIP_BAY_W, h=CHIP_BAY_H, shot=SHOT_IDS,
        )
        self.meter = bench_station(
            "What it costs", "price · context · latency", theme.WARN, "gauge",
            w=METER_W, h=METER_H, shot=SHOT_METER,
        )
        self.stations = [self.split, self.table, self.ids, self.meter]

        for station, (x, y) in (
            (self.split, SPLIT_POS),
            (self.table, TABLE_POS),
            (self.ids, IDS_POS),
            (self.meter, METER_POS),
        ):
            station.shift(np.array([x, y, 0.0]) - station.bay.get_center())

        # -- the vocabulary wall, over the table that built it -----------------
        # 14 rows, not more: the wall, its counter AND its caption all have to
        # fit the SHOT_TIGHT frame at once, and the counter goes ABOVE the cells
        # so neither it nor the caption lands on the rail that runs down the
        # wall's midline into the table.
        self.vocab = VocabWall(frame_width=SHOT_TIGHT, rows=14)
        self.vocab.shift(np.array([*WALL_POS, 0.0]) - self.vocab.wall.get_center())
        # The counter and the sample pieces arrive in beat 3, so they are
        # detached from the wall group and re-added by the scene.
        self.vocab.counter.next_to(self.vocab.cells, UP, buff=theme.PAD_MD)
        self.vocab.remove(self.vocab.cells, self.vocab.samples, self.vocab.counter)

        # -- the model boundary ------------------------------------------------
        # What is on the far side of it: vectors, and no text anywhere. Built
        # here so the box sizes itself around its real contents rather than
        # around a placeholder that a later edit would have to keep in step.
        self.vectors = EmbeddingGrid(
            [
                [((r * 5 + c * 3) % 9) / 8.0 for c in range(7)]
                for r in range(5)
            ],
            cell=0.5,
            gap=0.06,
        )
        self.door = PipelineBox(
            [self.vectors],
            title="THE MODEL",
            accent=theme.ASSISTANT,
            pad=1.2,
            title_role="heading",
            wide_width=SHOT_WIDE,
        )
        self.door.shift(np.array([*DOOR_POS, 0.0]) - self.door.frame.get_center())
        # `PipelineBox` sizes its title for the PULL-BACK and hangs it above the
        # frame, which at SHOT_IDS is 1.8 units of cap height sitting outside the
        # top of the shot — the beat-4 close-up cropped it in half. So the box
        # carries a close-up name of its own, inside its top edge, and the big
        # one joins `wide_labels` and stays dark until 51s. Exactly the
        # cross-fade every Station does for itself.
        self.door_label = typography.text(
            "heading", "the model", frame_width=SHOT_IDS,
            color=theme.ASSISTANT, bold=True,
        )
        self.door_label.next_to(self.door.frame.get_top(), DOWN, buff=theme.PAD_MD)
        # The grid rides with the box. Deliberately NOT added to `self`: it is
        # brought in by `FadeIn` in beat 4, and `FadeIn` restores a mobject to
        # the opacity it already has — so anything that arrives later is built
        # here, positioned here, and left out of the scene graph until its beat.
        self.vectors.move_to(self.door.frame.get_center())

        # -- the payload: ONE strip, built once, ids and all -------------------
        # Assertion 2 of the brief: the chips and the ids are one list. This
        # object is built here, shown in the SPLIT bay in beat 2, and flipped to
        # its integers in beat 4. There is no second list anywhere.
        self.strip = TokenStrip(
            TOKENS,
            token_ids=IDS,
            show_ids=False,
            color=theme.TOKEN,
            font_size=typography.size_for("label", SHOT_BENCH),
        )
        # Positioned at the IDS bay FIRST, so the integer faces can be built at
        # the chip centres they will occupy, and then moved back to the SPLIT
        # bay where the film actually starts it. The scene shifts it right by
        # `strip_travel` during beat 3.
        self.strip.move_to(self.ids.slot_center)
        self.id_faces = VGroup(
            *[
                typography.text(
                    "body", str(tid), frame_width=SHOT_IDS,
                    color=theme.FG, mono=True,
                )
                for tid in IDS
            ]
        )
        for face, chip in zip(self.id_faces, self.strip.chips):
            if face.width > chip.box.width * 0.86:
                face.scale(chip.box.width * 0.86 / face.width)
            face.move_to(chip.box.get_center())
        #: The one chip the film is about gets TWO halos, because it is lit in
        #: two places twenty-six units apart and a halo is a set of copies of the
        #: shape at the position it was built at — it does not follow.
        self.word_chip = self.strip.chips[TOKENS.index(" " + WORD)]
        self.id_glow = effects.glow(self.word_chip.box, theme.EMBED)
        self.id_glow.set_stroke(opacity=0.0)
        self.strip_travel = np.array(self.split.slot_center) - np.array(
            self.ids.slot_center
        )
        self.strip.shift(self.strip_travel)

        # -- the character row -------------------------------------------------
        self.row = CharacterRow(
            QUESTION,
            frame_width=SHOT_BENCH,
            width=ROW_WIDTH,
            highlight_span=WORD_SPAN,
        )
        self.row.move_to(np.array([SPLIT_POS[0], ROW_Y, 0.0]))
        self.row_counter = typography.text(
            "heading", "3", frame_width=SHOT_BENCH, color=theme.WARN, bold=True
        )
        self.row_counter.next_to(self.row, UP, buff=theme.PAD_SM)

        # -- the merge table's contents ---------------------------------------
        self.merges = MergeTable(frame_width=SHOT_TIGHT)
        self.table.fit(self.merges)

        # -- rails -------------------------------------------------------------
        # Built from the SHAPES (`bay`, `frame`, `wall`), never from the groups:
        # a group's bounding box includes its wide-shot label, and that anchor
        # moves when the label does.
        self.rail_question_split = Conveyor(
            [
                self.chat.get_right() + RIGHT * 0.25,
                self.split.bay.get_left() + LEFT * 0.05,
            ],
            color=theme.TOKEN,
            chevrons=1,
        )
        # Split and ids sit on the bench line; the table is one unit higher, so
        # both of its rails turn one corner. Orthogonal, via an explicit dogleg
        # — a diagonal across a bench reads as sloppy.
        turn_l = 0.5 * (self.split.bay.get_right()[0] + self.table.bay.get_left()[0])
        self.rail_split_table = Conveyor(
            [
                self.split.bay.get_right() + RIGHT * 0.05,
                np.array([turn_l, BENCH_Y, 0.0]),
                np.array([turn_l, TABLE_POS[1], 0.0]),
                self.table.bay.get_left() + LEFT * 0.05,
            ],
            color=theme.TOKEN,
            chevrons=1,
        )
        turn_r = 0.5 * (self.table.bay.get_right()[0] + self.ids.bay.get_left()[0])
        self.rail_table_ids = Conveyor(
            [
                self.table.bay.get_right() + RIGHT * 0.05,
                np.array([turn_r, TABLE_POS[1], 0.0]),
                np.array([turn_r, BENCH_Y, 0.0]),
                self.ids.bay.get_left() + LEFT * 0.05,
            ],
            color=theme.TOKEN,
            chevrons=1,
        )
        self.rail_ids_door = Conveyor(
            [
                self.ids.bay.get_right() + RIGHT * 0.05,
                self.door.frame.get_left() + LEFT * 0.05,
            ],
            color=theme.EMBED,
            chevrons=1,
        )
        # The wall hangs off the table, pointing DOWN: the table builds the
        # wall, and what the rest of the bench uses is the wall's output.
        self.rail_wall_table = Conveyor(
            [
                self.vocab.wall.get_bottom() + DOWN * 0.05,
                self.table.bay.get_top() + UP * 0.05,
            ],
            color=theme.ATTENTION,
            chevrons=1,
        )
        # Faint, and it leaves DOWNWARD off the table: what goes down here is
        # the consequence of the split, not the payload. Drawing it in the
        # bench's amber would say the text travels via the billing meter.
        self.rail_table_meter = Conveyor(
            [
                self.table.bay.get_bottom() + DOWN * 0.05,
                self.meter.bay.get_top() + UP * 0.05,
            ],
            color=theme.FG_FAINT,
            chevrons=2,
        )

        # -- glow halos, pre-built and invisible --------------------------------
        # STROKE opacity only, for ever. `set_opacity` raises the copies' FILL
        # too, which turns a dozen transparent outlines into a dozen opaque
        # plates that bury whatever the bay contains. That bug presents as "the
        # labels went grey" and has cost this repo two sessions.
        self._glows: dict[int, VGroup] = {}
        halos = VGroup()
        for station in self.stations:
            halo = effects.glow(station.bay, station.accent)
            halo.set_stroke(opacity=0.0)
            self._glows[id(station)] = halo
            halos.add(halo)
        # Built AFTER the strip has been moved back to the SPLIT bay, so this
        # one sits where beat 2 lights it; `id_glow` above sits where beat 4 does.
        self.strawberry_glow = effects.glow(self.word_chip.box, theme.TOKEN)
        self.strawberry_glow.set_stroke(opacity=0.0)
        halos.add(self.strawberry_glow, self.id_glow)
        self.halos = halos
        self.resting_glow = 0.18

        # -- wide-shot names for the bays a Station cannot name -----------------
        self.chat_wide_label = typography.text(
            "heading", "QUESTION", frame_width=SHOT_WIDE,
            color=theme.USER, bold=True,
        )
        # Clamped to the window it names. At SHOT_WIDE a `heading` is 2.2 units
        # of cap height, so eight capitals measure 13.9 end to end against a
        # 9.6-wide window — unclamped it ran off the left edge of the pull-back
        # and read as a rendering fault rather than a label. Clamped it is 3.2%
        # of frame height, still well over typography.MIN_READABLE.
        if self.chat_wide_label.width > CHAT_W * 0.82:
            self.chat_wide_label.scale(
                CHAT_W * 0.82 / self.chat_wide_label.width
            )
        self.chat_wide_label.move_to(self.chat.get_center())
        self.wall_wide_label = typography.text(
            "heading", "VOCABULARY", frame_width=SHOT_WIDE,
            color=theme.ATTENTION, bold=True,
        )
        # Centred ON the wall, the way a Station's wide label sits inside its
        # bay. Above it would land on the counter, and the counter is the one
        # thing in that bay that has to stay legible.
        self.wall_wide_label.move_to(self.vocab.wall.get_center())
        self.wide_labels = VGroup(
            self.chat_wide_label, self.wall_wide_label, self.door.caption
        )
        self.wide_labels.set_opacity(0.0)

        # DRAW ORDER: halos and rails first, then the enclosure, then the bays,
        # so a rail terminates neatly UNDER the bay edge it feeds rather than
        # over it — and so nothing filled with `theme.BG` buries a rail that
        # runs inside it.
        self.add(
            halos,
            self.rail_question_split,
            self.rail_split_table,
            self.rail_table_ids,
            self.rail_ids_door,
            self.rail_wall_table,
            self.rail_table_meter,
            self.door,
            self.door_label,
            self.chat,
            *self.stations,
            self.vocab,
            # LAST. `ChatWindow`'s frame is filled at full opacity, so a wide
            # label added before it is drawn underneath and never appears — the
            # QUESTION marquee was invisible for the whole pull-back in the
            # first draft, and nothing but a frame said so.
            self.wide_labels,
        )

        # -- beat 6's ghost of the Arc 0 plant ----------------------------------
        # NOT part of `self` and NOT part of `everything`: it is added by the
        # scene in beat 6, and a prop nobody can see until 53s must not be able
        # to widen the pull-back that frames the film at 51s.
        self.bench_shrink = 0.11
        host = (
            self.everything.width * self.bench_shrink * 1.18,
            self.everything.height * self.bench_shrink * 1.30,
        )
        self.ghost = GhostCircuit(frame_width=SHOT_WIDE, host_size=host)
        self.ghost.move_to(self.everything.get_center())
        #: Set here rather than animated to: `FadeIn` restores a mobject to the
        #: opacity it already carries, so the prop is BUILT at its resting
        #: values and faded in from nothing. The label keeps its own full
        #: opacity — it lights separately, one beat later.
        #:
        #: The first cut filled these with BG_ELEVATED at 15% and measured
        #: **1.03:1** against the background — arithmetically invisible,
        #: because 15% of a near-black over a near-black is still the
        #: background, and the closing gesture simply did not land. In a dark
        #: theme the stroke is what gives a ghost its shape, not the fill, so
        #: the body sits at SURFACE and the outline carries the contrast.
        #: If you touch these, re-measure on an actual frame.
        self.ghost.rail.set_stroke(opacity=0.45)
        self.ghost.nodes.set_fill(theme.SURFACE, opacity=1.0)
        self.ghost.nodes.set_stroke(theme.FG_MUTED, opacity=0.55)
        # The host is the bay this whole film lives in. It keeps its own accent
        # and lights to full at 55.3s, so it must not be dimmed with the rest.
        self.ghost.host.set_stroke(theme.TOKEN, opacity=0.55)
        # And it is a FRAME, not a filled box: the shrunken bench comes to rest
        # inside it, and an opaque fill drawn over the top hides the one thing
        # the whole shot exists to show. Giving the other nine a solid body and
        # forgetting this cost exactly that on the first pass.
        self.ghost.host.set_fill(opacity=0.0)

        self.validate()

    # ------------------------------------------------------------- inventory
    @property
    def everything(self) -> VGroup:
        """What the final pull-back frames.

        The bays and the two long rails that join them — not the close-up-only
        props, which are faded out by the time the camera gets here and must not
        be able to widen `SHOT_WIDE`.
        """
        return VGroup(
            self.chat,
            self.split,
            self.table,
            # The wall's CELLS, not the `VocabWall` group: the group is emptied
            # above so its contents can arrive in beat 3, and an empty VGroup
            # sits at the origin and would drag this bounding box with it.
            self.vocab.cells,
            self.vocab.counter,
            self.ids,
            self.door,
            self.meter,
            self.rail_table_meter,
            self.wall_wide_label,
        )

    def glow_for(self, station) -> VGroup:
        try:
            return self._glows[id(station)]
        except KeyError:
            raise KeyError(
                f"no glow halo built for {station}. Halos are pre-built in "
                "TokenizerSet.__init__; constructing one mid-shot costs a beat."
            ) from None

    def wide_frame_width(self, pad: float = 1.0) -> float:
        """Camera width the final pull-back needs, matching `camera.frame_all`."""
        group = self.everything
        return max(
            group.width + 2 * pad, (group.height + 2 * pad) * typography.ASPECT
        )

    # ------------------------------------------------------------------ paths
    @staticmethod
    def _through(station) -> list:
        return [station.bay.get_left(), station.bay.get_right()]

    def bench_path(self):
        """Question → split → table → ids → door, built from the DRAWN rails.

        Never from bay centres. If the path is made of the rails the viewer can
        see, the travel and the diagram cannot disagree — which is exactly how a
        payload once ended up flying through solid boxes in an earlier film.
        """
        return routing.join(
            self.rail_question_split,
            self._through(self.split),
            self.rail_split_table,
            self._through(self.table),
            self.rail_table_ids,
            self._through(self.ids),
            self.rail_ids_door,
            [self.door.frame.get_left(), self.door.frame.get_center()],
        )

    def question_to_split_path(self):
        """The one hop beat 1 flies: out of the bubble, onto the bench."""
        return routing.join(
            self.rail_question_split,
            [self.split.bay.get_left(), self.split.bay.get_center()],
        )

    def ids_to_door_path(self):
        """Beat 4's crossing: out of the ids bay and through the model wall."""
        return routing.join(
            [self.ids.bay.get_center(), self.ids.bay.get_right()],
            self.rail_ids_door,
            [self.door.frame.get_left(), self.door.frame.get_center()],
        )

    def meter_spur_path(self):
        """The consequence spur: off the bottom of the table, down to the meter."""
        return routing.join(
            [self.table.bay.get_center(), self.table.bay.get_bottom()],
            self.rail_table_meter,
            [self.meter.bay.get_top(), self.meter.bay.get_center()],
        )

    # ------------------------------------------------------------- validation
    def validate(self) -> None:
        """Assert the geometry the choreography depends on.

        Called from ``__init__``, so a layout mistake fails here rather than in
        a render three minutes later — or, worse, in a shipped video. Every
        figure below is RE-DERIVED from the drawn mobjects; nothing trusts the
        constants at the top of this module.
        """
        # 1. The run down the bench must clear the two bays that are not on it.
        #    It goes deliberately THROUGH the four it visits — that is what a
        #    bench is for — so they are not obstacles.
        bench_obstacles = [
            ("the vocabulary wall", self.vocab.wall),
            ("the meter bay", self.meter.bay),
        ]
        routing.assert_path_clears(
            self.bench_path(), bench_obstacles, ignore_ends=0.03
        )

        # 2. And the consequence spur must clear everything except the two bays
        #    it joins.
        routing.assert_path_clears(
            self.meter_spur_path(),
            [
                ("the chat window", self.chat),
                ("the split bay", self.split.bay),
                ("the ids bay", self.ids.bay),
                ("the model box", self.door.frame),
                ("the vocabulary wall", self.vocab.wall),
            ],
            ignore_ends=0.05,
        )

        # 3. Bay separation, each failure named for what it actually is. A
        #    generic "nothing overlaps" check would not say which collapse
        #    happened or what to do about it.
        wall_gap = float(self.vocab.wall.get_bottom()[1]) - float(
            self.table.bay.get_top()[1]
        )
        if wall_gap < 0.5:
            raise AssertionError(
                f"the vocabulary wall sits {wall_gap:.3f} above the merge "
                "table, under the 0.5 minimum. The rail between them needs "
                "visible run, or the two read as one tall box. Raise WALL_POS."
            )
        meter_drop = float(self.table.bay.get_bottom()[1]) - float(
            self.meter.bay.get_top()[1]
        )
        if meter_drop < 3.0:
            raise AssertionError(
                f"the meter bay's top is only {meter_drop:.3f} below the merge "
                "table. The spur is the film's one change of direction and it "
                "needs room to read as one. Lower METER_POS."
            )
        for left, right, name in (
            (self.chat, self.split.bay, "chat → split"),
            (self.split.bay, self.table.bay, "split → table"),
            (self.table.bay, self.ids.bay, "table → ids"),
            (self.ids.bay, self.door.frame, "ids → door"),
        ):
            gap = float(right.get_left()[0]) - float(left.get_right()[0])
            if gap < 1.5:
                raise AssertionError(
                    f"the {name} gap is {gap:.3f}, under the 1.5 minimum. The "
                    "rail between them would have no visible run, so the two "
                    "bays read as one machine."
                )

        # 4. The character row has to fit the shot it is read in, at 16:9.
        #    Beat 1 frames the split bay at SHOT_BENCH with an upward shift, and
        #    a row wider than that frame loses its first and last characters —
        #    which in a film about counting characters is not a cosmetic bug.
        if self.row.width > SHOT_BENCH - 1.0:
            raise AssertionError(
                f"the character row is {self.row.width:.2f} wide against a "
                f"{SHOT_BENCH:.1f} shot. Ends of the sentence would be cropped "
                "in the one beat that counts characters. Lower ROW_WIDTH."
            )

        # 5. The payload is ONE object. Assertion 2 of the brief, made
        #    structural: if a later edit builds a second strip for beat 4, the
        #    ids and the chips can drift apart and no render would say so.
        if not (len(self.strip.chips) == len(self.id_faces) == len(IDS) == 7):
            raise AssertionError(
                f"{len(self.strip.chips)} chips, {len(self.id_faces)} id faces "
                f"and {len(IDS)} ids. These are one list, built once."
            )
        if len(self.row.cells) != len(QUESTION):
            raise AssertionError(
                f"the character row has {len(self.row.cells)} cells for a "
                f"{len(QUESTION)}-character question."
            )
        if self.row.r_count != WORD.count("r"):
            raise AssertionError(
                f"the row would pulse {self.row.r_count} cells but {WORD!r} has "
                f"{WORD.count('r')} r's. The sentence has "
                f"{QUESTION.lower().count('r')} — that difference is the trap "
                "this assertion exists for."
            )

        # 6. Zoom budget. Wide-shot type is sized against SHOT_WIDE, so letting
        #    the constant and the real pull-back drift apart is exactly what
        #    makes labels come out the wrong size, with nothing else to say so.
        actual = self.wide_frame_width()
        drift = abs(actual - SHOT_WIDE) / SHOT_WIDE
        if drift > 0.12:
            raise AssertionError(
                f"SHOT_WIDE is {SHOT_WIDE:.1f} but the pull-back actually needs "
                f"{actual:.1f} ({drift:.1%} off). Fix the LAYOUT — widening "
                "SHOT_WIDE to match is how a set quietly becomes unreadable."
            )

        # 7. The pull-back must CLEAR THE BOTTOM OF THE METER BAY. A shot that
        #    crops the bottom of a bay is the commonest bug in this format and
        #    the snapshot gate cannot see it, so it is asserted here rather than
        #    left to a frame review.
        frame_h = actual / typography.ASPECT
        needed_h = float(self.everything.height)
        if frame_h < needed_h + 1.0:
            raise AssertionError(
                f"the pull-back frame is {frame_h:.1f} tall against a "
                f"{needed_h:.1f}-tall world. The meter bay's bottom edge would "
                "be cropped. Shorten the column or widen the layout."
            )

        # 8. Nothing read at the pull-back may fall below the readability floor.
        items = [
            (f"{st.title_mob.text} wide label", st.wide_label)
            for st in self.stations
            if st.wide_label is not None
        ]
        items += [
            ("the model box title", self.door.caption),
            ("the question wide label", self.chat_wide_label),
            ("the vocabulary wide label", self.wall_wide_label),
            ("the ghost node label", self.ghost.label),
        ]
        unreadable = typography.audit(items, SHOT_WIDE)
        if unreadable:
            raise AssertionError(
                "below typography.MIN_READABLE at the pull-back: "
                + ", ".join(unreadable)
                + f". At SHOT_WIDE={SHOT_WIDE} these are decoration, not "
                "labels. Shorten the text or give the bay more room."
            )

        # 9. The shrunken bench must end up INSIDE the ghost's tokenizer node,
        #    not merely near it. "Is the bench inside the node?" is on the frame
        #    review list precisely because it is easy to get almost right.
        host = self.ghost.host
        bench_w = float(self.everything.width) * self.bench_shrink
        bench_h = float(self.everything.height) * self.bench_shrink
        if bench_w > float(host.width) or bench_h > float(host.height):
            raise AssertionError(
                f"the bench shrinks to {bench_w:.2f}x{bench_h:.2f} but the "
                f"ghost's tokenizer node is {float(host.width):.2f}x"
                f"{float(host.height):.2f}. It would hang out of the node it is "
                "supposed to be inside."
            )

    def reveal_labels(self, opacity: float = 1.0) -> list:
        """Animations bringing up every wide-shot label for the pull-back.

        Each bay cross-fades its close-up header out as its pull-back label
        comes in, so a bay carries exactly one name at any distance.
        `Station.reveal_wide` fades text on fill and icons on stroke — do not
        "simplify" it into one `set_opacity`, or every icon returns as a blob.
        """
        # docs/slides.md rule 4: arriving content enters with FadeIn. Raising
        # opacity here made the deck read this play as a clear-down and merge
        # the wide diagram forward, costing the film's summary frame its stop.
        # `wide_labels` is BUILT at opacity 0 so it stays invisible until the
        # pull-back, and `FadeIn` animates up to a mobject's CURRENT opacity —
        # so it must be given its target state first or it fades 0 -> 0 and the
        # marquees never appear. (They did not, on the first pass at this fix,
        # with all five gates green. Look at the frame.)
        self.wide_labels.set_opacity(opacity)
        anims = [FadeIn(self.wide_labels)]
        # A Station empties itself for the wide shot; the vocabulary wall is not
        # a Station and kept drawing all 126 cells under its own marquee. Dim
        # them so the label reads, and leave the counter alone - at this
        # distance "= 200,000" is the only part of the wall that still means
        # anything.
        anims.append(self.vocab.cells.animate.set_opacity(0.18))
        # The chat is not a Station and has none of Station's cross-fade
        # machinery, so it gets the same treatment by hand: its close-up
        # furniture goes dark as its pull-back name comes up, leaving an empty
        # lit window with one word in it, like every bay beside it.
        anims.append(self.door_label.animate.set_opacity(1.0 - opacity))
        for part in (
            self.chat.title_mob, self.chat.divider, self.chat.messages,
        ):
            anims.append(part.animate.set_opacity(1.0 - opacity))
        if self.chat.input is not None:
            anims.append(self.chat.input.animate.set_opacity(1.0 - opacity))
        for station in self.stations:
            anims.extend(station.reveal_wide(opacity))
        return anims
