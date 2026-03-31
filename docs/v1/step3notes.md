Learning my setup and making sure it is correct

❯ Okay concurrently I'm working on the frontend portion trying to get this wired up to my actual
website, but I have some functionality concerns, I don't fully understand how it working and for me
to safely host on my website I need to understand this...

● That makes sense — you need to understand the system before exposing it publicly. What specifically
  are you unsure about? For example:

  - The request flow — what happens when someone asks a question on your website?
  - Security — what's exposed, who can call the API, is there auth?
  - Data safety — can users access/manipulate your Qdrant data through the API?
  - LLM behavior — can someone prompt-inject or get off-topic answers?
  - Resource concerns — what happens under load with local Ollama/Qdrant?

  /answer — What happens when someone asks a question

  Browser (sinehan.dev)
    │
    ▼  POST /answer { question: "What does Sinehan know?", top_k: 5 }
  Cloudflare Tunnel (api.sinehan.dev)
    │
    ▼  forwards to localhost:8000
  FastAPI (main.py:72)
    │
    ├─ 1. EMBED the question
    │     embedder.py → sentence-transformers encodes the question string
    │     into a 384-dimensional vector (locally, no API call)
    │
    ├─ 2. SEARCH Qdrant for similar chunks
    │     vector_store.py:search() → sends the vector to local Qdrant (Docker)
    │     → returns top-k chunks ranked by cosine similarity
    │     Each chunk has: text, section_title, doc_id, score, etc.
    │
    ├─ 3. BUILD context + CALL Ollama
    │     llm.py:answer_from_chunks() →
    │       - Concatenates the top-k chunk texts into a context block
    │       - Sends system prompt + context + question to Ollama (localhost:11434)
    │       - System prompt enforces: third-person, Sinehan-only, context-only
    │       - Temperature 0.2 (low creativity)
    │       - Returns the generated answer text
    │
    ├─ 4. BUILD citations
    │     Extracts chunk_id, doc_id, section_title, url, source_name
    │     from each of the top-k chunks (no text in citations)
    │
    ▼
    Response: { answer: "Sinehan has...", citations: [...] }

  Key things to know

  - Everything runs locally — embedding model, Qdrant, Ollama. No external API calls leave your
  machine.
  - Ollama is the bottleneck — it's the only synchronous LLM inference step. With llama3.2:3b it's
  fast, but concurrent requests will queue up since Ollama serves one request at a time by default.
  - The embedding model loads lazily — first request is slow (loads BAAI/bge-small-en-v1.5 into
  memory), subsequent requests are fast.
  - CORS is locked to your domain — only sinehan.dev and www.sinehan.dev can call the API from a
  browser (main.py:16-17).
  - No auth on the API — anyone who knows api.sinehan.dev can POST directly (e.g. via curl). CORS only
   protects browser requests.