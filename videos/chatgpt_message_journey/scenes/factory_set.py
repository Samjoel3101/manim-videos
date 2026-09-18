"""The factory set: every location the camera visits, built once.

Separated from the choreography in `scene_factory.py` on purpose. A continuous
shot has two independent concerns — *where things are* and *when the camera goes
there* — and mixing them produces a scene file nobody can re-time.

World layout, left to right, all coordinates in Manim units:

    x=-22   chat window (user's screen)
    x=-13   web server
    x=-7…20 the LLM box, holding four stations at -4, 3, 10, 17
    y=-7    the return rail, carrying the finished token back to the chat

Everything is one closed loop, so the final pulled-back shot reads as a circuit
with tokens cycling rather than a line that stops.
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, VGroup

from lib import theme, utils
from lib.components.chat_ui import ChatWindow
from lib.components.factory import Conveyor, PipelineBox, Station
from lib.components.network import DeviceNode

# --- world anchors ---------------------------------------------------------
CHAT_X = -22.0
SERVER_X = -13.0
STATION_XS = (-4.0, 3.0, 10.0, 17.0)
RETURN_Y = -7.0

STATION_W, STATION_H = 6.4, 5.2


class FactorySet(VGroup):
    """Every mobject in the film, positioned. Built once, never torn down."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # -- the user's screen ------------------------------------------------
        self.chat = ChatWindow(width=6.4, height=6.0, title="ChatGPT")
        self.chat.move_to(np.array([CHAT_X, 0.0, 0.0]))

        # -- the web tier -----------------------------------------------------
        self.server = DeviceNode(
            "Web server",
            subtitle="api.openai.com",
            width=3.6,
            height=2.4,
            color=theme.NETWORK,
        )
        self.server.move_to(np.array([SERVER_X, 0.0, 0.0]))

        # -- the four stations inside the model -------------------------------
        self.tokenizer = Station(
            "Tokenizer",
            subtitle="text → ids",
            width=STATION_W,
            height=STATION_H,
            accent=theme.TOKEN,
            marquee="TOKENIZE",
        )
        self.embedder = Station(
            "Embedding",
            subtitle="ids → vectors",
            width=STATION_W,
            height=STATION_H,
            accent=theme.EMBED,
            marquee="EMBED",
        )
        self.transformer = Station(
            "Transformer",
            subtitle="96 layers",
            width=STATION_W,
            height=STATION_H,
            accent=theme.ATTENTION,
            marquee="ATTEND",
        )
        self.sampler = Station(
            "Sampling",
            subtitle="vector → token",
            width=STATION_W,
            height=STATION_H,
            accent=theme.PROB,
            marquee="SAMPLE",
        )

        self.stations = [self.tokenizer, self.embedder, self.transformer, self.sampler]
        for station, x in zip(self.stations, STATION_XS):
            station.move_to(np.array([x, 0.0, 0.0]))

        # -- the machine those stations live in -------------------------------
        self.llm = PipelineBox(
            self.stations,
            title="THE MODEL",
            subtitle="one forward pass",
            accent=theme.ASSISTANT,
        )

        # -- rails ------------------------------------------------------------
        self.rail_chat_to_server = Conveyor(
            [self.chat.get_right() + RIGHT * 0.3, self.server.get_left() + LEFT * 0.3],
            chevrons=2,
        )
        self.rail_server_to_llm = Conveyor(
            [self.server.get_right() + RIGHT * 0.3, self.llm.entry + LEFT * 0.3],
            chevrons=2,
        )
        self.rails_between_stations = VGroup(
            *[
                Conveyor(
                    [
                        self.stations[i].exit + RIGHT * 0.15,
                        self.stations[i + 1].entry + LEFT * 0.15,
                    ],
                    chevrons=1,
                )
                for i in range(len(self.stations) - 1)
            ]
        )

        # The finished token drops out of the model and runs home underneath.
        exit_x = self.llm.exit[0] + 1.2
        self.return_rail = Conveyor(
            [
                self.sampler.exit + RIGHT * 0.15,
                np.array([exit_x, 0.0, 0.0]),
                np.array([exit_x, RETURN_Y, 0.0]),
                np.array([SERVER_X, RETURN_Y, 0.0]),
                np.array([CHAT_X, RETURN_Y, 0.0]),
                self.chat.get_bottom() + DOWN * 0.3,
            ],
            color=theme.ASSISTANT,
            chevrons=5,
        )
        self.return_label = utils._text(
            "one token at a time", theme.SIZE_LABEL, theme.FG_MUTED, theme.FONT_BODY
        )
        self.return_label.scale(2.2)
        self.return_label.move_to(np.array([2.0, RETURN_Y - 1.4, 0.0]))
        self.return_label.set_opacity(0.0)

        # Draw order: rails behind the boxes they connect.
        self.add(
            self.rail_chat_to_server,
            self.rail_server_to_llm,
            self.rails_between_stations,
            self.return_rail,
            self.return_label,
            self.llm,
            *self.stations,
            self.server,
            self.chat,
        )

    # ------------------------------------------------------------------ paths
    def full_loop(self) -> Conveyor:
        """One rail tracing the entire circuit, for the fast cycles at the end.

        Built lazily rather than added to the set — it is a path to move along,
        not something the viewer should ever see drawn.
        """
        points = [
            self.chat.get_right() + RIGHT * 0.3,
            self.server.get_left() + LEFT * 0.3,
        ]
        points.append(self.server.get_right() + RIGHT * 0.3)
        for station in self.stations:
            points.append(station.get_center())
        points.extend(list(self.return_rail.path.get_anchors())[1:])
        rail = Conveyor(points)
        rail.set_opacity(0.0)
        return rail

    @property
    def everything(self) -> VGroup:
        """Used by the final pull-back to frame the whole factory."""
        return VGroup(self.chat, self.server, self.llm, self.return_rail)

    def reveal_marquees(self, opacity: float = 1.0):
        """Animations fading in the big station labels for the wide shot."""
        return [
            station.marquee.animate.set_opacity(opacity)
            for station in self.stations
            if station.marquee is not None
        ]
