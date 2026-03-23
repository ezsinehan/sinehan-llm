The Stack:
The first step is to choose the components as everything depends on the interfaces and constraints like API shapes, vector DB schema, DeepSeek request format, and embedding model output size

API Server: FastAPI - Fastest to demo, other options like Flask are simpler but require me to wire basics, or Django are overkill.

Vector DB: Qdrant - 2nd Fastest to demo, Chroma is faster but isn't respected as a production tool and I want to learn while building something real.

Embedding Model: Local(BAAI/bge-small-en-v1.5 via sentence-transformers?) - Keeping it local for cost control, stability, latency, hosting this is just unneeded complexity

LLM: Hosted(Gemini??) - Using Hosted for better quality, Gemini because it is good and has free tier. 

Anti-Stack: 
LangChain - I want to keep the RAG flow explicit(chunk, embed, search, prompt, generate), its a simple system

Relevance of the components?
The API server will expose the HTTP endpoints that the user can call, it will trigger the pipeline

What Pipeline?
Ingestion - Turn my documents into searchable vectors
1. Recieve input

2. Extract text

3. Clean text - remove extra whitespace, normalize newlines, drop obviously useless sections if needed

4. Chunk text - split into overlapping chunks(eg 300-500 tokens?), assign chunk_id, doc_id, chunk_index - overlapping chunks are used to solve the problem of unnatural breaks - chunk id is a global identifier for the chunk, w/o it you can't reliably update or referencce chunks and chunk index gives you the position of the chunk within the document

5. Attach metadata - source name, section title, option path - metadata gives vectors(alone is just numbers), metadata tells you where it came from what it is about and whether you can filter it - this is critical since without metadata, citations are impossible, filtering is not possible, debugging(when an answer is wrong you can't inspect where it is without metadata)

6. Embed Chunks (Local model) - What is "embedding" actually? It's a neural network that takes in text, outputs a fixed-length numeric vector. The vector represents semantic meaning of the text. Step by step heres whats happening, the chunk text is passed to the embedding model, then the model tokenizes the text, neural network runs forward pass converting tokens into internal representations abd aggregating into one vector, a fixed size output vector is produced, vector is stored alongside the chunk

7. Store in vector DB(Qdrant) - We store one record per chunk containing three things, ID, Vector, Payload(text + metadata) Qdrant calls each of these a point, storing the vectoir in an index optimized for similarity search, storing the payload alongside it, no learning or training is occuring

Query/Answer - Answers questions w/ retrieved context
1. Recieve question - Plain text question from the client

2. Embed question - The same embedding model is used as ingestion so vectors live in the same space - question is converted into fixed-length numeric vector

3. Vector search - Using the question vector search the collection, retrieving the top-k points based on similarity(cosine/dot), each result includes chunk text, metadata, and similarity score

4. Select context - optinaly you can filter by metadata(eg only resume or projects), keeping only the most relevant chunks that fit within the LLM's context window, order chunks using doc_id + chunk index for coherence

5. Build prompt - Combine system instructions, user question, retrieved chunk texts as context, constraining the LLM and reducing hallucinations

6. Call LLM(Deepseek) - Send the constructed prompt to the hosted LLM, the LLM will generate a natural language response based on the provided context

7. Attach citations - Map statements back to the retrieved chunks' metadata enabling attribution and explainability. 

8. Return response - return final answer text and citations

The vector DB, Qdrant, is the component that makes the search my info by meaning possible, providing these three capabilities that our system needs, storing embeddings, performs similarity search, stores and returns payload + metadata. Why cant we just use a normal DB? - Without Qdrant I'd have to store emdedings in postgres or files, manually compute similarity against every vector, implement indexing/ANN search myself, Qdrant is built for this purpose

The relevance of the Embedding model and hosted llm is explained enough prior. 

