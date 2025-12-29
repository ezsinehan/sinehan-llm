1. Choose components: API server + embedding model + vector DB + hosted LLM (Qwen)
2. Set up secrets/config: Gemini API key, model name, vector DB URL, embedding model name
3. Build ingestion endpoint: upload/import docs
4. Chunk + clean text, attach metadata
5. Embed chunks locally
6. Store embeddings + chunk text + metadata in the vector DB
7. Build query endpoint: embed question → vector search top-k
8. Build answer endpoint: send (question + retrieved chunks) to DeepSeek → get response
9. Return response + citations (metadata for retrieved chunks)
10. Add minimal logs/metrics + package (Docker + README + example requests)
