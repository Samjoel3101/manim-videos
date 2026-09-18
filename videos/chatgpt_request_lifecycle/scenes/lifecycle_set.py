"""The lifecycle set: every location the camera visits, built once.

Separated from the choreography in `scene_lifecycle.py` for the reason the house
format always separates them: a 45-second uncut take is ~90 animations whose
timings all depend on each other, and if the geometry is interleaved with them,
re-timing one beat means re-deriving positions. Nobody does that twice.

Layout: **one clockwise circuit around a 16:9-shaped world.** Out along the top
band, down the right-hand side into the machine, back along the bottom band, and
up the left margin to the client. The previous film (`chatgpt_message_journey`)
was a single vertical column, which is height-bound and reaches about 3.3x at
the pull-back; this one has nine stations to place, so it spends the width a
16:9 frame gives it and the four bands read as the four stages of a request.

```
   CLIENT ──▶ [✓] ──▶  EDGE  ──▶ GATEWAY ──▶ ORCHESTRATOR      band y = +9
  (−24,+9)   bot     (−8,+9)     (+5,+9)      (+18,+9)
     ▲      check                                  │
     │     (−16,+9)                                ▼
     │                          ┌─ THE INFERENCE STACK ─┐      column x = +18
     │                          │  TOKENIZER    (+18, +0.85)
     │                          │  PREFILL·KV   (+18, −1.85)
     │                          │  DECODE LOOP  (+18, −4.55)
     │                          │  SAMPLER      (+18, −7.25)
     │                          └───────────┬───────────┘
     │                                      ▼
     └───────────◀──────────── STREAM BACK ◀┘                  band y = −12
   x = −30.5       │            (+5,−12)
                   ▼ fan-out spur
                 AFTER  (−20,−16)                              epilogue
```

Three things about this shape are decisions rather than accidents:

* **The model box is a vertical column inside a `PipelineBox`, deliberately
  echoing the previous film.** Same four accents, same order. A returning viewer
  should recognise the machine in the middle as the one they already walked
  through, now seen in context — which is the entire reason this is a second
  video rather than an edit of the first.
* **The way home runs down the far left margin, not back through the bands.** A
  return rail threaded between the machines would have to dodge nine of them,
  and every dodge reads as the payload taking a detour it has no reason to take.
  The empty left margin is free, and `validate()` asserts it stays clear.
* **The after-response bay hangs below the bottom band on a spur**, in
  `theme.FG_FAINT`, because what goes down it is a *copy* for the ledger, not the
  answer. Putting it on the main line would say the reply goes via billing.

Each bay carries two names and shows exactly one of them, exactly as the
reference set does: the close-up header (icon, title, subtitle) sized for
`SHOT_TIGHT`/`SHOT_TIGHT_OUTER` and living in the bay's left third, and the
pull-back `wide_label` sized for `SHOT_WIDE` and filling the bay. The pull-back
cross-fades one for the other. Two labels lit at once was tried in an earlier
video and removed — they overlap, and the opacity dance that swaps them fights
anything else animating the same group. A single compromise size was tried too,
and it starved the close-up's content slot, which is the thing the beat is
actually about.

`marquee=` is deliberately not used. It hangs a label *beside* the bay, and with
ten stations on four bands there is no side that is reliably empty.
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, LEFT, RIGHT, UP, VGroup

from lib import effects, routing, theme, typography
from lib.components.chat_ui import ChatWindow
from lib.components.factory import Conveyor, PipelineBox, Station
from lib.components.glyph import IconTile

# --- shot sizes this set is designed for -----------------------------------
#: The close-up an in-box bay gets. A 9.6-wide bay at 16:9 gives 7.64 of frame
#: height here, which clears the bay (2.1) plus a caption under it plus the top
#: and bottom of its neighbours — the viewer keeps their bearings inside the
#: column without the camera having to pull out.
SHOT_TIGHT = 13.6

#: The close-up a band station gets. The bays out here are 10.0 wide rather than
#: 9.6, and the beat usually has the *next* machine's edge in frame so the pan
#: has somewhere to go, so this is a step wider.
SHOT_TIGHT_OUTER = 16.0

#: The final pull-back. Every wide-shot label is sized against this, and
#: :meth:`LifecycleSet.validate` fails at construction if the real figure drifts
#: more than 12% from it — because the labels would then be the wrong size and
#: nothing else would say so.
SHOT_WIDE = 58.0

#: How long one end-of-film loop takes. It lives HERE rather than in the scene
#: because `validate()` budgets its chord-clearance assertion against it: a
#: comet is sampled once per frame and joined with straight chords, so a faster
#: loop cuts corners harder. Keeping the number in one place is what stops the
#: assertion silently checking a shot that no longer exists.
LOOP_RUN_TIME = 1.35

#: Frame rate the chord budget is computed at. The house convention (see the
#: reference set) is 30 — the `preview` profile — rather than the 15 of the test
#: profile, because a draft render is not what ships.
LOOP_FPS = 30

# --- world anchors ---------------------------------------------------------
#: The machine's vertical midline. Everything in the column hangs off it, and it
#: is also the orchestrator's x, so the payload turns exactly one corner on its
#: way into the box.
COLUMN_X = 18.0
BAND_TOP_Y = 9.0
BAND_BOT_Y = -12.0

#: Band stations are wide and short: there is no vertical room for a stacked
#: header out here, so they all use `header_side="left"`.
SERVICE_W, SERVICE_H = 10.0, 2.8
#: The epilogue bay, one size down — it is an aside, and reads as one.
AFTER_W, AFTER_H = 10.0, 2.4
#: The four in-box bays. Narrower than a band bay so the box around them stays
#: inside the column without crowding the orchestrator above it.
BAY_W, BAY_H = 9.6, 2.1
BAY_PITCH = 2.7  # BAY_H + 0.6

#: The chat has to hold the question AND the finished four-line reply inside its
#: frame at the same time. At 6.4 tall it does not: `ChatWindow` scrolls the
#: transcript to keep the newest message clear of the composer and then hides
#: anything pushed past the top (there is no clipping mask), so the question the
#: whole film is about silently disappeared at the exact moment the answer
#: landed. Measured, not guessed: question 1.30 + PAD_MD + reply 1.67 = 3.47,
#: and `message_area_height` is 3.29 at 6.4 and 3.89 at 7.0.
CHAT_W, CHAT_H = 9.6, 7.0
CHECK_SIZE = 1.8

#: How far left the climb home runs. Left of the chat AND left of the after bay,
#: with room to spare, so the rail never grazes either — asserted in validate().
RETURN_X = -30.5


class LifecycleSet(VGroup):
    """Every mobject in the film, positioned. Built once, never torn down."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # -- the client -------------------------------------------------------
        self.chat = ChatWindow(width=CHAT_W, height=CHAT_H, title="ChatGPT")
        self.chat.move_to(np.array([-24.0, BAND_TOP_Y, 0.0]))

        # A tile rather than a Station: the proof-of-work check is a gate, not a
        # machine with a slot full of content, and drawing it the same size as
        # the Edge tier would overstate it.
        self.bot_check = IconTile(
            "hash", label="bot check", color=theme.WARN, size=CHECK_SIZE
        )
        self.bot_check.shift(
            np.array([-16.0, BAND_TOP_Y, 0.0]) - self.bot_check.tile.get_center()
        )

        # -- the four band stations -------------------------------------------
        def band_station(title, subtitle, accent, icon, *, height=SERVICE_H,
                         width=SERVICE_W):
            return Station(
                title,
                subtitle=subtitle,
                width=width,
                height=height,
                accent=accent,
                icon=icon,
                # No vertical room for a stacked header in a 2.8-tall bay; a
                # top header collapses the slot to nothing (HEADER_SHARE exists
                # for exactly this, see lib/components/factory.py).
                header_side="left",
                shot_width=SHOT_TIGHT_OUTER,
                wide_label=title,
                wide_width=SHOT_WIDE,
            )

        self.edge = band_station(
            "Edge", "WAF · bot score · rate limit", theme.NETWORK, "cloud"
        )
        self.gateway = band_station(
            "Gateway", "auth · entitlements · quota", theme.WARN, "lock"
        )
        self.orchestrator = band_station(
            "Orchestrator", "context · prompt · routing", theme.ASSISTANT, "database"
        )
        self.stream = band_station(
            "Stream back", "detokenise · safety · SSE", theme.ASSISTANT, "activity"
        )
        self.after = band_station(
            "After the response", "persist · bill · async jobs", theme.NETWORK,
            "git-branch", height=AFTER_H, width=AFTER_W,
        )

        # -- the four in-box bays ---------------------------------------------
        # The accents are EXACTLY the previous film's four, in the same order.
        # Same machine, seen in context — see the module docstring.
        def bay_station(title, subtitle, accent, icon):
            return Station(
                title,
                subtitle=subtitle,
                width=BAY_W,
                height=BAY_H,
                accent=accent,
                icon=icon,
                header_side="left",
                shot_width=SHOT_TIGHT,
                wide_label=title,
                wide_width=SHOT_WIDE,
            )

        self.tokenizer = bay_station("Tokenizer", "text → ids", theme.TOKEN, "binary")
        self.prefill = bay_station(
            "Prefill · KV cache", "reuse the prefix", theme.EMBED, "grid-3x3"
        )
        self.decode = bay_station(
            "Decode loop", "one token per step", theme.ATTENTION, "cpu"
        )
        self.sampler = bay_station("Sampling", "logits → one token", theme.PROB, "dices")
        self.in_box_stations = [
            self.tokenizer, self.prefill, self.decode, self.sampler
        ]

        # -- position everything by its BAY, not by its group ------------------
        # Shifting the bay alone would leave the header and the wide label
        # behind; shifting the group would land the bay wherever the group's
        # bounding box happens to centre, which depends on how long the title is.
        placements = [
            (self.edge, (-8.0, BAND_TOP_Y)),
            (self.gateway, (5.0, BAND_TOP_Y)),
            (self.orchestrator, (COLUMN_X, BAND_TOP_Y)),
            (self.stream, (5.0, BAND_BOT_Y)),
            (self.after, (-20.0, -16.0)),
            (self.tokenizer, (COLUMN_X, 0.85)),
            (self.prefill, (COLUMN_X, -1.85)),
            (self.decode, (COLUMN_X, -4.55)),
            (self.sampler, (COLUMN_X, -7.25)),
        ]
        for station, (x, y) in placements:
            station.shift(np.array([x, y, 0.0]) - station.bay.get_center())

        # -- the machine those four bays live in -------------------------------
        # Built around the BAYS, not the whole stations: a station's group also
        # contains its wide label, and enclosing that would inflate the box for
        # no visual gain.
        self.llm = PipelineBox(
            [st.bay for st in self.in_box_stations],
            title="THE INFERENCE STACK",
            accent=theme.ASSISTANT,
            pad=0.9,
            # One step down from `title`: at the pull-back this names a machine,
            # it does not headline the film.
            title_role="heading",
            # Down the empty side margin. A tall box fed from above has a rail
            # coming down its midline, and a name sized for the pull-back is
            # about as wide as the box, so a top title and the rail want the
            # same space. Stopping the rail short of the words is the trap the
            # previous film fell into: the title is a wide-shot label that stays
            # dark through every close-up, so all the viewer saw for 25 seconds
            # was an arrow ending in nothing.
            title_side="side",
            wide_width=SHOT_WIDE,
        )
        # DERIVED, never hardcoded. The expected values are in script.md and are
        # checked by validate(); if PipelineBox's padding changes, these follow
        # and the assertions catch anything that no longer fits.
        box_top = float(self.llm.frame.get_top()[1])
        box_bottom = float(self.llm.frame.get_bottom()[1])

        # -- rails -------------------------------------------------------------
        # Every rail is built from the SHAPES (`tile`, `bay`) rather than the
        # groups, because a group's bounding box includes its caption and its
        # anchors move when the caption does. Travel direction is carried by the
        # point order, which is what orients the chevrons.
        self.rail_chat_to_check = Conveyor(
            [
                self.chat.get_right() + RIGHT * 0.25,
                self.bot_check.tile.get_left() + LEFT * 0.25,
            ],
            chevrons=1,
        )
        self.rail_check_to_edge = Conveyor(
            [
                self.bot_check.tile.get_right() + RIGHT * 0.25,
                self.edge.bay.get_left() + LEFT * 0.05,
            ],
            chevrons=1,
        )
        self.rail_edge_to_gateway = Conveyor(
            [
                self.edge.bay.get_right() + RIGHT * 0.05,
                self.gateway.bay.get_left() + LEFT * 0.05,
            ],
            chevrons=1,
        )
        self.rail_gateway_to_orch = Conveyor(
            [
                self.gateway.bay.get_right() + RIGHT * 0.05,
                self.orchestrator.bay.get_left() + LEFT * 0.05,
            ],
            chevrons=1,
        )
        # The corner where the request stops being a web request and starts
        # being a forward pass. It leaves the orchestrator downward, which is
        # why the orchestrator's in-bay run is L-shaped (see `circuit`).
        self.rail_orch_to_box = Conveyor(
            [
                self.orchestrator.bay.get_bottom() + DOWN * 0.05,
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
                        self.in_box_stations[i].bay.get_bottom() + DOWN * 0.05,
                        self.in_box_stations[i + 1].bay.get_top() + UP * 0.05,
                    ],
                    chevrons=1,
                )
                for i in range(len(self.in_box_stations) - 1)
            ]
        )
        self.rail_out_of_column = Conveyor(
            [
                self.sampler.bay.get_bottom() + DOWN * 0.05,
                np.array([COLUMN_X, box_bottom, 0.0]),
            ],
        )
        # From here on the rails are ASSISTANT green: this is the reply path,
        # and colouring it is what lets the pull-back read as a loop with a
        # direction rather than a wiring diagram.
        self.rail_box_to_stream = Conveyor(
            [
                np.array([COLUMN_X, box_bottom, 0.0]),
                np.array([COLUMN_X, BAND_BOT_Y, 0.0]),
                self.stream.bay.get_right() + RIGHT * 0.05,
            ],
            color=theme.ASSISTANT,
            chevrons=2,
        )
        self.rail_stream_home = Conveyor(
            [
                self.stream.bay.get_left() + LEFT * 0.05,
                np.array([RETURN_X, BAND_BOT_Y, 0.0]),
                np.array([RETURN_X, BAND_TOP_Y, 0.0]),
                self.chat.get_left() + LEFT * 0.25,
            ],
            color=theme.ASSISTANT,
            chevrons=4,
        )
        # Faint, because what goes down here is a COPY for the ledger. Drawing
        # it in the reply's green would say the answer travels via billing.
        self.rail_after_spur = Conveyor(
            [
                np.array([-20.0, BAND_BOT_Y, 0.0]),
                self.after.bay.get_top() + UP * 0.05,
            ],
            color=theme.FG_FAINT,
            chevrons=1,
        )

        # Reads bottom-to-top up the left margin, balancing the box's side title
        # in the opposite margin. It names the long climb home, which is the one
        # stretch of the circuit with no station on it to explain itself.
        self.return_label = typography.text(
            "label",
            "one token at a time",
            frame_width=SHOT_WIDE,
            color=theme.FG_MUTED,
        )
        self.return_label.rotate(np.pi / 2)
        self.return_label.move_to(np.array([RETURN_X - 1.1, -1.5, 0.0]))

        # -- glow halos --------------------------------------------------------
        # Pre-built and invisible. Lighting a node is the house cue for "this is
        # running"; building the halos here means the choreography only ever
        # animates an opacity and no beat pays to construct twelve stroked
        # copies mid-shot.
        #
        # STROKE opacity only. `set_opacity` would raise the copies' FILL too,
        # turning a dozen transparent outlines into a dozen opaque plates that
        # bury everything inside the bay. That bug has been paid for twice in
        # this repo (sessions 5 and 6) and both times it presented as "the
        # labels went grey" rather than as what it was.
        self._glows: dict[int, VGroup] = {}
        halos = VGroup()
        self.check_glow = effects.glow(self.bot_check.tile, theme.WARN)
        self.check_glow.set_stroke(opacity=0.0)
        self._glows[id(self.bot_check)] = self.check_glow
        halos.add(self.check_glow)
        for station in self._stations():
            halo = effects.glow(station.bay, station.accent)
            halo.set_stroke(opacity=0.0)
            self._glows[id(station)] = halo
            halos.add(halo)
        self.halos = halos

        #: Residual glow once the pull-back is running. Lower than the previous
        #: film's 0.18 because there are ten lit rectangles here rather than
        #: five, and ten bright ones at once is noise rather than emphasis.
        self.resting_glow = 0.16

        # Wide-shot labels stay dark until the pull-back: at a close-up they are
        # several times the size of anything else on screen.
        self.wide_labels = VGroup(self.llm.caption, self.return_label)
        self.wide_labels.set_opacity(0.0)

        self.add(
            halos,
            self.rail_chat_to_check,
            self.rail_check_to_edge,
            self.rail_edge_to_gateway,
            self.rail_gateway_to_orch,
            self.rail_orch_to_box,
            self.rail_into_column,
            self.rails_between_stations,
            self.rail_out_of_column,
            self.rail_box_to_stream,
            self.rail_stream_home,
            self.rail_after_spur,
            self.return_label,
            self.llm,
            *self._stations(),
            self.bot_check,
            self.chat,
        )

        self.validate()

    # ------------------------------------------------------------- inventory
    def _stations(self) -> list:
        """Every `Station` in flow order. Not the bot check — that is a tile."""
        return [
            self.edge,
            self.gateway,
            self.orchestrator,
            *self.in_box_stations,
            self.stream,
            self.after,
        ]

    @property
    def nodes(self) -> list:
        """Everything that can light up, in flow order."""
        return [
            self.bot_check,
            self.edge,
            self.gateway,
            self.orchestrator,
            self.tokenizer,
            self.prefill,
            self.decode,
            self.sampler,
            self.stream,
            self.after,
        ]

    # ------------------------------------------------------------- validation
    def validate(self) -> None:
        """Assert the geometry the choreography depends on.

        Called from ``__init__``, so a layout mistake fails here rather than in
        a render three minutes later — or, worse, in a shipped video.

        Note what is deliberately *not* asserted: the descent through the column
        passes straight through all four in-box bays, because "it goes into
        tokenize, then into prefill" is the whole reading a column is for. What
        must stay clear is the way home and the fan-out spur.
        """
        obstacles = [(st.title_mob.text, st.bay) for st in self._stations()]
        obstacles += [
            ("the chat window", self.chat),
            ("the bot check", self.bot_check.tile),
            ("the inference stack", self.llm.frame),
        ]

        # 1. The climb home must go AROUND everything, not through it.
        routing.assert_path_clears(
            self.rail_stream_home, obstacles, ignore_ends=0.03
        )

        # 2. And the CHORDS it is drawn with must too. A comet is sampled once
        #    per frame and joined with straight segments, so a corner taken too
        #    fast cuts across things the underlying path never touches — which
        #    `path_clears` cannot see, because it walks the true curve. Budget
        #    the check at the frames this stretch actually receives: the loop
        #    runs the WHOLE circuit in LOOP_RUN_TIME, so the way home gets its
        #    share of those frames, not all of them.
        total_frames = LOOP_FPS * LOOP_RUN_TIME
        circuit_len = routing.length(self.circuit())
        home_len = routing.length(self.rail_stream_home)
        home_frames = max(6, int(total_frames * home_len / circuit_len))
        routing.assert_trail_clears(
            self.rail_stream_home, obstacles, steps=home_frames, ignore_ends=0.05
        )

        # 3. The fan-out spur, same treatment.
        routing.assert_path_clears(
            self.rail_after_spur, obstacles, ignore_ends=0.05
        )

        # 4. Band separation. Each of these is a specific way the layout can
        #    collapse, and a generic "nothing overlaps" check would not say
        #    which one happened or what to do about it.
        box_top = float(self.llm.frame.get_top()[1])
        box_bottom = float(self.llm.frame.get_bottom()[1])
        for station in (self.edge, self.gateway, self.orchestrator):
            clearance = float(station.bay.get_bottom()[1]) - box_top
            if clearance < 1.0:
                raise AssertionError(
                    f"the {station.title_mob.text} bay sits {clearance:.2f} above "
                    "the inference stack, which is under the 1.0 minimum. The "
                    "top band and the box would read as one machine at the "
                    "pull-back. Raise BAND_TOP_Y or shorten the column."
                )
        stream_gap = box_bottom - float(self.stream.bay.get_top()[1])
        if stream_gap < 1.0:
            raise AssertionError(
                f"the box bottom is only {stream_gap:.2f} above the stream bay. "
                "The rail out of the column needs visible run before it turns. "
                "Lower BAND_BOT_Y or shorten the column."
            )
        after_drop = BAND_BOT_Y - float(self.after.bay.get_top()[1])
        if after_drop < 1.5:
            raise AssertionError(
                f"the after bay's top is only {after_drop:.2f} below the bottom "
                "band, so the return rail at y={BAND_BOT_Y} would run through "
                "it. Move the after bay further down."
            )
        for name, edge in (
            ("the chat window", float(self.chat.get_left()[0])),
            ("the after bay", float(self.after.bay.get_left()[0])),
        ):
            if edge - RETURN_X < 1.0:
                raise AssertionError(
                    f"RETURN_X={RETURN_X} is only {edge - RETURN_X:.2f} left of "
                    f"{name}. The climb home would graze it — and a comet's "
                    "chords reach further than the rail does. Move RETURN_X "
                    "left."
                )

        # 5. Zoom budget. Wide-shot type is sized against SHOT_WIDE, so letting
        #    the constant and the real pull-back drift apart is exactly what
        #    makes labels come out the wrong size — with nothing else to say so.
        actual = self.wide_frame_width()
        drift = abs(actual - SHOT_WIDE) / SHOT_WIDE
        if drift > 0.12:
            raise AssertionError(
                f"SHOT_WIDE is {SHOT_WIDE:.1f} but the pull-back actually needs "
                f"{actual:.1f} ({drift:.1%} off). Wide-shot type is sized "
                "against SHOT_WIDE, so letting the two drift apart is exactly "
                "what makes labels come out the wrong size. Fix the LAYOUT — "
                "widening SHOT_WIDE to match is how a set quietly becomes "
                "unreadable."
            )

        # 6. And nothing read at the pull-back may fall below the readability
        #    floor. The two rotated labels are audited through an unrotated copy:
        #    `typography.measure` compares a bounding-box height against frame
        #    height, and for a label turned on its side that height is the
        #    length of the words, which would pass trivially and tell us nothing.
        items = [
            (f"{st.title_mob.text} wide label", st.wide_label)
            for st in self._stations()
            if st.wide_label is not None
        ]
        items += [
            ("the box title", self.llm.caption.copy().rotate(-np.pi / 2)),
            ("the return label", self.return_label.copy().rotate(-np.pi / 2)),
        ]
        unreadable = typography.audit(items, SHOT_WIDE)
        if unreadable:
            raise AssertionError(
                "below typography.MIN_READABLE at the pull-back: "
                + ", ".join(unreadable)
                + f". At SHOT_WIDE={SHOT_WIDE} these are decoration, not labels. "
                "Shorten the text or give the bay more room — do not reach for "
                "a bigger role, because the clamp inside Station will undo it."
            )

    def wide_frame_width(self, pad: float = 1.0) -> float:
        """Camera width the final pull-back needs to frame everything.

        ``pad`` matches what the scene passes to ``camera.frame_all``, so this
        prediction and the actual shot cannot drift apart.
        """
        group = self.everything
        return max(group.width + 2 * pad, (group.height + 2 * pad) * typography.ASPECT)

    # ------------------------------------------------------------------ paths
    def circuit(self):
        """The whole loop, built by joining the rails the viewer can see.

        Built from the DRAWN rails rather than from node centres, so the travel
        path and the diagram cannot disagree — which is exactly how a token once
        ended up flying through solid boxes in an earlier cut.
        """
        return routing.join(
            self.rail_chat_to_check,
            self.rail_check_to_edge,
            self._through(self.edge),
            self.rail_edge_to_gateway,
            self._through(self.gateway),
            self.rail_gateway_to_orch,
            # The orchestrator's run is L-shaped: the request comes in from the
            # left and leaves downward, so a straight left-to-right run would
            # have the payload exit the far side and then double back.
            [
                self.orchestrator.bay.get_left(),
                self.orchestrator.bay.get_center(),
                self.orchestrator.bay.get_bottom(),
            ],
            self.rail_orch_to_box,
            self.rail_into_column,
            *self.descent_rails(),
            self.rail_out_of_column,
            self.rail_box_to_stream,
            # And the stream bay is entered from the RIGHT, because the bottom
            # band runs the other way.
            [self.stream.bay.get_right(), self.stream.bay.get_left()],
            self.rail_stream_home,
        )

    @staticmethod
    def _through(station) -> list:
        """The straight left-to-right run inside a top-band bay."""
        return [station.bay.get_left(), station.bay.get_right()]

    def descent_rails(self) -> list:
        """The fall through the column, including the run inside each bay."""
        rails: list = []
        for i, station in enumerate(self.in_box_stations):
            rails.append(
                [
                    station.bay.get_top() + UP * 0.05,
                    station.bay.get_bottom() + DOWN * 0.05,
                ]
            )
            if i < len(self.in_box_stations) - 1:
                rails.append(self.rails_between_stations[i])
        return rails

    def home_rails(self) -> list:
        """Box bottom → stream → chat, as one traversable run.

        Exposed for a beat that wants to send something the whole way home in a
        single ``MoveAlongPath``. The shipped choreography does not: it stops at
        the stream bay to run the output checks, so it joins the first two rails
        for the courier and then flies the SSE chunks down
        ``rail_stream_home`` separately. This stays here because "the way home"
        is a property of the SET, and a future re-timing that drops the stop
        should not have to re-derive it from the rail attributes.
        """
        return [
            self.rail_out_of_column,
            self.rail_box_to_stream,
            [self.stream.bay.get_right(), self.stream.bay.get_left()],
            self.rail_stream_home,
        ]

    def glow_for(self, node) -> VGroup:
        """The pre-built halo for a station or for the bot-check tile."""
        try:
            return self._glows[id(node)]
        except KeyError:
            raise KeyError(
                f"no glow halo built for {node}. Halos are pre-built in "
                "LifecycleSet.__init__ for everything in `nodes`; constructing "
                "one mid-shot costs a beat."
            ) from None

    @property
    def everything(self) -> VGroup:
        """What the final pull-back frames.

        Deliberately the machines and the long way home, not every rail: the
        short rails all sit inside the bounding box of the bays they join, and
        the scene's close-up-only props (the request card) are excluded because
        a prop that has been faded out must not be able to widen SHOT_WIDE.
        """
        return VGroup(
            self.chat,
            self.bot_check,
            self.edge,
            self.gateway,
            self.orchestrator,
            self.llm,
            self.stream,
            self.after,
            self.rail_stream_home,
            self.return_label,
        )

    def reveal_labels(self, opacity: float = 1.0) -> list:
        """Animations bringing up every wide-shot label for the pull-back.

        Includes each bay's own swap: the close-up header fades out as the
        wide-shot label fades in, so a bay carries exactly one name at any
        distance rather than a small one nobody can read under a large one.
        `Station.reveal_wide` already fades text on fill and icons on stroke —
        do not "simplify" this into a single `set_opacity`, or every icon comes
        back as a solid blob.
        """
        anims = [self.wide_labels.animate.set_opacity(opacity)]
        for station in self._stations():
            anims.extend(station.reveal_wide(opacity))
        return anims
