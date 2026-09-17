"""Scene 1 — User Input.

"You type a sentence." Establishes the chat surface the whole video returns to,
and ends on the typing indicator that the rest of the pipeline explains.

Every visual here comes from lib/components/chat_ui.py; nothing in this file is
reusable enough to promote.
"""

from __future__ import annotations

from manim import DOWN, RIGHT, UP, FadeIn, FadeOut, Scene

from lib import theme, utils
from lib.components.chat_ui import ChatWindow, TypingIndicator

QUESTION = "How does ChatGPT work?"


class UserInput(Scene):
    def construct(self) -> None:
        theme.apply(self)

        window = ChatWindow(width=6.6, height=6.2, title="ChatGPT")
        window.shift(UP * theme.PAD_SM)
        self.play(FadeIn(window), run_time=theme.T_NORMAL)
        self.wait(theme.T_SLOW)

        # 1. The question types itself into the composer, character by character.
        #    Slow enough to read along with — this is the beat the viewer owns.
        window.input.type_animation(self, QUESTION, cps=11)
        self.wait(theme.T_SLOW)

        # 2. Enter. The typed text lifts out of the composer and lands as a
        #    right-aligned user bubble; the composer resets the way a real one does.
        ghost = window.input.text_mob.copy()
        self.add(ghost)

        bubble = window.commit(window.make_message(QUESTION, "user"))
        bubble.set_opacity(0)

        self.play(
            ghost.animate.move_to(bubble).set_opacity(0),
            bubble.animate.set_opacity(1),
            run_time=theme.T_NORMAL,
        )
        self.remove(ghost)

        # A real composer empties instantly on send, so this is a hard cut, not
        # an animation. (It also replaces the text mobject, which `.animate`
        # cannot interpolate across.)
        window.input.clear()
        self.wait(theme.T_BEAT)

        # 3. The assistant side starts thinking, in the left gutter where its
        #    bubble will eventually appear.
        thinking = TypingIndicator()
        thinking.next_to(bubble, DOWN, buff=theme.PAD_LG)
        left_gutter = window.frame.get_left()[0] + theme.PAD_MD * 2
        thinking.shift(RIGHT * (left_gutter - thinking.get_left()[0]))

        self.play(FadeIn(thinking), run_time=theme.T_FAST)
        thinking.pulse(self, cycles=4)

        # 4. The line that sets up the rest of the video.
        caption = utils.label("Everything after this point takes about two seconds.")
        utils.fit_text(caption, 10.0)
        caption.to_edge(DOWN, buff=theme.PAD_MD)

        self.play(FadeIn(caption, shift=UP * theme.PAD_SM), run_time=theme.T_NORMAL)
        thinking.pulse(self, cycles=3)
        self.wait(theme.T_SLOW)

        self.play(FadeOut(caption), run_time=theme.T_FAST)
        self.wait(theme.T_BEAT)
