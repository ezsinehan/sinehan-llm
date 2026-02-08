# Sinehan RAG

This project ingests markdown documentation, chunks it with structure-aware rules, and answers questions using retrieved chunks and an LLM. You control the docs, so chunking is deterministic and optimized for your headings and paragraph structure.

## Getting Started

Install dependencies with pip. Create a virtual environment and activate it before installing. Then run the API server and upload your first markdown document.

You can pass an optional URL when ingesting so that citations in answers link back to the source. The chunker only accepts markdown to keep the pipeline simple and predictable.

- Create a venv: `python -m venv venv`
- Activate (Windows): `.\venv\Scripts\activate`
- Install: `pip install -r requirements.txt`
- Run the server and hit the ingestion endpoint with your file and doc_id.

## Configuration

Set environment variables for the API key, model names, and vector DB URL. The chunker uses fixed thresholds you can rely on when writing docs.

- **MAX_TOKENS (600)**: Soft maximum per chunk. Sections or paragraphs above this are split by paragraph, then by sentence or list item if needed. Slightly over (e.g. 650) is kept whole to preserve meaning.
- **MIN_TOKENS (100)**: Chunks below this are merged with a sibling in the same section (backward merge, or forward if the chunk is the first in the section).
- Section titles are stored in chunk metadata for citations; the heading line is not duplicated in chunk text. When embedding, use `section_title + "\n\n" + chunk.text` so the vector has full context.

Only markdown is accepted. You control structure, so we use regex-based parsing and avoid heavy dependencies.

## Chunking Pipeline

The pipeline runs in four steps. Understanding them helps you write docs that chunk well.

**Step 1: Split by headings.** The chunker splits only on level-two headings (`##`). The top-level `#` is treated as project or doc title and stays in the first section. Content before the first `##` becomes a section titled "Introduction". Subheadings like `###` are left inside the section and are not split points. Empty sections (a heading with no content) are dropped. Section titles are stored as plain text in metadata (no `##` prefix).

**Step 2: Split by paragraphs.** If a section is larger than MAX_TOKENS, it is split by paragraphs. Paragraphs are separated by two or more newlines. Each resulting chunk keeps the same section_title. The `##` heading line is removed from the chunk text; citations use metadata (section_title and url). If a section has only one paragraph and it is over the limit, the pipeline continues to Step 3 for that paragraph.

**Step 3: Split by sentences and list items.** If a paragraph is still over MAX_TOKENS, it is split into units: sentences (split on `. `, `! `, `? `) and list items (lines starting with `-`, `*`, or `1.`). List items are never split in the middle. Units are then grouped in order until the next unit would exceed the token limit, so you get fewer, fuller chunks instead of one chunk per sentence. A single very long sentence with no period stays as one chunk. We use simple sentence boundaries; avoid abbreviations like "U.S." or "e.g." in the middle of sentences or write them in a way that does not trigger a false split.

**Step 4: Merge small chunks.** Chunks smaller than MIN_TOKENS are merged with a sibling in the same section. We prefer merging backward (into the previous chunk). If the first chunk of the document is small, it is merged forward into the next chunk. Merging only happens within the same section, so a tiny "Introduction" and a tiny "Configuration" do not get merged together. This reduces noisy retrieval from very small chunks while keeping section boundaries clear.

After all steps, each chunk has: doc_id, chunk_index, section_title, url (optional), token_count, and source_name. chunk_id is derived as `{doc_id}_{chunk_index}`. Embeddings should be computed over the combined title and text so that retrieval and citations stay aligned.

## API Overview

The ingestion endpoint accepts a markdown file and parameters such as doc_id and optional url. doc_id should be stable and human-readable (e.g. project or doc name) so that you can replace all chunks for a document when you re-ingest. The source_name is typically the filename and is used for debugging and display. The vector store will hold the embedding, the chunk text, and the metadata so that at query time you can return the top-k chunks and their section_title and url for citations.

The query endpoint will take a question, embed it with the same model used for chunks, and run a vector search. The answer endpoint will receive the question and the retrieved chunks (text and metadata) and call the LLM to produce an answer with citations. Returning metadata for each cited chunk lets the client show "From section X" and link to the url when available. Logs and metrics can be minimal at first; add more as you need to debug or tune retrieval and model behavior.

## Reference: Thresholds and Edge Cases

The chunker is configured with two main constants. MAX_TOKENS is 600. Any section whose content (after removing the heading line) is at or below 600 tokens stays as a single chunk. If the section is larger, it is split by paragraphs. Each paragraph is then checked: if it is at or below 600 tokens, it becomes one chunk; if it is larger, it is split into units (sentences and list items) and units are grouped until adding the next unit would exceed 600 tokens. So you can get multiple chunks from one section when that section has several paragraphs or one very long paragraph. The limit is soft: a paragraph of 620 tokens is kept whole rather than split mid-sentence. MIN_TOKENS is 100. Any chunk with fewer than 100 tokens is merged with an adjacent chunk in the same section. The merge is backward (into the previous chunk) unless the small chunk is the first in the document, in which case it is merged forward into the next chunk. Merging only happens when the two chunks share the same section_title, so section boundaries are preserved. Empty sections (a `##` heading with no content or only whitespace) are dropped and do not produce a chunk. Content before the first `##` is assigned the synthetic section title "Introduction". If the entire document has no `##` headings, the whole document is one section titled "Introduction". Token counting uses tiktoken with the cl100k_base encoding so that sizes are consistent with typical embedding and LLM usage. When you re-ingest a document, use the same doc_id so that the system can replace all existing chunks for that document with the new set; chunk_index is then reassigned 0, 1, 2, and so on for the new chunks.

List items are defined as lines that start with a dash, asterisk, or number followed by a period and space (e.g. `-`, `*`, `1.`). Such a line is treated as one indivisible unit. If a list item is longer than 600 tokens, it stays as one chunk. We do not split in the middle of a list item. Sentences are split on the first space after a period, exclamation mark, or question mark. Abbreviations that look like sentence endings (e.g. "Dr." or "U.S.") can cause incorrect splits, so the docs recommend avoiding them in the middle of sentences or spelling them in a way that does not match the pattern. The chunker does not use a full NLP sentence tokenizer. Headings below level two (e.g. `###` or `####`) are kept as part of the section content and are not used as split points. Only `##` starts a new section. This keeps the structure simple and matches the expectation that the top-level `#` is the doc or project name and that subsections belong under a single `##` section for chunking purposes.

## Writing Docs for Good Chunking

Use clear `##` headings for each major section so that the chunker can split there first. Keep paragraphs under roughly 600 tokens when you can; if a section grows large, the chunker will split by paragraph and then by sentence, but coherent paragraphs make for better chunks. Use lists where they fit; each list item is one unit and is never split in the middle. Avoid a long block of text with no paragraph breaks or sentence boundaries, since the only option then is to keep it as one large chunk or split by character, which we do not do. If you have a very long section, adding a few subheadings or paragraph breaks gives the chunker natural split points. Finally, small sections (e.g. one short paragraph) are fine; if they end up under 100 tokens, they will be merged with the previous or next chunk in the same section, which keeps retrieval quality while preserving section identity in metadata.
