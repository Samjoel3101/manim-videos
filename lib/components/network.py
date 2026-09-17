"""Network and transport visuals — the "your request leaves the device" layer.

Client, server, the link between them, and packets flying across it. Reused for
any video that has to show something travelling over a wire.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Dot,
    Line,
    MoveAlongPath,
    Rectangle,
    Succession,
    VGroup,
    Wait,
)

from lib import theme, utils


class DeviceNode(VGroup):
    """A labelled box standing for a machine: a laptop, a server, a GPU cluster."""

    def __init__(
        self,
        title: str,
        *,
        subtitle: str | None = None,
        width: float = 2.2,
        height: float = 1.4,
        color=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = color or theme.NETWORK
        self.box = utils.panel(
            width=width,
            height=height,
            fill=theme.BG_ELEVATED,
            stroke=self.accent,
            stroke_width=theme.STROKE_NORMAL,
        )
        self.title_mob = utils._text(title, theme.SIZE_LABEL, theme.FG, theme.FONT_BODY)
        utils.fit_text(self.title_mob, width - 2 * theme.PAD_SM)
        content = VGroup(self.title_mob)
        if subtitle:
            self.subtitle_mob = utils._text(
                subtitle, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            )
            utils.fit_text(self.subtitle_mob, width - 2 * theme.PAD_SM)
            content.add(self.subtitle_mob)
            content.arrange(DOWN, buff=theme.PAD_XS)
        content.move_to(self.box.get_center())
        self.add(self.box, content)


class ServerRack(VGroup):
    """A stack of slots standing for a datacentre — the model's end of the link."""

    def __init__(
        self,
        *,
        slots: int = 4,
        width: float = 1.6,
        slot_height: float = 0.3,
        label: str | None = "GPU cluster",
        color=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.accent = color or theme.ASSISTANT
        self.slots = VGroup(
            *[
                utils.panel(
                    width=width,
                    height=slot_height,
                    fill=theme.SURFACE,
                    stroke=self.accent,
                    radius=0.04,
                )
                for _ in range(slots)
            ]
        ).arrange(DOWN, buff=theme.PAD_XS)
        self.add(self.slots)
        self.label_mob = None
        if label:
            self.label_mob = utils._text(
                label, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_BODY
            ).next_to(self.slots, DOWN, buff=theme.PAD_SM)
            self.add(self.label_mob)


class Link(VGroup):
    """The wire between two nodes, optionally labelled (protocol, latency…)."""

    def __init__(
        self,
        start_mob,
        end_mob,
        *,
        label: str | None = None,
        color=None,
        dashed: bool = False,
        buff: float = theme.PAD_SM,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        color = color or theme.FG_FAINT
        start = start_mob.get_right() + RIGHT * buff
        end = end_mob.get_left() + LEFT * buff
        self.line = Line(
            start, end, stroke_color=color, stroke_width=theme.STROKE_NORMAL
        )
        if dashed:
            from manim import DashedLine

            self.line = DashedLine(
                start, end, stroke_color=color, stroke_width=theme.STROKE_NORMAL
            )
        self.add(self.line)
        self.label_mob = None
        if label:
            self.label_mob = utils._text(
                label, theme.SIZE_MICRO, theme.FG_MUTED, theme.FONT_MONO
            ).next_to(self.line, UP, buff=theme.PAD_XS)
            self.add(self.label_mob)

    @property
    def path(self) -> Line:
        return self.line


class Packet(Dot):
    """A single travelling dot. Use :meth:`flight` to animate it along a link."""

    def __init__(self, *, color=None, radius: float = 0.09, **kwargs) -> None:
        super().__init__(radius=radius, color=color or theme.NETWORK, **kwargs)

    def flight(self, link: Link, *, reverse: bool = False, run_time: float = theme.T_NORMAL):
        """Animation carrying this packet from one end of ``link`` to the other."""
        path = link.path.copy()
        if reverse:
            path.rotate(np.pi)
        self.move_to(path.get_start())
        return MoveAlongPath(self, path, run_time=run_time)


class PacketStream(VGroup):
    """Several packets crossing a link in sequence — a request or a token stream."""

    def __init__(self, count: int = 3, *, color=None, radius: float = 0.08, **kwargs) -> None:
        super().__init__(**kwargs)
        self.packets = VGroup(*[Packet(color=color, radius=radius) for _ in range(count)])
        self.add(self.packets)

    def flight(
        self,
        link: Link,
        *,
        reverse: bool = False,
        run_time: float = theme.T_SLOW,
        lag: float = 0.25,
    ):
        """Staggered flight of every packet across ``link``."""
        from manim import AnimationGroup

        per = run_time / max(1, len(self.packets))
        return AnimationGroup(
            *[p.flight(link, reverse=reverse, run_time=run_time) for p in self.packets],
            lag_ratio=lag,
        )


class RequestPath(VGroup):
    """The canonical client → internet → server row, ready to drop into a scene.

    This is the composition most "what happens when you send a message" scenes
    need; build it from here rather than re-wiring three nodes by hand.
    """

    def __init__(
        self,
        *,
        client_title: str = "Your device",
        server_title: str = "OpenAI datacentre",
        hop_title: str = "Internet",
        gap: float = 1.5,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.client = DeviceNode(client_title, subtitle="browser", color=theme.USER)
        self.hop = DeviceNode(hop_title, subtitle="TLS · HTTPS", color=theme.NETWORK)
        self.server = DeviceNode(server_title, subtitle="inference", color=theme.ASSISTANT)

        nodes = VGroup(self.client, self.hop, self.server).arrange(RIGHT, buff=gap)
        self.link_out = Link(self.client, self.hop, label="POST /chat")
        self.link_in = Link(self.hop, self.server, label="route")
        self.add(nodes, self.link_out, self.link_in)

    @property
    def links(self) -> list[Link]:
        return [self.link_out, self.link_in]


__all__ = ["DeviceNode", "ServerRack", "Link", "Packet", "PacketStream", "RequestPath"]
