The next step is to actually process the uploaded documents, this means we need to chunk, clean and attach the metadata

For the chunking step there are alot of options how we can do this each with its own upsides and downsides. 

Lets look at the various chunking methods to choose the best one: 
1. Character-Based Chunking - Pros: The simplest, no dependencies, fast - Cons: Can split mid sentence/word, disregards semantic boundaries, token count varience
2. Sentence-Based Chunking - Pros: Preserves sentence boundaries, more natural breaks, no dependencies - Cons: Token count varience, and handling long sentences
3. Paragraph-Based Chunking - Pros: Perserves paragraph structure, very simple, good for structured documents - Cons: Paragraphs can be long or short, less granular control
4. Recursive Character Chunking(hybrid) - Try the larger units first(paragraphs) then fall back to smaller ones(sentences then characters) - Pros: Respects structure when possible, Falls back gracefully, Good default strategy - Cons: More compex logic and not token aware
5. Sliding Window Chunking - Fixed-size windows that overlap - Pros: Consistent Chunk sizes, simple implementation, good for certain search patterns - Cons: Can break sentences/words

For this system, im noticing none of the methods actually maintain full sementic meaning and since for this specific project why not have some form of ai based chunking to maintain full sementic meaning since I wouldn't be vectorizing that much information

After further research on this, AI Chunking is not a good idea since the documents will be short and I controll the writing and structure, AI chunking will provide minimal returns for the complexity though it is something I want to experiment with in the future.

I will use structure-based deterministic chunking which is basically like recursive chunking but starting with headings prior to paragraphs:
Split by headings, if section is small -> keep it whole, if too big then split by paragraph, if paragraph to big then by sentence never mid sentence or mid list

I will do without overlap and test with it later.

Size Thresholds:
1. Section <= 600 tokens - Keep as one chunk
2. Section > 600 tokens - Split by paragraph
3. Paragrapgh > 600 tokens - Split by sentences
4. Chunk < 100 tokens merge with nearest sibling same section only

Token Counting Library - tiktoken with cl100k_base - Fast stable and close enough for LLM tokenization no need to waste time looking further

Markdown Parsing Approach - Regex Patterns - I will have control over the md structure so no need for more complex implementation

Markdown Formating - Not stripping markdown since Embeddings ignore most formating anyways and since stripping can remove important keywords

Next thing I need to decide is metadata structure, why is this important? - One, a vvector cannot explain it's self, when you retrieve a chunk you get text and similarty score, not enough to show citations, or links to projects or explain why something was retrieved debug wrong answers and update docs safely - metadata is the bridge between meaning and reality

Why we need each field:
1. doc_id (stable, human readable) - Purpose: identity, answers which project is this, enables replacing all chunks for a project on update, enables stable links, not using UUID since this is meaningless to humans, and breaks citation clarity, hard to reason about during debugging
2. chunk_index (sequential) - Purpose: position, perserves document order, allows merging/spliting later, enables recontruction of sections if needed, order mattrers for language humans think in order not hashes
3. section_title - Purpose: semantic anchor, this is how the model is going to say "im citing this section of that project
4. url - Purpose: verification, completes trust loop
5. token_count - Purpose: control and learning
6. source_name - Purpose: debugging tracking
Chunk_id is dervived. 

Only accepting markdown to ease complexity. 

Small Chunk Merging Logic - Merge backwords with prev chunk and if both are small merge both since small chunks retrieve noisily, merge backwards since language builds forward, unless its the first chunk then forward. 

Now actually building... Finished the chunk models and tested, now the text extractor, done and tested, text cleaner done and texted

next is the chunker which is the main logic... Okay so I have an untested implementation but very foreign to me, learning the code now: 
What is a regex string? - '^##\s+(.+)$' is just a string by itsefl it does nothing, it is data not behavior. 
What re.compile does? - Two concrete things: One it parses the pattern once, reading the string analyzing its structure and builds a internal representation, this internal form is not a string anymore. Two it returns a pattern object, stores the parsed regex and stores the flags multiline, exposes methods.
Why does this matter? - without compile we could do this re.finditer(r'^##\s+(.+)$', text, re.MULTILINE) but this leads python to re-parse the regex string and rebuild the internal search machine everytime you call it. 
With compile - You parse and build once. Then you can search as many times as needed. 
Without re.MULTILINE, the regex engine treat the input text as one long line.

Nice I understand the split by headings... Next step now.

---
[AI-GENERATED SUMMARY]

Step 1 Decisions - Split by Headings:
- Split on ## headings only (# is project title, ### stays within section)
- Content before first ## becomes "Introduction" section
- Empty sections (heading with no content) are dropped
- Section titles stored as plain text (no ## prefix)
- Regex: ^##\s+(.+)$ with re.MULTILINE

Step 2 Decisions - Split by Paragraphs:
- Paragraphs split on double newlines (\n\n or more)
- Section > 600 tokens triggers paragraph split
- All paragraph chunks inherit same section_title
- Heading line removed from chunk.text (stored in metadata only)
- Embedding will combine: f"{section_title}\n\n{text}" (Option B)
- chunk_index is sequential across all chunks (not per-section)

Step 3 Decisions - Split by Sentences:
- Paragraph > 600 tokens triggers sentence/unit split
- Simple sentence detection: split on ". ", "! ", "? " (user avoids abbreviations)
- List items (-, *, 1.) are atomic units - never split mid-item
- Units grouped together until approaching 600 tokens
- Single extremely long sentence stays whole (can't split mid-sentence)
- Regex for list items: ^\s*(-|\*|\d+\.)\s+

Step 4 Decisions - Merge Small Chunks:
- Chunks with < 100 tokens (MIN_TOKENS) are merged with a sibling
- Same section only (same section_title)
- Prefer merging backward (small chunk merges into previous)
- If first chunk is small, merge forward into next
- Separator when concatenating: "\n\n"
- merge_small_chunks() runs after building text_chunks, before creating Chunk objects
- chunk_index re-assigned 0, 1, 2... after merge
---

Okay at this stage step 3 is implemented and tested by ai but I still want to manually look over it and make sure all is well.

Next step is working on implementing chunks that are too small most be grouped.
- We will merge small chunks of the same section

---
How to run the manual test (chunking + optional embedding)
- From project root, with venv activated: `python scripts/manual_test_chunking.py`
- Uses `sample_doc.md` by default. To use another file: `python scripts/manual_test_chunking.py path/to/your.md`
- By default runs full pipeline: clean text -> chunk -> embed. Output: chunk summary by section, full chunk text, then embedding summary and writes `manual_test_embeddings.json` in project root (chunk_id, section_title, text_preview, embedding vector per chunk).
- To run chunking only (no embedding): `python scripts/manual_test_chunking.py --no-embed`
- Requires `sentence-transformers` for embedding: `pip install sentence-transformers`
- Step 5 (embedding) uses the same script; see step5notes for embedding details.