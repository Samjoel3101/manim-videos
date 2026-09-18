"""The factory set: every location the camera visits, built once.

Separated from the choreography in `scene_factory.py` on purpose. A continuous
shot has two independent concerns — *where things are* and *when the camera goes
there* — and mixing them produces a scene file nobody can re-time.

Layout: one vertical column. The message falls straight down through the
machine and climbs back up the side.

                  ┌──────────┐
                  │   CHAT   │
                  └────┬─────┘
                       ↓
                  ┌──────────┐
                  │  SERVER  │
                  └────┬─────┘
                       ↓
           ┌──── THE MODEL ──────────┐
           │  ┌───────────────────┐  │ ┐
    TOKENIZE  │     Tokenizer     │  │ │
           │  └─────────┬─────────┘  │ │
           │  ┌─────────▼─────────┐  │ │
      EMBED   │     Embedding     │  │ │  return
           │  └─────────┬─────────┘  │ │   lane
           │  ┌─────────▼─────────┐  │ │    up
     ATTEND   │    Transformer    │  │ │   the
           │  └─────────┬─────────┘  │ │   side
           │  ┌─────────▼─────────┐  │ │
     SAMPLE   │     Sampling      │  │ │
           │  └─────────┬─────────┘  │ │
           └────────────┼────────────┘ │
                        └──────────────┘

Two consequences of the shape, both deliberate:

* A tall column in a 16:9 frame is **height-bound**, so the final pull-back is
  around 3x rather than the 2x a wide layout allows. That is the price of the
  vertical reading, and it is paid knowingly.
* It is affordable because type is sized *relative to the shot*
  (`lib/typography.py`), so wide-shot labels grow with the pull-back instead of
  shrinking into it. Fixed-size type is what made an earlier 3.6x cut
  illegible — not the zoom itself.

The column leaves the sides of a 16:9 frame empty, so station marquees sit
*beside* their bays rather than above them: it spends margin that would
otherwise be wasted, and keeps the stack short.
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, VGroup

from lib import effects, routing, theme, typography
from lib.components.chat_ui import ChatWindow
from lib.components.factory import Conveyor, PipelineBox, Station
from lib.components.glyph import IconTile

# --- shot sizes this set is designed for -----------------------------------
#: The close-up every station gets. Bays are wide and short, so this is
#: narrower than a square-bay layout would need.
SHOT_TIGHT = 11.0
#: The final pull-back. Marquees and the box title are sized against this, and
#: `validate()` fails if the real figure drifts away from it.
SHOT_WIDE = 45.5

# --- world anchors ---------------------------------------------------------
COLUMN_X = 0.0

STATION_W, STATION_H = 7.8, 2.4
STATION_GAP = 0.75

CHAT_H = 3.8
SERVER_SIZE = 2.2
#: Vertical breathing room between the chat, the server and the machine.
STACK_GAP = 1.0

#: How far out from the box the climb home runs.
RETURN_MARGIN = 1.6


class FactorySet(VGroup):
    """Every mobject in the film, positioned. Built once, never torn down."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # -- the four stations, stacked top to bottom -------------------------
        def station(title, subtitle, accent, icon, marquee):
            return Station(
                title,
                subtitle=subtitle,
                width=STATION_W,
                height=STATION_H,
                accent=accent,
                icon=icon,
                header_side="left",
                marquee=marquee,
                marquee_side="left",
                marquee_role="title",
                marquee_max_width=5.4,
                shot_width=SHOT_TIGHT,
                wide_width=SHOT_WIDE,
            )

        self.tokenizer = station(
            "Tokenizer", "text → ids", theme.TOKEN, "binary", "TOKENIZE"
        )
        self.embedder = station(
            "Embedding", "ids → vectors", theme.EMBED, "grid-3x3", "EMBED"
        )
        self.transformer = station(
            "Transformer", "96 layers", theme.ATTENTION, "layers", "ATTEND"
        )
        self.sampler = station(
            "Sampling", "vector → token", theme.PROB, "dices", "SAMPLE"
        )

        self.stations = [self.tokenizer, self.embedder, self.transformer, self.sampler]
        pitch = STATION_H + STATION_GAP
        top_y = (len(self.stations) - 1) * pitch / 2
        for i, st in enumerate(self.stations):
            target = np.array([COLUMN_X, top_y - i * pitch, 0.0])
            # Shift the whole station so its *bay* lands on the anchor; moving
            # the bay alone would leave the header and marquee behind.
            st.shift(target - st.bay.get_center())

        # -- the machine those stations live in -------------------------------
        # Built around the bays, not the whole stations: a marquee is a
        # wide-shot label that should sit beside the box, not inflate it.
        self.llm = PipelineBox(
            [st.bay for st in self.stations],
            title="THE MODEL",
            subtitle="one forward pass",
            accent=theme.ASSISTANT,
            pad=0.9,
            wide_width=SHOT_WIDE,
        )
        box_top = float(self.llm.frame.get_top()[1])
        box_bottom = float(self.llm.frame.get_bottom()[1])
        box_right = float(self.llm.frame.get_right()[0])

        # -- the user's screen and the web tier, stacked above ----------------
        self.server = IconTile(
            "server", label="web server", color=theme.NETWORK, size=SERVER_SIZE
        )
        server_y = box_top + STACK_GAP + SERVER_SIZE / 2
        self.server.shift(
            np.array([COLUMN_X, server_y, 0.0]) - self.server.tile.get_center()
        )

        self.chat = ChatWindow(width=6.0, height=CHAT_H, title="ChatGPT")
        chat_y = self.server.tile.get_top()[1] + STACK_GAP + CHAT_H / 2
        self.chat.move_to(np.array([COLUMN_X, chat_y, 0.0]))

        # -- rails: straight down the column ----------------------------------
        self.rail_chat_to_server = Conveyor(
            [
                self.chat.get_bottom() + DOWN * 0.25,
                self.server.tile.get_top() + UP * 0.25,
            ],
            chevrons=1,
        )
        self.rail_server_to_model = Conveyor(
            [
                self.server.tile.get_bottom() + DOWN * 0.25,
                np.array([COLUMN_X, box_top, 0.0]),
            ],
            chevrons=1,
        )
        self.rail_into_column = Conveyor(
            [
                np.array([COLUMN_X, box_top, 0.0]),
                self.tokenizer.bay.get_top() + UP * 0.05,
            ],
        )
        self.rails_between_stations = VGroup(
            *[
                Conveyor(
                    [
                        self.stations[i].bay.get_bottom() + DOWN * 0.05,
                        self.stations[i + 1].bay.get_top() + UP * 0.05,
                    ],
                    chevrons=1,
                )
                for i in range(len(self.stations) - 1)
            ]
        )
        self.rail_out_of_column = Conveyor(
            [
                self.sampler.bay.get_bottom() + DOWN * 0.05,
                np.array([COLUMN_X, box_bottom, 0.0]),
            ],
        )

        # -- the climb home, up the right-hand side ---------------------------
        return_x = box_right + RETURN_MARGIN
        below_y = box_bottom - 1.3
        self.return_rail = Conveyor(
            [
                np.array([COLUMN_X, box_bottom, 0.0]),
                np.array([COLUMN_X, below_y, 0.0]),
                np.array([return_x, below_y, 0.0]),
                np.array([return_x, chat_y, 0.0]),
                self.chat.get_right() + RIGHT * 0.25,
            ],
            color=theme.ASSISTANT,
            chevrons=4,
        )
        self.return_label = typography.text(
            "label",
            "one token at a time",
            frame_width=SHOT_WIDE,
            color=theme.FG_MUTED,
        )
        self.return_label.rotate(-np.pi / 2)
        self.return_label.move_to(
            np.array([return_x + 0.9, (below_y + chat_y) / 2, 0.0])
        )

        # -- glow halos -------------------------------------------------------
        # Pre-built and invisible. Lighting a node up is the house cue for "this
        # is running"; building the halos here means the choreography only ever
        # animates an opacity, and no beat pays to construct one mid-shot.
        self.server_glow = effects.glow(self.server.tile, theme.NETWORK)
        self.server_glow.set_opacity(0.0)
        self._glows = {}
        halos = VGroup(self.server_glow)
        for st in self.stations:
            halo = effects.glow(st.bay, st.accent)
            halo.set_opacity(0.0)
            self._glows[id(st)] = halo
            halos.add(halo)
        self.halos = halos

        # Wide-shot labels stay dark until the pull-back. At a close-up they
        # would be several times the size of anything else on screen.
        self.wide_labels = VGroup(self.llm.caption, self.return_label)
        self.wide_labels.set_opacity(0.0)

        self.add(
            halos,
            self.rail_chat_to_server,
            self.rail_server_to_model,
            self.rail_into_column,
            self.rails_between_stations,
            self.rail_out_of_column,
            self.return_rail,
            self.return_label,
            self.llm,
            *self.stations,
            self.server,
            self.chat,
        )

        self.validate()

    # ------------------------------------------------------------- validation
    def validate(self) -> None:
        """Assert the geometry the choreography depends on.

        Called at construction, so a layout mistake fails here rather than in a
        render three minutes later — or, worse, in a shipped video.

        Note what is deliberately *not* asserted: the descent passes through
        every station, because "it goes into tokenize, then into embed" is the
        whole reading a column is for. What must stay clear is the way home.
        """
        obstacles = [(st.title_mob.text, st.bay) for st in self.stations]
        obstacles += [
            ("the chat window", self.chat),
            ("the web server", self.server.tile),
        ]

        routing.assert_path_clears(self.return_rail, obstacles, ignore_ends=0.03)

        # The end-of-film loop is sampled once per frame and drawn with straight
        # chords, so a corner taken too fast can cut across something the path
        # itself misses. Checked at the frame budget the loop actually gets.
        routing.assert_trail_clears(self.return_rail, obstacles, steps=30)

        actual = self.wide_frame_width()
        drift = abs(actual - SHOT_WIDE) / SHOT_WIDE
        if drift > 0.12:
            raise AssertionError(
                f"SHOT_WIDE is {SHOT_WIDE:.1f} but the pull-back actually needs "
                f"{actual:.1f}. Wide-shot type is sized against SHOT_WIDE, so "
                "letting the two drift apart is exactly what makes labels come "
                "out the wrong size."
            )

    def wide_frame_width(self, pad: float = 1.0) -> float:
        """Camera width the final pull-back needs to frame everything.

        ``pad`` matches the value the scene passes to ``camera.frame_all``, so
        this prediction and the actual shot cannot drift apart.
        """
        group = self.everything
        return max(group.width + 2 * pad, (group.height + 2 * pad) * typography.ASPECT)

    # ------------------------------------------------------------------ paths
    def circuit(self):
        """The full loop, built by joining the rails the viewer can actually see.

        Built from the drawn rails rather than from node centres, so the travel
        path and the diagram cannot disagree — which is exactly how a token ended
        up flying through solid boxes in an earlier cut.
        """
        return routing.join(
            self.rail_chat_to_server,
            self.rail_server_to_model,
            self.rail_into_column,
            *self.descent_rails(),
            self.rail_out_of_column,
            self.return_rail,
        )

    def descent_rails(self) -> list:
        """The fall through the column, including the run inside each bay."""
        rails: list = []
        for i, st in enumerate(self.stations):
            rails.append(
                [st.bay.get_top() + UP * 0.05, st.bay.get_bottom() + DOWN * 0.05]
            )
            if i < len(self.stations) - 1:
                rails.append(self.rails_between_stations[i])
        return rails

    def tour_rails(self) -> list:
        """The in-machine rails, in pipeline order, for the close-up section."""
        return list(self.rails_between_stations)

    def glow_for(self, node) -> VGroup:
        """The pre-built halo for a station (or the server tile)."""
        if node is self.server:
            return self.server_glow
        try:
            return self._glows[id(node)]
        except KeyError:
            raise KeyError(f"no glow halo built for {node}") from None

    @property
    def everything(self) -> VGroup:
        """Used by the final pull-back to frame the whole factory."""
        return VGroup(
            self.chat,
            self.server,
            self.llm,
            self.return_rail,
            *[st.marquee for st in self.stations if st.marquee is not None],
        )

    @property
    def nodes(self) -> list:
        """Everything that can light up, in pipeline order."""
        return [self.server, *self.stations]

    def reveal_labels(self, opacity: float = 1.0):
        """Animations bringing up every wide-shot label for the pull-back."""
        return [
            *[
                st.marquee.animate.set_opacity(opacity)
                for st in self.stations
                if st.marquee is not None
            ],
            self.wide_labels.animate.set_opacity(opacity),
        ]
