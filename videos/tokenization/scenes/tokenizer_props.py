"""Local one-off visuals for the tokenization film.

Four props, all of them specific to this video and therefore NOT promoted into
``/lib`` (root ``AGENTS.md`` → the promotion rule: a one-off stays in the
video's ``scenes/`` until a second scene needs it, and it gets a test at the
moment it moves, not before).

* :class:`CharacterRow` — the 27 character cells of B1, with ``wipe_dark()``.
* :class:`MergeTable` — the three worked merge rows and the ordered list.
* :class:`VocabWall` — the dense column and its counter.
* :class:`GhostCircuit` — B6's ten faint nodes, one of them labelled.

``GhostCircuit`` is a *gesture* at the Arc 0 film, not a rendering of it: ten
dots and one label. It deliberately does not import
``chatgpt_request_lifecycle`` — videos are self-contained.
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Circle, Line, Transform, VGroup

from lib import theme, typography, utils


# ==========================================================================
# B1 — the character row
# ==========================================================================
class CharacterCell(VGroup):
    """One character of the question, in its own cell.

    ``char`` is kept on the mobject so the row can count its own contents
    rather than a caption asserting a number nobody re-derives.
    """

    def __init__(
        self,
        char: str,
        *,
        cell_width: float,
        cell_height: float,
        shot_width: float,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.char = char
        self.box = utils.panel(
            width=cell_width,
            height=cell_height,
            fill=theme.SURFACE,
            stroke=theme.BORDER,
            stroke_width=theme.STROKE_HAIRLINE,
            radius=theme.CORNER_RADIUS * 0.5,
        )
        shown = char if char.strip() else ""
        self.glyph = typography.text(
            "label", shown or "·", frame_width=shot_width, color=theme.FG, mono=True
        )
        if not shown:
            # A space is a real character and gets a real cell, but drawing a
            # "·" as bright as a letter reads as a typo. Faint says "this is
            # here, it is not a letter" without needing a caption.
            self.glyph.set_color(theme.FG_FAINT)
        if self.glyph.width > cell_width * 0.8:
            self.glyph.scale(cell_width * 0.8 / self.glyph.width)
        self.glyph.move_to(self.box.get_center())
        self.add(self.box, self.glyph)


class CharacterRow(VGroup):
    """The question, one cell per character. Derived from the string.

    The whole point of building it this way is that the row cannot disagree
    with the copy: ``len(row.cells)`` is ``len(text)`` by construction, and
    :meth:`r_count_in` counts the cells the film actually pulses.
    """

    def __init__(
        self,
        text: str,
        *,
        width: float,
        shot_width: float,
        highlight_word: str,
        gap: float = 0.06,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.text = text
        self.highlight_word = highlight_word

        pitch = width / len(text)
        cell_width = pitch - gap
        cell_height = cell_width * 1.4

        self.cells = VGroup(
            *[
                CharacterCell(
                    ch,
                    cell_width=cell_width,
                    cell_height=cell_height,
                    shot_width=shot_width,
                )
                for ch in text
            ]
        ).arrange(RIGHT, buff=gap)
        self.add(self.cells)

    # ------------------------------------------------------------- counting
    def cells_in(self, word: str) -> list:
        """The cells belonging to ``word`` inside the question."""
        start = self.text.index(word)
        return list(self.cells[start : start + len(word)])

    def r_cells_in(self, word: str) -> list:
        """The ``r`` cells inside ``word``, and no others.

        Scoped to the word on purpose. The question also contains a standalone
        ``r`` in ``r's``, so counting the whole string would put a 4 on screen
        under a caption about strawberry.
        """
        return [cell for cell in self.cells_in(word) if cell.char == "r"]

    def r_count_in(self, word: str) -> int:
        return len(self.r_cells_in(word))

    # -------------------------------------------------------------- states
    def highlight_anims(self, color=None):
        """Animations pulsing the ``r`` cells of the highlighted word."""
        color = color or theme.WARN
        return [
            cell.glyph.animate.set_color(color)
            for cell in self.r_cells_in(self.highlight_word)
        ] + [
            cell.box.animate.set_stroke(color, width=theme.STROKE_NORMAL)
            for cell in self.r_cells_in(self.highlight_word)
        ]

    def wipe_anims(self):
        """Every cell drops to ``FG_FAINT``. Left to right, one per cell.

        The single most important frame in the film is the end of this: what
        comes before it has letters, and nothing after it does.
        """
        return [
            VGroup(cell.glyph, cell.box).animate.set_color(theme.FG_FAINT)
            for cell in self.cells
        ]


# ==========================================================================
# B3 — the worked merges and the ordered list
# ==========================================================================
class MergeUnit(VGroup):
    """One cell of a merge row. Carries the token it currently spells."""

    def __init__(self, token: str, *, shot_width: float, **kwargs) -> None:
        super().__init__(**kwargs)
        self.token = token
        self.glyph = typography.text(
            "body", token, frame_width=shot_width, color=theme.FG, mono=True
        )
        self.box = utils.panel(
            width=max(0.46, self.glyph.width + 2 * theme.PAD_XS),
            height=self.glyph.height + 2 * theme.PAD_XS,
            fill=theme.SURFACE,
            stroke=theme.BORDER,
            stroke_width=theme.STROKE_HAIRLINE,
            radius=theme.CORNER_RADIUS * 0.5,
        )
        self.glyph.move_to(self.box.get_center())
        self.add(self.box, self.glyph)


class MergeCell:
    """Bookkeeping for one cell of a merge row: what it spells, and what draws it.

    A merge does not destroy the two boxes it joins — they slide together and
    stay. So a cell is a *list* of drawn units plus the token they now spell,
    and the next merge addresses the whole run. Collapsing the pair into one
    mobject was the first attempt, and it left the second merge moving the `l`
    box and the `w` box on top of the `o` box still sitting between them.
    """

    __slots__ = ("token", "parts")

    def __init__(self, token: str, parts: list) -> None:
        self.token = token
        self.parts = parts

    @property
    def left(self) -> float:
        return min(float(p.box.get_left()[0]) for p in self.parts)

    @property
    def right(self) -> float:
        return max(float(p.box.get_right()[0]) for p in self.parts)


class MergeTable(VGroup):
    """Three words as loose letters, merged a pair at a time, plus the list.

    The merge example is **ours**, in the shape of the BPE paper's worked
    example — the note under it says so, because captioning it as the paper's
    would be a citation this film has not earned.

    Each merge is derived: :meth:`merge_anims` looks for the adjacent cells
    whose tokens are the ones being merged, so a row that does not contain the
    pair is simply not touched, and nothing is positioned by hand per merge.

    **Everything this prop will ever draw is built in the constructor**, the
    list entries and the ramp's counter faces included. A caller fits this whole
    group into a station bay, and anything created afterwards is drawn at the
    unscaled size — which is how the ordered list first came out hanging past
    the right-hand edge of the bay.

    The cells move by animating their own ``box`` and ``glyph`` rather than the
    unit group. A ``VGroup`` carries its own (transparent) rgba, and animating
    one drags every child's opacity down with it — the trap that reads as a
    colour bug and is a grouping one.
    """

    #: Entry slots reserved under the listing's title, so the counter beneath
    #: them does not move as entries arrive.
    ENTRY_SLOTS = 5

    def __init__(
        self,
        words: list[str],
        merges: list[tuple[str, str]],
        ramp_labels: list[str],
        *,
        shot_width: float,
        gap: float = 0.1,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.words = list(words)
        self.merges = list(merges)
        self.shot_width = shot_width
        self.gap = gap

        #: Per row, the cells currently on screen, in order.
        self.cells: list[list[MergeCell]] = []
        rows = VGroup()
        for word in words:
            units = [MergeUnit(ch, shot_width=shot_width) for ch in word]
            VGroup(*units).arrange(RIGHT, buff=gap)
            self.cells.append([MergeCell(u.token, [u]) for u in units])
            rows.add(VGroup(*units))
        self.rows = rows.arrange(DOWN, buff=theme.PAD_SM, aligned_edge=LEFT)

        # -- the ordered list, to the right of the rows ---------------------
        self.list_title = typography.text(
            "caption", "merges, in order", frame_width=shot_width,
            color=theme.FG_MUTED,
        )
        self.entries = VGroup(
            *[
                typography.text(
                    "caption", f"{i + 1}.  {a} + {b}  ->  {a + b}",
                    frame_width=shot_width, color=theme.FG, mono=True,
                )
                for i, (a, b) in enumerate(self.merges)
            ]
        )
        anchor = self.list_title
        for entry in self.entries:
            entry.next_to(anchor, DOWN, buff=theme.PAD_XS)
            entry.align_to(self.list_title, LEFT)
            anchor = entry

        self.counter = self._counter_face("merge 1")
        self.counter.next_to(
            self.list_title,
            DOWN,
            buff=(self.list_title.height + theme.PAD_XS) * self.ENTRY_SLOTS,
        )
        self.counter.align_to(self.list_title, LEFT)

        #: The ramp's counter faces, pre-built for the same reason the entries
        #: are: created later, they would be drawn at the unscaled size.
        self.tickers = {}
        self.ramp = ramp = VGroup()
        for label in ramp_labels:
            face = RampTicker(
                label, shot_width=shot_width, anchor=self.counter.get_center()
            )
            self.tickers[label] = face
            ramp.add(face)

        self.note = typography.text(
            "caption", "worked example · not the paper's",
            frame_width=shot_width, color=theme.FG_FAINT,
        )

        self.listing = VGroup(self.list_title, self.entries, self.counter, ramp)
        #: Detached by :meth:`detach_staged` once the caller has fitted this
        #: group — they are built here so a fit scales them, and taken out so
        #: adding the table to a scene does not render every entry at once.
        self.listing.next_to(self.rows, RIGHT, buff=theme.PAD_MD)
        self.listing.align_to(self.rows, UP)
        self.note.next_to(self.rows, DOWN, buff=theme.PAD_SM)
        self.note.align_to(self.rows, LEFT)
        self.add(self.rows, self.listing, self.note)

    def detach_staged(self) -> None:
        """Take the entries and the ramp faces out of the drawn group.

        Call AFTER fitting the table into its bay: built as children so the fit
        scales them, detached so ``scene.add(table)`` does not put the finished
        list and all four counter faces on screen at once.
        """
        self.listing.remove(self.entries, self.ramp)

    def _counter_face(self, label: str):
        return typography.text(
            "caption", label, frame_width=self.shot_width,
            color=theme.ATTENTION, mono=True,
        )

    # --------------------------------------------------------------- merges
    def merge_anims(self, step: int):
        """Animations for merge ``step`` (0-based) and the entry it writes.

        The pair closes the gap between them and takes the ``WARN`` highlight;
        everything to its right closes up behind it by the same amount.
        """
        left, right = self.merges[step]
        anims = []

        for row in self.cells:
            hit = next(
                (
                    i
                    for i in range(len(row) - 1)
                    if row[i].token == left and row[i + 1].token == right
                ),
                None,
            )
            if hit is None:
                continue
            a, b = row[hit], row[hit + 1]
            closing = b.left - a.right
            for cell, delta in (
                (a, np.array([closing / 2, 0.0, 0.0])),
                (b, np.array([-closing / 2, 0.0, 0.0])),
            ):
                for unit in cell.parts:
                    anims.append(
                        unit.box.animate.shift(delta).set_stroke(
                            theme.WARN, width=theme.STROKE_NORMAL
                        )
                    )
                    anims.append(
                        unit.glyph.animate.shift(delta).set_color(theme.WARN)
                    )
            for later in row[hit + 2 :]:
                for unit in later.parts:
                    anims.append(
                        unit.box.animate.shift(np.array([-closing, 0.0, 0.0]))
                    )
                    anims.append(
                        unit.glyph.animate.shift(np.array([-closing, 0.0, 0.0]))
                    )
            # The run now spells the merged token, which is what makes merge 2
            # find `lo` + `w` without anybody writing an index down.
            row[hit] = MergeCell(left + right, a.parts + b.parts)
            del row[hit + 1]

        anims.append(Transform(self.counter, self._placed(f"merge {step + 1}")))
        return anims, self.entries[step]

    def _placed(self, label: str):
        face = self._counter_face(label)
        face.scale_to_fit_height(self.counter.height)
        face.move_to(self.counter.get_center(), aligned_edge=LEFT)
        return face

    # ----------------------------------------------------------------- ramp
    def ticker(self, label: str) -> "RampTicker":
        """The pre-built counter face for one step of B3's ramp.

        Its own class so the deck can recognise the ramp by *what it animates*
        rather than by a play index — an index moves silently when a beat is
        re-ordered. See ``videos/tokenization/slides.py``.
        """
        return self.tickers[label]


class RampTicker(VGroup):
    """One face of B3's ``merge 4`` -> ``merge 50,000`` counter.

    A distinct class purely so the deck's ``_sticky_play`` can recognise the
    ramp's plays. The figures on it are illustrative and it says so.
    """

    def __init__(self, label: str, *, shot_width: float, anchor, **kwargs) -> None:
        super().__init__(**kwargs)
        self.face = typography.text(
            "caption", label, frame_width=shot_width,
            color=theme.ATTENTION, mono=True,
        )
        self.face.move_to(anchor, aligned_edge=LEFT)
        self.add(self.face)


# ==========================================================================
# B3 — the vocabulary wall
# ==========================================================================
#: Plausible subword pieces for the wall's decoration. Real-looking rather than
#: real: at this size they are texture, not a claim, and the beat's claim is
#: the counter underneath.
_WALL_PIECES = (
    "ing", " the", "tion", "ly", " of", "ed", " in", "er", " to", "al",
    "ous", " and", "ment", "ity", " a", "re", "un", " for", "ness", "able",
    "st", "raw", "berry", " is", "pre", " on", "est", "ive", " it", "ary",
)


class VocabWall(VGroup):
    """The dense column of everything the model can ever see, and its counter.

    Most cells are deliberately below ``typography.MIN_READABLE`` at the shot
    they are seen in. That is not an oversight — the wall is texture, and the
    one thing on it the viewer is meant to read is the counter.
    """

    def __init__(
        self,
        *,
        width: float,
        height: float,
        caption: str,
        shot_width: float,
        accent=None,
        # Dense on purpose. At 6x22 in a 3.6x4.6 wall almost every cell lands
        # below `typography.MIN_READABLE` at SHOT_TIGHT, which is the point: the
        # wall is texture and the counter beside it is the one readable thing.
        columns: int = 6,
        rows: int = 22,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        accent = accent or theme.ATTENTION

        cell_w = width / columns - 0.045
        cell_h = height / rows - 0.045
        self.cells = VGroup()
        for r in range(rows):
            for c in range(columns):
                # Stride by columns+1, not columns: with 30 pieces in 6
                # columns the naive index repeats the same block every five
                # rows, and the repeat is visible even at this size.
                piece = _WALL_PIECES[(r * (columns + 1) + c) % len(_WALL_PIECES)]
                box = utils.panel(
                    width=cell_w,
                    height=cell_h,
                    fill=theme.SURFACE,
                    stroke=theme.BORDER,
                    stroke_width=theme.STROKE_HAIRLINE * 0.6,
                    radius=theme.CORNER_RADIUS * 0.3,
                )
                glyph = typography.text(
                    "micro", piece, frame_width=shot_width, color=theme.FG_MUTED,
                    mono=True,
                )
                glyph.scale(min(cell_w * 0.86 / glyph.width, cell_h * 0.7 / glyph.height))
                cell = VGroup(box, glyph)
                glyph.move_to(box.get_center())
                cell.move_to(
                    np.array(
                        [
                            -width / 2 + (c + 0.5) * width / columns,
                            height / 2 - (r + 0.5) * height / rows,
                            0.0,
                        ]
                    )
                )
                self.cells.add(cell)

        self.frame = utils.panel(
            width=width + 0.3,
            height=height + 0.3,
            fill=theme.BG_ELEVATED,
            stroke=accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        self.add(self.frame, self.cells)

        #: The counter and its caption sit BESIDE the wall, not under it. The
        #: wall is tall and the shot that reads it is 12 wide, so the column
        #: beside it is the only place with room at a readable size.
        self.counter = typography.text(
            "heading", caption, frame_width=shot_width, color=accent, bold=True
        )
        self.sub = typography.text(
            "label",
            "every piece the\nmodel can ever see",
            frame_width=shot_width,
            color=theme.FG_MUTED,
        )
        self.readout = VGroup(self.counter, self.sub).arrange(
            DOWN, buff=theme.PAD_SM, aligned_edge=LEFT
        )
        self.readout.next_to(self.frame, RIGHT, buff=theme.PAD_MD)
        self.add(self.readout)


# ==========================================================================
# B6 — the ghost circuit
# ==========================================================================
class GhostCircuit(VGroup):
    """Ten faint nodes in the Arc 0 circuit's shape, one of them labelled.

    A gesture at that film, not a rendering of it. Ten dots and one label is
    the whole prop — if it grows past forty lines it is being over-built.

    The layout is height-bound by the closing wide frame, so the node radius
    and the level pitch are chosen together and exposed: the set derives the
    bench's shrink factor from ``node_radius`` rather than hardcoding one.
    """

    #: Node radius and vertical pitch, in world units at the wide shot.
    RADIUS = 2.3
    PITCH = 5.28
    HALF_SPAN = 10.0

    def __init__(self, *, labelled: str, shot_width: float, accent=None, **kwargs):
        super().__init__(**kwargs)
        accent = accent or theme.TOKEN
        self.node_radius = self.RADIUS
        levels = [(2.5 - i) * self.PITCH for i in range(6)]

        # Down the right-hand column, back up the left: Arc 0's loop.
        centres = (
            [np.array([0.0, levels[0], 0.0])]
            + [np.array([self.HALF_SPAN, y, 0.0]) for y in levels[1:5]]
            + [np.array([0.0, levels[5], 0.0])]
            + [np.array([-self.HALF_SPAN, y, 0.0]) for y in reversed(levels[1:5])]
        )
        self.nodes = VGroup(
            *[
                Circle(
                    radius=self.RADIUS,
                    stroke_color=theme.FG_MUTED,
                    stroke_width=theme.STROKE_NORMAL,
                    stroke_opacity=0.40,
                    fill_color=theme.BG_ELEVATED,
                    fill_opacity=0.15,
                ).move_to(c)
                for c in centres
            ]
        )
        self.wires = VGroup(
            *[
                Line(
                    a,
                    b,
                    stroke_color=theme.FG_FAINT,
                    stroke_width=theme.STROKE_NORMAL,
                    stroke_opacity=0.55,
                )
                for a, b in zip(centres, centres[1:] + centres[:1])
            ]
        )
        #: chat, server, TOKENIZER, ... — the third node in pipeline order.
        self.labelled_node = self.nodes[2]
        self.label = typography.text(
            "label", labelled, frame_width=shot_width, color=accent, bold=True
        )
        self.label.next_to(self.labelled_node, LEFT, buff=theme.PAD_LG)
        # The label is a child for layout and is faded in on its own — B6 lights
        # exactly one node, and the label arrives with it.
        self.add(self.wires, self.nodes, self.label)


__all__ = [
    "CharacterCell",
    "CharacterRow",
    "MergeUnit",
    "MergeTable",
    "RampTicker",
    "VocabWall",
    "GhostCircuit",
]
