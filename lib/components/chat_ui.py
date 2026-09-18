"""Chat interface primitives — the "product surface" end of an LLM explainer.

Reused wherever a video needs to show a human talking to a model: ChatGPT,
Claude, a support bot, an agent loop.
"""

from __future__ import annotations

from typing import Iterable

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    Dot,
    FadeIn,
    Line,
    Mobject,
    Rectangle,
    Succession,
    VGroup,
    Wait,
)

from lib import theme, utils


class ChatBubble(VGroup):
    """A single message bubble.

    Parameters
    ----------
    text:
        Message body. Wrapped to ``max_width`` automatically.
    sender:
        ``"user"`` or ``"assistant"`` — drives colour and alignment.
    max_width:
        Widest the bubble may grow before text wraps.
    """

    def __init__(
        self,
        text: str,
        sender: str = "user",
        *,
        max_width: float = 4.2,
        font_size: float = theme.SIZE_LABEL,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if sender not in ("user", "assistant"):
            raise ValueError("sender must be 'user' or 'assistant'")

        self.sender = sender
        accent = theme.USER if sender == "user" else theme.ASSISTANT

        self.text_mob = utils._text(
            text, font_size, theme.FG, theme.FONT_BODY, line_spacing=0.8
        )
        utils.fit_text(self.text_mob, max_width - 2 * theme.PAD_MD)

        self.body = utils.panel(
            width=self.text_mob.width + 2 * theme.PAD_MD,
            height=self.text_mob.height + 2 * theme.PAD_MD,
            fill=theme.SURFACE,
            stroke=accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        self.text_mob.move_to(self.body.get_center())
        self.add(self.body, self.text_mob)

    @property
    def accent(self):
        return theme.USER if self.sender == "user" else theme.ASSISTANT

    def set_text_opacity(self, opacity: float) -> "ChatBubble":
        self.text_mob.set_opacity(opacity)
        return self


class ChatInput(VGroup):
    """The composer box at the bottom of a chat window, with a caret.

    ``typed`` is what is already in the box; use :meth:`type_animation` to fill
    it character by character.
    """

    def __init__(
        self,
        placeholder: str = "Message ChatGPT…",
        *,
        width: float = 5.6,
        typed: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.full_text = typed
        self.box = utils.panel(
            width=width,
            height=0.62,
            fill=theme.SURFACE,
            stroke=theme.BORDER,
        )
        content = typed or placeholder
        self.text_mob = utils._text(
            content,
            theme.SIZE_LABEL,
            theme.FG if typed else theme.FG_FAINT,
            theme.FONT_BODY,
        )
        utils.fit_text(self.text_mob, width - 2 * theme.PAD_MD - 0.3)
        self.text_mob.next_to(self.box.get_left(), RIGHT, buff=theme.PAD_MD)

        self.caret = Line(
            UP * 0.13, DOWN * 0.13, stroke_color=theme.USER, stroke_width=theme.STROKE_NORMAL
        )
        self._place_caret()
        self.add(self.box, self.text_mob, self.caret)

    def _place_caret(self) -> None:
        anchor = self.text_mob if self.full_text else None
        if anchor is not None and anchor.width > 0:
            self.caret.next_to(anchor, RIGHT, buff=theme.PAD_XS)
        else:
            self.caret.next_to(self.box.get_left(), RIGHT, buff=theme.PAD_MD)

    def clear(self, placeholder: str = "Message ChatGPT…") -> "ChatInput":
        """Reset the composer to its empty placeholder state, in place.

        What a real composer does the instant a message is sent. Lives here
        rather than in a scene because every chat-driven video needs it.
        """
        self.remove(self.text_mob)
        self.full_text = ""
        self.text_mob = utils._text(
            placeholder, theme.SIZE_LABEL, theme.FG_FAINT, theme.FONT_BODY
        )
        utils.fit_text(self.text_mob, self.box.width - 2 * theme.PAD_MD - 0.3)
        self.text_mob.next_to(self.box.get_left(), RIGHT, buff=theme.PAD_MD)
        self.add(self.text_mob)
        self._place_caret()
        return self

    def type_animation(self, scene, text: str, *, cps: float = 18.0) -> None:
        """Type ``text`` into the box one character at a time, caret trailing."""
        per_char = 1.0 / cps
        for i in range(1, len(text) + 1):
            partial = utils._text(text[:i], theme.SIZE_LABEL, theme.FG, theme.FONT_BODY)
            utils.fit_text(partial, self.box.width - 2 * theme.PAD_MD - 0.3)
            partial.next_to(self.box.get_left(), RIGHT, buff=theme.PAD_MD)
            self.remove(self.text_mob)
            self.text_mob = partial
            self.full_text = text[:i]
            self.add(self.text_mob)
            self._place_caret()
            scene.wait(per_char)


class TypingIndicator(VGroup):
    """Three pulsing dots — the "model is thinking" beat."""

    def __init__(self, *, color=None, radius: float = 0.07, **kwargs) -> None:
        super().__init__(**kwargs)
        color = color or theme.ASSISTANT
        self.dots = VGroup(
            *[Dot(radius=radius, color=color, fill_opacity=0.45) for _ in range(3)]
        ).arrange(RIGHT, buff=theme.PAD_SM)
        self.add(self.dots)

    def pulse(self, scene, *, cycles: int = 2, beat: float = 0.16) -> None:
        for _ in range(cycles):
            for dot in self.dots:
                scene.play(dot.animate.set_opacity(1.0), run_time=beat * 0.5)
                scene.play(dot.animate.set_opacity(0.45), run_time=beat * 0.5)


class StreamingBubble(VGroup):
    """An assistant bubble whose text arrives a word at a time.

    The bubble is laid out at its *final* size immediately and words are then
    revealed progressively, so it never reflows mid-stream — which is what a
    real streaming UI does, and what stops the animation jittering.

    The text is built as a **single** ``Text`` mobject with explicit line breaks
    rather than one mobject per word. Per-word mobjects get vertically centred
    by ``arrange``, so a word with a descender ("your") sits visibly higher than
    its neighbours; letting Pango lay out the whole block keeps every word on a
    common baseline. Words are then addressed by glyph range.

    Reveal with :meth:`reveal`, or animate it: ``bubble.animate.reveal(n)``.
    """

    def __init__(
        self,
        text: str,
        *,
        sender: str = "assistant",
        max_width: float = 4.4,
        font_size: float = theme.SIZE_LABEL,
        line_spacing: float = 0.9,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if sender not in ("user", "assistant"):
            raise ValueError("sender must be 'user' or 'assistant'")
        self.sender = sender
        accent = theme.USER if sender == "user" else theme.ASSISTANT

        word_list = text.split()
        if not word_list:
            raise ValueError("StreamingBubble needs at least one word")

        wrapped = self._wrap(word_list, max_width - 2 * theme.PAD_MD, font_size)
        self.text_mob = utils._text(
            "\n".join(" ".join(line) for line in wrapped),
            font_size,
            theme.FG,
            theme.FONT_BODY,
            line_spacing=line_spacing,
        )
        # The greedy wrap measures words in isolation; Pango's kerning across a
        # space can push a line a hair wider. Clamp so max_width is a guarantee.
        utils.fit_text(self.text_mob, max_width - 2 * theme.PAD_MD)

        # Text drops whitespace, so glyph i of the mobject is glyph i of the
        # concatenated words. Map each word to its glyph slice.
        self.words = VGroup()
        cursor = 0
        glyphs = list(self.text_mob)
        for word in word_list:
            nxt = min(cursor + len(word), len(glyphs))
            self.words.add(VGroup(*glyphs[cursor:nxt]))
            cursor = nxt

        self.lines = VGroup()
        cursor = 0
        for line in wrapped:
            span = sum(len(w) for w in line)
            nxt = min(cursor + span, len(glyphs))
            self.lines.add(VGroup(*glyphs[cursor:nxt]))
            cursor = nxt

        self.body = utils.panel(
            width=self.text_mob.width + 2 * theme.PAD_MD,
            height=self.text_mob.height + 2 * theme.PAD_MD,
            fill=theme.SURFACE,
            stroke=accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        self.text_mob.move_to(self.body.get_center())
        self.add(self.body, self.text_mob)

        self.revealed = 0
        self.text_mob.set_opacity(0.0)

    @staticmethod
    def _wrap(words, inner_width: float, font_size: float):
        """Greedy word wrap, measuring real rendered widths."""
        lines, current, used = [], [], 0.0
        space = utils._text("x x", font_size, theme.FG, theme.FONT_BODY).width
        space -= 2 * utils._text("x", font_size, theme.FG, theme.FONT_BODY).width
        space = max(space, 0.05)
        for word in words:
            width = utils._text(word, font_size, theme.FG, theme.FONT_BODY).width
            advance = width + (space if current else 0.0)
            if current and used + advance > inner_width:
                lines.append(current)
                current, used, advance = [], 0.0, width
            current.append(word)
            used += advance
        if current:
            lines.append(current)
        return lines

    @property
    def word_count(self) -> int:
        return len(self.words)

    def reveal(self, count: int) -> "StreamingBubble":
        """Show the first ``count`` words. Clamped to the available range."""
        count = max(0, min(count, self.word_count))
        for i, word in enumerate(self.words):
            word.set_opacity(1.0 if i < count else 0.0)
        self.revealed = count
        return self

    def reveal_next(self, step: int = 1) -> "StreamingBubble":
        return self.reveal(self.revealed + step)


class ChatWindow(VGroup):
    """A framed chat surface: title bar, message area, composer.

    Messages are added with :meth:`add_message`, which handles alignment,
    stacking and scroll-off when the transcript overflows.
    """

    def __init__(
        self,
        *,
        width: float = 6.4,
        height: float = 6.0,
        title: str = "ChatGPT",
        show_input: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.win_width = width
        self.win_height = height

        self.frame = utils.panel(width=width, height=height, fill=theme.BG_ELEVATED)
        self.title_mob = utils.label(title).set_color(theme.FG)
        self.title_mob.next_to(self.frame.get_top(), DOWN, buff=theme.PAD_MD)
        self.divider = Line(
            self.frame.get_left(),
            self.frame.get_right(),
            stroke_color=theme.BORDER,
            stroke_width=theme.STROKE_HAIRLINE,
        ).next_to(self.title_mob, DOWN, buff=theme.PAD_SM)

        self.messages = VGroup()
        self.add(self.frame, self.title_mob, self.divider, self.messages)

        self.input = None
        if show_input:
            self.input = ChatInput(width=width - 2 * theme.PAD_MD)
            self.input.next_to(self.frame.get_bottom(), UP, buff=theme.PAD_MD)
            self.add(self.input)

    @property
    def message_max_width(self) -> float:
        return self.win_width * 0.72

    @property
    def message_area_height(self) -> float:
        """Vertical room a single bubble has between the divider and composer.

        A bubble taller than this cannot be shown: scrolling it clear of the
        composer pushes its top past the divider, and a message whose top is
        above the divider is hidden (there is no clipping mask). So callers
        building their own bubble — a :class:`StreamingBubble`, typically —
        size it against this rather than guessing, which is what had a
        four-line reply hanging out of the bottom of the window and across
        everything drawn below it.
        """
        return float(
            self._top_of_message_area()[1] - self._bottom_of_message_area()
        )

    def _top_of_message_area(self):
        return self.divider.get_bottom() + DOWN * theme.PAD_MD

    def _bottom_of_message_area(self):
        """Lowest y a bubble may occupy without colliding with the composer."""
        if self.input is not None:
            return self.input.get_top()[1] + theme.PAD_MD
        return self.frame.get_bottom()[1] + theme.PAD_MD

    def place(self, bubble: Mobject, sender: str = "user") -> Mobject:
        """Position ``bubble`` where the next message in this transcript goes.

        Split out of :meth:`make_message` so a bubble the caller built itself —
        a :class:`StreamingBubble`, say — lands in the transcript flow and the
        window's gutters instead of being positioned by hand near the window.
        Hand-placing is what let a reply escape the frame entirely.
        """
        if sender not in ("user", "assistant"):
            raise ValueError("sender must be 'user' or 'assistant'")

        if len(self.messages) == 0:
            bubble.next_to(self._top_of_message_area(), DOWN, buff=0)
        else:
            bubble.next_to(self.messages[-1], DOWN, buff=theme.PAD_MD)

        # Horizontal alignment: user hugs the right gutter, assistant the left.
        if sender == "user":
            target_x = self.frame.get_right()[0] - theme.PAD_MD
            bubble.shift(RIGHT * (target_x - bubble.get_right()[0]))
        else:
            target_x = self.frame.get_left()[0] + theme.PAD_MD
            bubble.shift(RIGHT * (target_x - bubble.get_left()[0]))
        return bubble

    def post(self, bubble: Mobject, sender: str = "user") -> Mobject:
        """Place an externally built bubble and attach it to the transcript."""
        return self.commit(self.place(bubble, sender))

    def make_message(self, text: str, sender: str = "user") -> ChatBubble:
        """Build a correctly sized and positioned bubble without adding it yet.

        Useful when a scene wants to animate the bubble in itself; call
        :meth:`commit` afterwards so later messages stack below it.
        """
        return self.place(
            ChatBubble(text, sender, max_width=self.message_max_width), sender
        )

    def commit(self, bubble: ChatBubble) -> ChatBubble:
        """Attach an already-built bubble to the transcript, scrolling if needed."""
        self.messages.add(bubble)
        self._scroll_into_view(bubble)
        return bubble

    def _scroll_into_view(self, bubble: ChatBubble) -> None:
        """Push the transcript up if the newest bubble would hit the composer.

        Manim has no cheap clipping mask, so bubbles that scroll past the top of
        the message area are hidden rather than drawn over the title bar.
        """
        overflow = self._bottom_of_message_area() - bubble.get_bottom()[1]
        if overflow > 0:
            self.messages.shift(UP * overflow)
        self._hide_scrolled_off()

    def _hide_scrolled_off(self) -> None:
        ceiling = self._top_of_message_area()[1]
        for message in self.messages:
            visible = message.get_top()[1] <= ceiling + 1e-6
            message.set_opacity(1.0 if visible else 0.0)

    def visible_messages(self) -> VGroup:
        """Messages currently inside the message area (i.e. not scrolled off)."""
        ceiling = self._top_of_message_area()[1]
        return VGroup(*[m for m in self.messages if m.get_top()[1] <= ceiling + 1e-6])

    def add_message(self, text: str, sender: str = "user") -> ChatBubble:
        """Append a message bubble and return it."""
        return self.commit(self.make_message(text, sender))

    def add_messages(self, items: Iterable[tuple[str, str]]) -> VGroup:
        return VGroup(*[self.add_message(text, sender) for text, sender in items])


__all__ = [
    "ChatWindow",
    "ChatBubble",
    "ChatInput",
    "StreamingBubble",
    "TypingIndicator",
]
