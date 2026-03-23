  2. Local LLM with Ollama (a few hours) — rewrite llm.py, model selection based on your GPU


  GPU: NVIDIA GeForce GTX 1650 4gb
  Model: Lack of personal exprience with open source lets just use the one of the top open source models: GLM-5 744B Kimi K2.5 1T MiniMax M2.5 230B DeepSeek V3.2 685B Step-3.5-Flash 196B Qwen 3.5 397B
  
  I want the home machine exposed via tunnel!


  Exact model can be worried about later!!!
  Refactors so far!:
  1. env. swwapped cloud setups to local setups
  2. config.py replaced gemini settings to ollama settigns
  3. vector_store.py works with local
  4. llm.py replaced gemini with gemini via openai python client (logic all same just transport layer changhed)
  5. added openai client api package

