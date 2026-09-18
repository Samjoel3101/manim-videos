# What happens when you send a message to ChatGPT — script

**30 seconds, one continuous shot, no cuts.**

The whole pipeline is laid out once in world space (see `scenes/factory_set.py`)
and the camera flies through it: close on each machine in turn, then all the way
out at the end to show the plant running as one circuit. The viewer recognises
the wide shot because they have already stood inside every part of it.

## The set

```
 [chat −22] → [web server −13] → ┌ THE MODEL ─────────────────────────┐
                                 │ tokenize  embed  transformer  sample│
                                 │   −4       +3       +10       +17   │
                                 └─────────────────────────────────┬───┘
   ▲                                                               │
   └──────────────── return rail (y = −7) ─────────────────────────┘
```

Roughly 48 units wide, so the final pull-back is about 3.3×.

## The through-line

One payload, never destroyed, only transformed. This is what makes it read as a
factory rather than a slideshow:

> typed text → packet → token chips → vector columns → activation in the stack →
> probability bars → one token → packet → a word in the reply

## Beat sheet

| Timecode | Beat | Shot |
|---|---|---|
| 0.0–3.0 | The question types itself in and is sent; the message becomes a packet | tight on chat, w=12 |
| 3.0–6.2 | Packet crosses the wire, the web server lights up, and hands off to the model; camera dives in | pan + zoom out to w=38, then dive |
| 6.2–10.0 | **Tokenize** — the sentence arrives and shatters into chips with ids | tight, w=12 |
| 10.0–13.6 | **Embed** — each chip flies across and becomes a column of numbers | pan right |
| 13.6–17.8 | **Transformer** — activation climbs 96 layers, a prediction vector drops out | pan right |
| 17.8–21.2 | **Sample** — a score for every word it knows; one is picked | pan right |
| 21.2–24.6 | The token rides the return rail home and lands as a word | pull back, then tight on chat |
| 24.6–29.3 | **The whole plant.** Marquees light up, three more tokens run the full circuit, the answer completes | w≈50 |

## Narration (if a voice-over pass happens)

> You type a question and hit send. It leaves your machine as an ordinary web
> request — and lands in a building full of GPUs.
>
> First your sentence is cut into tokens. Not words: pieces the model has seen
> before. Each one becomes a long list of numbers — a direction in a space where
> similar meanings point the same way.
>
> Then it climbs the stack. Ninety-six layers, and in every one, each token gets
> to look at every token before it.
>
> Out the top comes a score for every word the model knows. One gets picked.
>
> That single token travels all the way back to your screen. And then the whole
> thing runs again, for the next one — which is why the answer arrives a word at
> a time.

## Notes for editing

- Pacing is carried by `run_time` values in `scenes/scene_factory.py`, grouped by
  beat with the target timecodes in comments. Changing one means re-balancing
  its neighbours.
- `W_TIGHT = 12.0` is a floor, not a preference: at 16:9 anything smaller crops
  the bottom of a 5.2-tall station bay and its caption.
- Station marquees sit *below* their bays and are clamped to the bay width, so
  they cannot collide with each other or with the box title in the wide shot.
