# What happens when you send a message to ChatGPT — script

Target runtime ~6:30. One section per scene. Narration is the source of truth
for pacing; the duration budget is what `render.py` output should land near.

---

## 1. User Input — "You type a sentence" (0:00–0:45, budget 45s)

**Narration.** You open ChatGPT, type a question, and hit enter. On your screen
that's one action. Underneath, it's the start of a journey through a few hundred
billion numbers. Let's follow a single message all the way through.

**Beats.**
1. Empty chat window fades in, composer focused, caret blinking.
2. The question types itself in: *"How does ChatGPT work?"*
3. Enter — the text lifts out of the composer and becomes a user bubble.
4. The assistant side stays empty; a typing indicator appears and holds.
5. Caption: *"Everything after this point happens in about two seconds."*

**Reuses:** `chat_ui.ChatWindow`, `ChatInput`, `TypingIndicator`.

---

## 2. Network Request — "It leaves your device" (0:45–1:25, budget 40s)

**Narration.** The text doesn't stay on your machine. It's wrapped in an HTTPS
request and sent to a datacentre, where a GPU is waiting.

**Beats.** Chat window shrinks to the left; `RequestPath` appears; packets fly
client → internet → server; the server rack lights up.

**Reuses:** `network.RequestPath`, `PacketStream`, `ServerRack`.

---

## 3. Tokenization — "Your sentence is chopped up" (1:25–2:20, budget 55s)

**Narration.** The model never sees your sentence. Before anything else, it's
split into tokens — chunks of characters that the model has a fixed vocabulary
for. Notice the spaces: a leading space belongs to the token after it. And
notice that a long or unusual word gets broken into pieces.

**Beats.**
1. The sentence appears as plain text, centred.
2. Split markers slide in between tokens; the text separates into chips.
3. The space glyph is called out on one chip.
4. A long word is shown breaking into two chips.
5. Each chip flips to reveal its integer token id.
6. Caption: *"The model only ever sees this list of integers."*

**Reuses:** `tokens.TokenStrip`, `TokenChip`, `simple_tokenize`.

---

## 4. Embedding — "Integers become directions" (2:20–3:05, budget 45s)

Each token id indexes a row in an embedding table: a long list of numbers. Similar
meanings end up pointing in similar directions.

**Reuses:** `vectors.VectorColumn`, `EmbeddingGrid`, `SemanticSpace`.

---

## 5. Transformer Pass — "96 layers of mixing" (3:05–4:15, budget 70s)

Attention lets every token look at every earlier token; the stack refines the
representation layer by layer.

**Reuses:** `transformer.TransformerStack`, `AttentionLines`, `AttentionMatrix`,
`ResidualStream`.

---

## 6. Sampling — "A probability over every word" (4:15–5:05, budget 50s)

The final layer produces a score for every token in the vocabulary. Softmax turns
those into probabilities; temperature decides how adventurous the pick is.

**Reuses:** `probability.ProbabilityChart`, `softmax`.

---

## 7. Token Streaming — "One token at a time" (5:05–5:55, budget 50s)

The chosen token is appended to the input and the whole thing runs again. That's
why the answer arrives word by word.

**Reuses:** `tokens.TokenStrip`, `network.PacketStream`, `chat_ui.ChatBubble`.

---

## 8. Response Rendered — "Back where you started" (5:55–6:30, budget 35s)

The stream lands back in the chat window as a finished answer. Pull back to show
the whole pipeline at once.

**Reuses:** `chat_ui.ChatWindow`, plus miniatures of every earlier component.
