# Spec: Context Window Management (RAG Proxy)

## Purpose

Maintain coherent conversation without unbounded history by combining a rolling summary with a trimmed recent-message window.

## State

* `summary`: abstractive running synopsis of prior turns.
* `window`: deque of last N messages `[{role, content}]`, token-limited.
* Limits:

  * `WINDOW_MAX_TOKENS` (e.g., 1200)
  * `SUMMARY_MAX_CHARS` (e.g., 8k)

## Inputs per Turn

* `session_id`
* `user_msg`

## Outputs per Turn

* OpenAI-compatible `chat.completions` response
* Optional `proxy_metadata.tokens_used`, `proxy_metadata.history_kept`

## Algorithm (Turn K)

1. Load state `{summary, window}` for `session_id`.
2. Query rewrite: produce a short self-contained query from `summary + tail(window) + user_msg`.
3. Retrieval: get `chunks(K)` from vector store using rewritten query.
4. Build prompt:

   * `SYSTEM`: “Use only CONTEXT. If missing, say ‘not present’. Cite.”
   * `HISTORY`: trimmed `window`
   * `USER`: `CONTEXT = summary + chunks(K)` + `user_msg`
5. Call upstream `chat.completions`.
6. Post-process:

   * Update `summary` by incremental summarization of `{user_msg, answer}`
   * Append `{user_msg, answer}` to `window`
   * Prune `window` to `WINDOW_MAX_TOKENS`
   * Truncate `summary` to `SUMMARY_MAX_CHARS`
   * Persist state

## Token Budgeting

Order of sacrifice under pressure:

1. Drop oldest items in `window`
2. Shorten `summary` (tail-preserving trim)
3. Reduce `top_k` retrieval

## Determinism

* `temperature = 0–0.2`
* Set `seed` if supported

## Failure Modes

* Empty retrieval → answer template “not present”; do not update `summary`
* State store unavailable → degrade to `window` only
* Oversized inputs → enforce hard caps, return `proxy_metadata.truncated=true`

## Security

* Do not store secrets or PII in `summary`/`window`
* Namespace state by tenant/org/session

## Observability

* Log counts: `tokens_history`, `tokens_context`, `k_selected`
* Spans: `rewrite`, `retrieve`, `prompt_build`, `llm_call`, `summarize`
* Redact user content in logs by default

## Config

* `WINDOW_MAX_TOKENS`
* `SUMMARY_MAX_CHARS`
* `RAG_TOP_K`
* `CHAT_MODEL`, `EMBED_MODEL`
