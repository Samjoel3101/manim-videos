"""Local one-offs for the tokenization film.

Four props, and every one of them is deliberately **not** in `/lib`. The root
`AGENTS.md` promotion rule is "used by 2+ scenes, or clearly needed by a future
video"; none of these has a second consumer yet, so they stay here and get
promoted the moment one appears. `CharacterRow` is the likeliest candidate —
the "Forcing JSON" episode is about exactly the character/token mismatch this
film's beat 1 draws — and when that happens it moves to `/lib` with a
structural test, not before.

Everything is sized against the shot it is read in (`lib/typography.py`); no
prop here takes a point size. Colour comes from `lib/theme.py`.
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, Line, Rectangle, RoundedRectangle, VGroup

from lib import theme, typography

__all__ = ["CharacterRow", "MergeTable", "VocabWall", "GhostCircuit"]


class _Cell(VGroup):
    """One character of the question, in its own box.

    A box plus (usually) one glyph. A space gets a box and no glyph, which is
    the honest drawing: the space IS a character, and the film's whole point in
    beat 2 is that the tokenizer keeps it. Drawing it as `␣` was considered and
    rejected for the reason `lib/components/tokens.SPACE_GLYPH` gives — at this
    size it reads as a rendering fault rather than as a space.
    """

    def __init__(self, char: str, *, width: float, height: float,
                 frame_width: float, **kwargs) -> None:
        super().__init__(**kwargs)
        self.char = char
        self.box = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=theme.CORNER_RADIUS * 0.5,
            fill_color=theme.SURFACE,
            fill_opacity=1.0,
            stroke_color=theme.BORDER,
            stroke_width=theme.STROKE_HAIRLINE,
        )
        self.add(self.box)

        self.glyph = None
        if char.strip():
            self.glyph = typography.text(
                "label", char, frame_width=frame_width, color=theme.FG, mono=True
            )
            # Clamp rather than trust: an apostrophe and a "w" are very
            # different widths at the same point size, and one overflowing cell
            # in a row of 27 reads as a layout bug.
            if self.glyph.width > width * 0.8:
                self.glyph.scale(width * 0.8 / self.glyph.width)
            self.glyph.move_to(self.box.get_center())
            self.add(self.glyph)

    def darken(self) -> list:
        """Animations taking this cell to `FG_FAINT` — the wipe, per cell."""
        anims = [self.box.animate.set_stroke(color=theme.FG_FAINT)]
        if self.glyph is not None:
            anims.append(self.glyph.animate.set_color(theme.FG_FAINT))
        return anims

    def light(self, color) -> list:
        """Animations lighting this cell — beat 1's three `r`s."""
        anims = [self.box.animate.set_stroke(color=color, width=theme.STROKE_NORMAL)]
        if self.glyph is not None:
            anims.append(self.glyph.animate.set_color(color))
        return anims


class CharacterRow(VGroup):
    """The question as one box per character.

    The row is what the wipe happens to, and the wipe is the single most
    important frame in the film: everything before it has letters in it and
    nothing after it does.

    ``highlight_span`` is the ``(start, stop)`` slice whose ``r``s are the ones
    beat 1 pulses. It exists because the sentence has **four** ``r``s and the
    word has **three** — the ``r`` in ``r's`` is the fourth, and pulsing it
    would contradict the ``3`` on screen. The count is derived from the span,
    never written down.
    """

    def __init__(self, text: str, *, frame_width: float, width: float = 13.2,
                 highlight_span: tuple[int, int] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.source = text
        gap = 0.03
        cell_w = (width - gap * (len(text) - 1)) / len(text)
        cell_h = cell_w * 1.45

        self.cells = VGroup(
            *[
                _Cell(ch, width=cell_w, height=cell_h, frame_width=frame_width)
                for ch in text
            ]
        ).arrange(RIGHT, buff=gap)
        self.add(self.cells)

        start, stop = highlight_span if highlight_span else (0, len(text))
        self.highlight_span = (start, stop)
        #: The cells the beat pulses: the `r`s INSIDE the span, not in the
        #: sentence. Derived from the span so the two can never disagree.
        self.r_cells = [
            self.cells[i]
            for i in range(start, stop)
            if text[i].lower() == "r"
        ]

    @property
    def r_count(self) -> int:
        return len(self.r_cells)

    def wipe_dark(self) -> list:
        """One animation group per cell, in reading order, for a `LaggedStart`.

        Returned rather than played, so the scene owns the timing and the rate
        function — the wipe is a 1.2s `motion.SHARP` sweep and nothing else in
        the film moves during it.
        """
        from manim import AnimationGroup

        return [AnimationGroup(*cell.darken()) for cell in self.cells]


class MergeTable(VGroup):
    """The worked BPE example: three words, three merges, one ordered list.

    The example is **ours**, in the shape of the BPE paper's worked example.
    It is not captioned as the paper's, and nothing here claims these are
    `o200k_base`'s first three merges — they are not, and the film does not say
    they are.

    The merge is drawn as two letters sliding together rather than as a
    `Transform` between two rows: a Transform between rows of unequal length
    re-flows every letter on screen, so the one pair the beat is about is the
    hardest thing in the frame to follow.
    """

    WORDS = ("low", "lower", "newest")
    #: ``(left, right, merged)``, in order. Verified against the word list at
    #: construction: a merge that matches no row would be a lie on screen.
    MERGES = (("l", "o", "lo"), ("lo", "w", "low"), ("e", "s", "es"))

    def __init__(self, *, frame_width: float, pitch: float = 0.62,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.frame_width = frame_width
        self.pitch = pitch

        #: Per row: the live token list, and the mobject group holding each.
        self.row_tokens: list[list[str]] = [list(w) for w in self.WORDS]
        self.row_units: list[list[VGroup]] = []

        rows = VGroup()
        for word in self.WORDS:
            units = []
            row = VGroup()
            for i, ch in enumerate(word):
                glyph = typography.text(
                    "body", ch, frame_width=frame_width, color=theme.FG, mono=True
                )
                # A FIXED origin per row, not `arrange`: every row's letters
                # then sit on the same column grid, so "the l and the o" is the
                # same pair of columns in row 1 and row 2 and the merge reads
                # across all of them at once.
                glyph.move_to(np.array([i * pitch, 0.0, 0.0]))
                unit = VGroup(glyph)
                units.append(unit)
                row.add(unit)
            self.row_units.append(units)
            rows.add(row)
        rows.arrange(DOWN, buff=theme.PAD_MD, aligned_edge=LEFT)
        self.rows = rows
        self.add(rows)

        # The ordered list, to the right of the words. Built empty; entries are
        # faded in one per merge by the scene.
        self.list_title = typography.text(
            "caption", "merges", frame_width=frame_width,
            color=theme.FG_MUTED,
        )
        self.list_entries = VGroup()
        self.ordered = VGroup(self.list_title)
        self.ordered.next_to(rows, RIGHT, buff=theme.PAD_XL)
        self.ordered.align_to(rows, UP)
        self.add(self.ordered)

        self._validate()

    def _validate(self) -> None:
        tokens = [list(w) for w in self.WORDS]
        for left, right, merged in self.MERGES:
            if left + right != merged:
                raise AssertionError(
                    f"merge {left!r}+{right!r} is written as {merged!r}, which "
                    "is not what concatenating them gives."
                )
            hits = 0
            for row in tokens:
                j = self._find(row, left, right)
                if j is not None:
                    row[j : j + 2] = [merged]
                    hits += 1
            if hits == 0:
                raise AssertionError(
                    f"merge {left!r}+{right!r} matches none of {self.WORDS}. A "
                    "merge nothing on screen performs is a lie in the one beat "
                    "that claims the merges are counted rather than chosen."
                )

    @staticmethod
    def _find(tokens: list[str], left: str, right: str) -> int | None:
        for j in range(len(tokens) - 1):
            if tokens[j] == left and tokens[j + 1] == right:
                return j
        return None

    def merge_step(self, index: int) -> list:
        """Animations for merge ``index``: light the pair, then close the gap.

        Mutates the live token lists, so calling it twice for the same index
        would be a no-op rather than a double merge — the second call finds no
        pair.
        """
        left, right, merged = self.MERGES[index]
        anims: list = []
        for row_i, tokens in enumerate(self.row_tokens):
            j = self._find(tokens, left, right)
            if j is None:
                continue
            a, b = self.row_units[row_i][j], self.row_units[row_i][j + 1]
            midpoint = 0.5 * (a.get_center() + b.get_center())
            # Close most of the gap, not all of it: two glyphs overlapping is a
            # rendering fault, two glyphs touching is a merged token.
            pull = 0.38 * (midpoint - a.get_center())
            anims.append(
                a.animate.set_color(theme.WARN).shift(pull)
            )
            anims.append(
                b.animate.set_color(theme.WARN).shift(-pull)
            )
            tokens[j : j + 2] = [merged]
            self.row_units[row_i][j : j + 2] = [VGroup(a, b)]
        return anims

    def list_entry(self, index: int):
        """The ordered-list line for merge ``index``, positioned and unattached."""
        left, right, merged = self.MERGES[index]
        line = typography.text(
            "caption",
            f"{index + 1}.  {left} + {right}  →  {merged}",
            frame_width=self.frame_width,
            color=theme.FG,
            mono=True,
        )
        anchor = (
            self.list_title if not self.list_entries else self.list_entries[-1]
        )
        line.next_to(anchor, DOWN, buff=theme.PAD_SM)
        line.align_to(self.list_title, LEFT)
        self.list_entries.add(line)
        self.ordered.add(line)
        return line

    def tail_entry(self, text: str):
        """A further line for the scroll ramp — `merge 4`, `merge 50,000`."""
        line = typography.text(
            "caption", text, frame_width=self.frame_width,
            color=theme.FG_MUTED, mono=True,
        )
        anchor = (
            self.list_title if not self.list_entries else self.list_entries[-1]
        )
        line.next_to(anchor, DOWN, buff=theme.PAD_SM)
        line.align_to(self.list_title, LEFT)
        self.list_entries.add(line)
        self.ordered.add(line)
        return line


class VocabWall(VGroup):
    """The finished vocabulary: a dense column of pieces, and how many there are.

    Most cells are deliberately below `typography.MIN_READABLE` at the shot
    this is seen in. That is the content: the wall is not a list to be read,
    it is a quantity to be felt, and the counter under it is the only thing in
    the bay that has to be legible.
    """

    PIECES = (
        "the", "ing", "tion", " str", "aw", "berry", " to", "ly", " ?", "ed",
        " in", "'s", "ver", " an", "est", "low", " re", "ough", " my", "ate",
    )

    def __init__(self, *, frame_width: float, cols: int = 9, rows: int = 16,
                 cell: float = 0.55, **kwargs) -> None:
        super().__init__(**kwargs)
        gap = 0.05
        self.cells = VGroup()
        for r in range(rows):
            for c in range(cols):
                # A deterministic wobble, so the wall looks woven rather than
                # printed, and so re-renders are identical.
                t = ((r * 7 + c * 13) % 11) / 10.0
                box = Rectangle(
                    width=cell,
                    height=cell * 0.52,
                    fill_color=theme.ATTENTION,
                    fill_opacity=0.10 + 0.32 * t,
                    stroke_width=0,
                )
                box.move_to(
                    np.array([c * (cell + gap), -r * (cell * 0.52 + gap), 0.0])
                )
                self.cells.add(box)
        self.add(self.cells)

        # A handful of real pieces, scattered, so the wall reads as text rather
        # than as a heatmap. Under the readability floor on purpose.
        self.samples = VGroup()
        for k, piece in enumerate(self.PIECES):
            idx = (k * 23 + 5) % len(self.cells)
            glyph = typography.text(
                "micro", piece, frame_width=frame_width,
                color=theme.FG_MUTED, mono=True,
            )
            glyph.scale(min(1.0, (cell * 0.82) / max(glyph.width, 1e-6)))
            glyph.move_to(self.cells[idx].get_center())
            self.samples.add(glyph)
        self.add(self.samples)

        self.counter = typography.text(
            "heading", "≈ 200,000", frame_width=frame_width,
            color=theme.ATTENTION, bold=True,
        )
        self.counter.next_to(self.cells, DOWN, buff=theme.PAD_MD)
        self.add(self.counter)

    @property
    def wall(self) -> VGroup:
        """The dense block alone — what a camera frames and a rail lands on."""
        return self.cells


class GhostCircuit(VGroup):
    """Beat 6's gesture at the Arc 0 plant: ten faint nodes, one of them named.

    Deliberately NOT an import of `chatgpt_request_lifecycle`'s set. Videos are
    self-contained, and this is a gesture at that film rather than a rendering
    of it — ten dots and one label is the whole prop.
    """

    #: The Arc 0 circuit, abstracted: a top band, a column down the right, and
    #: the way home along the bottom. Index 5 is the tokenizer — the bay this
    #: entire film lives inside — and it is the only one that gets a name.
    NODES = (
        (-20.0, 11.0), (-10.0, 11.0), (0.0, 11.0), (10.0, 11.0), (20.0, 11.0),
        (20.0, 3.0), (20.0, -4.0), (20.0, -9.5),
        (2.0, -13.0), (-20.0, -13.0),
    )
    HOST_INDEX = 5

    def __init__(self, *, frame_width: float, host_size: tuple[float, float],
                 **kwargs) -> None:
        super().__init__(**kwargs)
        pts = [np.array([x, y, 0.0]) for x, y in self.NODES]

        # Orthogonal, via an explicit corner wherever two nodes differ in both
        # axes. A diagonal across a circuit diagram reads as sloppy, and the one
        # link that needed it — the turn out of the column onto the bottom band
        # — was the only thing in the wide shot drawn at an angle.
        self.rail = VGroup()
        for a, b in zip(list(pts) + [pts[0]], list(pts[1:]) + [pts[0], pts[0]]):
            if a is b:
                continue
            corner = np.array([a[0], b[1], 0.0])
            for p, q in ((a, corner), (corner, b)):
                if np.linalg.norm(q - p) > 1e-6:
                    self.rail.add(
                        Line(p, q, stroke_color=theme.FG_FAINT,
                             stroke_width=theme.STROKE_NORMAL)
                    )
        self.add(self.rail)

        self.nodes = VGroup()
        for i, p in enumerate(pts):
            w, h = (host_size if i == self.HOST_INDEX else (2.2, 1.4))
            node = RoundedRectangle(
                width=w, height=h, corner_radius=theme.CORNER_RADIUS,
                fill_color=theme.BG_ELEVATED, fill_opacity=1.0,
                stroke_color=theme.TOKEN if i == self.HOST_INDEX else theme.FG_FAINT,
                stroke_width=theme.STROKE_NORMAL,
            ).move_to(p)
            self.nodes.add(node)
        self.add(self.nodes)

        self.host = self.nodes[self.HOST_INDEX]
        self.label = typography.text(
            "title", "TOKENIZER", frame_width=frame_width,
            color=theme.TOKEN, bold=True,
        )
        self.label.next_to(self.host, UP, buff=theme.PAD_MD)
        self.add(self.label)
