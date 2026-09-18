# Assets

Rendered videos, checked in so a cut can be watched without a render.

`out/` is ignored — it is scratch, and every profile writes there. This
directory is the opposite: one committed file per video, the cut that was
reviewed and accepted. Replace a file here only when the video changes and the
new render has been looked at.

| File | Video | Profile |
|---|---|---|
| `chatgpt_message_journey.mp4` | `videos/chatgpt_message_journey` — `TheFactory` | `preview` (720p30, ~28s, 1.5M) |
| `chatgpt_request_lifecycle.mp4` | `videos/chatgpt_request_lifecycle` — `TheLifecycle` | `final` (1080p60, 44.1s, 4.1M) |

Regenerate with:

```bash
.venv/bin/python videos/<slug>/render.py --profile <profile>
cp out/<slug>/<profile>/<slug>_<profile>.mp4 assets/<slug>.mp4
```

Keep these small. The rule of thumb used to be "`preview` is the right size to
commit, `final` is not", and for footage that is mostly true. It is not true for
what this repo makes: these are flat vector frames on a near-black background,
which H.264 compresses far better than photographic video, so the 1080p60
`final` cut of the 45-second lifecycle film is **4.1M** — less than three times
the 720p30 preview of the 30-second one. Check the size before assuming;
`final` is committable here as long as it stays in single-digit megabytes. If a
future cut does not, render it at `preview` instead, or attach the `final` to a
release rather than the tree.
