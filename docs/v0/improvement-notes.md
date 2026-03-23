## Improving answer quality

- **Retrieval**
  - Add an optional score threshold in `vector_store.search` to drop low-similarity chunks.
  - Tune `top_k` (default 5–8) based on question type and log scores to see what works best.

- **Prompt / LLM**
  - Refine `SYSTEM_INSTRUCTIONS` with 1–2 negative examples (off-topic questions) so refusals are consistent.
  - Standardize answer format (e.g. 2–3 bullets plus 1 summary sentence) for recruiter-facing responses.

- **Chunks & content**
  - Experiment with `MAX_TOKENS` in the chunker (e.g. 450–700) for the best balance of detail vs. focus.
  - Add a `section_type` field (experience/skills/projects) to `ChunkMetadata` to bias retrieval later.
  - Enrich `sinehan_rag.md` with concrete bullets (tech, responsibilities, outcomes) under each role.

