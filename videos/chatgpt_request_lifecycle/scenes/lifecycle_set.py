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

#: How long the pull-back's ONE lap of the whole plant takes.
#:
#: Renamed from LOOP_RUN_TIME, which is the defect this film shipped with: the
#: end-of-film runner lapped the entire circuit repeatedly, which says every
#: token is re-scored at the edge and re-authenticated at the gateway. The plant
#: is crossed ONCE. What repeats is `decode_cycle()`, inside the box.
#:
#: It lives HERE rather than in the scene because `validate()` budgets its
#: chord-clearance assertion against it: a comet is sampled once per frame and
#: joined with straight chords, so a faster lap cuts corners harder. Keeping the
#: number in one place is what stops the assertion silently checking a shot that
#: no longer exists.
#:
#: 1.6 → 2.2 for the narration pass. The lap is the pull-back's one long travel
#: and it is what "the request crosses the plant once" is spoken over, so it is
#: where the beat's extra time went — a slower lap over the same path, rather
#: than a second lap, which would say the opposite of what the shot means.
#: Slowing it only makes the chord budget below finer, never coarser.
REQUEST_LAP_RUN_TIME = 2.2

#: How long one emitted token takes to fly the whole way home, in the pull-back's
#: four EXPLICIT cycles — the slowest thing that draws a comet over
#: `home_rails()`, and therefore the one `validate()` has to budget chords for.
#:
#: The accelerated cycles after those four fly the same path faster than this,
#: and deliberately carry NO comet: without a trail the payload is sampled onto
#: the true path every frame and cannot cut a corner at all, so there is nothing
#: for a chord budget to check. That is the trade — a bare dot at the speed the
#: beat is about, rather than a trail drawing a straight line across the plant.
EMIT_RUN_TIME = 0.40

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

#: The x the autoregressive loop-back rail runs up, inside the box.
#:
#: MEASURED, not chosen: the box frame's right edge is at 23.70 and the four
#: bays stop at 22.80, so the box's inner right margin is exactly 0.90 wide and
#: completely empty. 23.25 is its midline — 0.45 clear of the bays it passes and
#: 0.45 clear of the frame it runs inside. `validate()` re-derives both gaps
#: from the mobjects rather than trusting these numbers, so a change to
#: BAY_W or to PipelineBox's padding fails at construction instead of drawing a
#: rail through a bay.
LOOPBACK_X = 23.25


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
        # -- the autoregressive loop, drawn ------------------------------------
        # The one rail that makes the film's central claim true. Everything else
        # in this set is crossed ONCE: the request goes in along the top band and
        # the answer comes back along the bottom. Only this rail is travelled
        # again per token, and until it existed the end-of-film runner had
        # nowhere to lap but the whole plant — which asserts that every token is
        # re-authenticated at the gateway and re-assembled by the orchestrator.
        # It is not; decode reads the cache and nothing walks back upstream.
        #
        # Sampler → PREFILL/KV, not sampler → decode. The sampled token's keys
        # and values are appended to the cache and the next step reads the cache,
        # so routing the return through the KV bay makes the cache the hinge of
        # the cycle — which is the real mechanism — and reuses the two rails
        # already drawn (cache→decode, decode→sampler) for the rest of the lap.
        # The loop the viewer sees is then literally
        # `KV cache → decode → sample → append → KV cache`.
        #
        # It leaves the sampler's RIGHT edge and enters the prefill bay's RIGHT
        # edge, so the travel order runs bottom-to-top up the margin and the
        # chevrons point back up at the cache for free — no rotation argument,
        # nothing to keep in sync with the geometry.
        self.rail_sample_to_cache = Conveyor(
            [
                self.sampler.bay.get_right() + RIGHT * 0.05,
                np.array([LOOPBACK_X, float(self.sampler.bay.get_center()[1]), 0.0]),
                np.array([LOOPBACK_X, float(self.prefill.bay.get_center()[1]), 0.0]),
                self.prefill.bay.get_right() + RIGHT * 0.05,
            ],
            # TOKEN, not ASSISTANT: what rides this rail is the sampled token on
            # its way back into the machine, not a piece of the reply on its way
            # out. The reply path is the green one along the bottom.
            color=theme.TOKEN,
            chevrons=2,
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

        # Names the loop-back rail at the pull-back, where the rail is three
        # pixels of amber and nothing else says what it carries. Rotated and
        # placed in the box's RIGHT margin by the same `next_to` the box title
        # uses on the left, so the two read as a pair and neither is a written
        # -down coordinate that a padding change could invalidate.
        #
        # Centred on the loop's own vertical span (sampler → prefill), not on
        # the box, so the words sit beside the rail they name rather than beside
        # the tokenizer, which is not in the loop at all.
        self.loopback_label = typography.text(
            "label",
            "append K,V · next token",
            frame_width=SHOT_WIDE,
            color=theme.TOKEN,
        )
        self.loopback_label.rotate(np.pi / 2)
        # Clamped to the box's height for the same reason PipelineBox clamps its
        # own side title: at SHOT_WIDE a `label` role is 1.5 units of cap height,
        # so twenty-three characters measure 18.2 units end to end against a
        # 12.8-tall box. Unclamped it hung 4.5 units below the frame and 1.0
        # above it — a caption longer than the machine it names, crossing the
        # bottom band. Centring on the loop's own 5.4-unit span was tried and is
        # worse: the scale that fits puts it at 0.013 of frame height, a third
        # under typography.MIN_READABLE, i.e. drawn and unreadable.
        span = float(self.llm.frame.height) * 0.92
        if self.loopback_label.height > span:
            self.loopback_label.scale(span / float(self.loopback_label.height))
        self.loopback_label.next_to(self.llm.frame, RIGHT, buff=theme.PAD_MD)

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

        # The bot check is an `IconTile`, not a `Station`, so none of Station's
        # wide-label machinery applies to it — and nothing said so. Its close-up
        # caption measured 0.0073 of frame height at SHOT_WIDE=58, 2.7x under
        # typography.MIN_READABLE (0.020): at the pull-back, one of the ten
        # nodes was an illegible smudge standing next to nine marquee-sized
        # names. validate()'s readability audit walked `_stations()`, which by
        # definition cannot reach a tile, so the assertion that exists to catch
        # exactly this had a hole precisely where the problem was. Both halves
        # are fixed: the tile gets a pull-back label here, and the audit in
        # validate() now includes it.
        #
        # Sized to the free corridor between the chat window and the Edge bay
        # rather than to the 1.8-wide tile, because a label typed for the tile
        # would be back under the floor. The corridor is DERIVED from the two
        # neighbours, so moving either one cannot silently make this collide.
        corridor = float(self.edge.bay.get_left()[0]) - float(self.chat.get_right()[0])
        self.check_wide_label = typography.text(
            "heading", "bot check", frame_width=SHOT_WIDE,
            color=self.bot_check.accent, bold=True,
        )
        check_factor = min(corridor * 0.88 / float(self.check_wide_label.width), 1.0)
        if check_factor < 1.0:
            self.check_wide_label.scale(check_factor)
        self.check_wide_label.move_to(
            np.array([
                0.5 * (float(self.edge.bay.get_left()[0])
                       + float(self.chat.get_right()[0])),
                float(self.bot_check.tile.get_bottom()[1])
                - theme.PAD_SM
                - 0.5 * float(self.check_wide_label.height),
                0.0,
            ])
        )

        # Wide-shot labels stay dark until the pull-back: at a close-up they are
        # several times the size of anything else on screen.
        self.wide_labels = VGroup(
            self.llm.caption,
            self.return_label,
            self.check_wide_label,
            self.loopback_label,
        )
        self.wide_labels.set_opacity(0.0)

        # DRAW ORDER MATTERS, and it matters in one specific way that cost this
        # session a render: `PipelineBox.frame` is filled with theme.BG at full
        # opacity, so every rail that runs INSIDE the box is buried by it unless
        # it is added afterwards. The four in-box rails — down the midline,
        # between the bays, out of the bottom, and the loop-back up the right
        # margin — were added before `self.llm` in the first cut, and the
        # loop-back rail this film's whole correction rests on rendered as
        # nothing at all: the runner lapped a path with no visible track under
        # it. The rails outside the box never showed the problem, which is why
        # it survived until something was drawn inside.
        #
        # The stations come last of all, so a rail terminates neatly under the
        # bay edge it feeds rather than over it.
        self.add(
            halos,
            self.rail_chat_to_check,
            self.rail_check_to_edge,
            self.rail_edge_to_gateway,
            self.rail_gateway_to_orch,
            self.rail_orch_to_box,
            self.rail_box_to_stream,
            self.rail_stream_home,
            self.rail_after_spur,
            self.return_label,
            self.check_wide_label,
            self.loopback_label,
            self.llm,
            # --- inside the box, so after the box ---
            self.rail_into_column,
            self.rails_between_stations,
            self.rail_out_of_column,
            self.rail_sample_to_cache,
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
        """Everything that can light up, in flow order.

        An INVENTORY, not a loop. Lighting all ten of these on a repeating
        runner is the bug this film shipped with: it says every token is
        re-scored at the edge, re-authenticated at the gateway and re-assembled
        by the orchestrator. For a repeating pass use :attr:`loop_nodes`; for
        the one journey in, :attr:`request_nodes`.
        """
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

    @property
    def request_nodes(self) -> list:
        """The nodes the request crosses ONCE, on the way in.

        Prefill is deliberately not here even though the request's first pass
        goes through it: prefill is where the request stops being a request and
        becomes a cache, and it is the top of the loop. Splitting it this way is
        what lets the pull-back light this list once and then leave it resting
        while :attr:`loop_nodes` runs over and over.
        """
        return [
            self.bot_check,
            self.edge,
            self.gateway,
            self.orchestrator,
            self.tokenizer,
        ]

    @property
    def loop_nodes(self) -> list:
        """The three bays a decode step actually touches, in cycle order.

        KV cache → decode → sample, and then the sampled token's keys and
        values go back to the cache along `rail_sample_to_cache`. Nothing
        outside the box is in this list because nothing outside the box is in
        the loop.
        """
        return [self.prefill, self.decode, self.sampler]

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
        #    runs the WHOLE circuit in REQUEST_LAP_RUN_TIME, so the way home gets its
        #    share of those frames, not all of them.
        total_frames = LOOP_FPS * REQUEST_LAP_RUN_TIME
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
                    # {clearance:.3f}, not :.2f — a clearance of 0.998 printed
                    # as "sits 1.00 above ... under the 1.0 minimum", so the one
                    # message a maintainer sees when this trips read as a
                    # contradiction and sent the last reader looking for a bug
                    # in the assertion instead of in the layout.
                    f"the {station.title_mob.text} bay sits {clearance:.3f} above "
                    "the inference stack, which is under the 1.0 minimum. The "
                    "top band and the box would read as one machine at the "
                    "pull-back. Raise BAND_TOP_Y or shorten the column."
                )
        stream_gap = box_bottom - float(self.stream.bay.get_top()[1])
        if stream_gap < 1.0:
            raise AssertionError(
                f"the box bottom is only {stream_gap:.3f} above the stream bay. "
                "The rail out of the column needs visible run before it turns. "
                "Lower BAND_BOT_Y or shorten the column."
            )
        after_drop = BAND_BOT_Y - float(self.after.bay.get_top()[1])
        if after_drop < 1.5:
            raise AssertionError(
                # Every fragment carries the f prefix. An earlier version had
                # it on the first line only, so a maintainer who tripped this
                # assertion was told the rail runs "at y={BAND_BOT_Y}" —
                # literally, braces and all.
                f"the after bay's top is only {after_drop:.3f} below the bottom "
                f"band, so the return rail at y={BAND_BOT_Y} would run through "
                "it. Move the after bay further down."
            )
        for name, edge in (
            ("the chat window", float(self.chat.get_left()[0])),
            ("the after bay", float(self.after.bay.get_left()[0])),
        ):
            if edge - RETURN_X < 1.0:
                raise AssertionError(
                    f"RETURN_X={RETURN_X} is only {edge - RETURN_X:.3f} left of "
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
            # The bot check is a tile, so `_stations()` never reaches it and its
            # label used to be audited by nothing at all — see the note where
            # `check_wide_label` is built.
            ("the bot check wide label", self.check_wide_label),
            ("the box title", self.llm.caption.copy().rotate(-np.pi / 2)),
            ("the return label", self.return_label.copy().rotate(-np.pi / 2)),
            # Rotated, so audited through an unrotated copy like the other two:
            # `typography.measure` compares a bounding-box HEIGHT against the
            # frame, and for a label turned on its side that height is the
            # length of the words, which passes trivially and means nothing.
            (
                "the loop-back label",
                self.loopback_label.copy().rotate(-np.pi / 2),
            ),
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

        # 7. The loop-back rail runs INSIDE the box, up a margin 0.90 wide.
        #    `assert_path_clears` cannot express that — the box frame is an
        #    obstacle the rail is deliberately inside of, so the generic check
        #    would fire on the one thing that is correct. The two gaps that
        #    actually matter are measured instead, and they are measured off the
        #    mobjects so a change to BAY_W or to PipelineBox's padding trips this
        #    rather than quietly drawing a rail through a bay.
        rail_x = float(self.rail_sample_to_cache.path.get_right()[0])
        bay_gap = rail_x - float(self.sampler.bay.get_right()[0])
        frame_gap = float(self.llm.frame.get_right()[0]) - rail_x
        for name, gap in (("the bays", bay_gap), ("the box frame", frame_gap)):
            if gap < 0.25:
                raise AssertionError(
                    f"the loop-back rail clears {name} by only {gap:.3f}. It "
                    "runs up the box's inner right margin, which is "
                    f"{float(self.llm.frame.get_right()[0]) - float(self.sampler.bay.get_right()[0]):.2f} "
                    "wide; at this range it reads as drawn ON the bay edge "
                    "rather than as a return path. Move LOOPBACK_X, or widen "
                    "the box's pad."
                )
        # And the label that names it must sit OUTSIDE the frame, or the film's
        # one new caption is printed across the sampler's wide label.
        label_gap = (
            float(self.loopback_label.get_left()[0])
            - float(self.llm.frame.get_right()[0])
        )
        if label_gap < 0.1:
            raise AssertionError(
                f"the loop-back label overlaps the box frame by "
                f"{-label_gap:.3f}. It belongs in the right margin, mirroring "
                "the box title in the left one."
            )

        # 8. The cycle must CLOSE. A runner laps this once per token, so a gap
        #    between the last point and the first is not a rounding detail — it
        #    is a visible teleport, once per token, ten times in four seconds.
        #    routing.join welds segments within its own tolerance; if the ends
        #    do not meet within that same tolerance, nothing welds them and the
        #    lap is open.
        cycle = self.decode_cycle()
        gap = float(np.linalg.norm(cycle.get_start() - cycle.get_end()))
        if gap > 0.05:
            raise AssertionError(
                f"decode_cycle() does not close: its ends are {gap:.3f} apart. "
                "The pull-back laps this path once per generated token, so the "
                "payload would jump that distance ten times in four seconds. "
                "The loop-back rail must land on the same point the in-bay "
                "prefill run starts from."
            )

        # 9. The pull-back emits one token per cycle and flies each one the
        #    whole way home with a comet, at EMIT_RUN_TIME — three times faster
        #    than the streaming beat does it. Fast comets cut corners, so budget
        #    the chords at the frames that flight actually gets. The stream bay
        #    is excluded because the flight deliberately runs THROUGH it, which
        #    is the one thing on that path it is supposed to touch.
        emit_path = routing.join(*self.home_rails())
        emit_obstacles = [o for o in obstacles if o[1] is not self.stream.bay]
        emit_frames = max(6, int(LOOP_FPS * EMIT_RUN_TIME))
        routing.assert_trail_clears(
            emit_path, emit_obstacles, steps=emit_frames, ignore_ends=0.05
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

    def decode_cycle(self):
        """One autoregressive step: KV cache → decode → sample → append → repeat.

        The counterpart to :meth:`circuit`, and the reason the two exist
        separately. `circuit()` is the request's ONE journey through the plant.
        This is the loop that runs once per generated token, and it never leaves
        the box: a decode step takes the previously generated token, attends to
        the cached keys and values, emits one token, and appends that token's own
        K/V to the cache. The client, the edge, the gateway and the orchestrator
        are not in it.

        Built by joining the DRAWN rails, exactly as `circuit()` is, so the lap
        and the diagram cannot disagree. Both in-bay runs at the ends of the loop
        are L-shaped for the same reason the orchestrator's is: the prefill bay
        is entered from the right (off the loop-back rail) and left downward, and
        the sampler bay is entered from the top and left rightward onto the
        loop-back rail. A straight left-to-right run would have the payload exit
        the far side of a bay and double back.

        It CLOSES: the last point is the first point, so a runner can lap it any
        number of times without the jump that a gap would produce once per token.
        `validate()` asserts that, because a loop that does not close is a
        teleport the viewer sees and no test does.
        """
        return routing.join(
            # in-bay prefill: in from the loop-back rail, out downward
            [
                self.prefill.bay.get_right() + RIGHT * 0.05,
                self.prefill.bay.get_center(),
                self.prefill.bay.get_bottom() + DOWN * 0.05,
            ],
            self.rails_between_stations[1],  # prefill → decode
            [
                self.decode.bay.get_top() + UP * 0.05,
                self.decode.bay.get_bottom() + DOWN * 0.05,
            ],
            self.rails_between_stations[2],  # decode → sampler
            # in-bay sampler: in from above, out to the right
            [
                self.sampler.bay.get_top() + UP * 0.05,
                self.sampler.bay.get_center(),
                self.sampler.bay.get_right() + RIGHT * 0.05,
            ],
            self.rail_sample_to_cache,
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
            # The loop-back label hangs in the box's right margin, OUTSIDE the
            # frame that would otherwise bound this side of the world. It has to
            # be framed or the pull-back crops the one label that names the new
            # rail — and it is the reason wide_frame_width moved.
            self.loopback_label,
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
        # The tile's own cross-fade, matching every bay's: the close-up caption
        # (0.0073 of frame height out here) goes dark as the pull-back label
        # comes up, so the node carries exactly one name at any distance.
        if self.bot_check.label_mob is not None:
            anims.append(
                self.bot_check.label_mob.animate.set_opacity(1.0 - opacity)
            )
        for station in self._stations():
            anims.extend(station.reveal_wide(opacity))
        return anims
