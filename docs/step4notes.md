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

next is the chunker which is the main logic... I want todo this myself though it will take a longer time... it seems possible todo