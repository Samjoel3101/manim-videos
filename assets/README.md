# Assets

Rendered videos, checked in so a cut can be watched without a render.

`out/` is ignored — it is scratch, and every profile writes there. This
directory is the opposite: one committed file per video, the cut that was
reviewed and accepted. Replace a file here only when the video changes and the
new render has been looked at.

| File | Video | Profile |
|---|---|---|
| `chatgpt_message_journey.mp4` | `videos/chatgpt_message_journey` — `TheFactory` | `preview` (720p30, ~28s) |

Regenerate with:

```bash
.venv/bin/python scripts/evaluate.py --video chatgpt_message_journey \
  --scene TheFactory --profile preview
cp out/chatgpt_message_journey/preview/chatgpt_message_journey_preview.mp4 \
  assets/chatgpt_message_journey.mp4
```

Keep these small. A `preview` render is the right size to commit; a `final`
render is not — if one is wanted for distribution, attach it to a release
rather than the tree.
