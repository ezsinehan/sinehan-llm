  1. Local Qdrant (30 min) — Docker + two .env lines
  2. Local LLM with Ollama (a few hours) — rewrite llm.py, model selection based on your GPU
  3. Cloudflare Tunnel is setup but need it to be proper...

Note - End goal is to have this full system hosted on my website


Okay hosting now!
SOME SHIT WE HAVE TODO TO GIVE CLOUDFLARE THE ABILITY TO HOST OUR BACKEND
ou can transfer your domain out of Netlify at any time following these steps:

Sign up for a Name.com account.

ICANN — the organization that manages the Domain Name System (DNS) – requires verification of your contact information before we can transfer the domain to your account.

Go to Account Contacts in your Name.com dashboard, make sure your contact information is correct, and click Update. You can choose to verify your details via email or phone.

Once your contact information is verified, contact Netlify support with your Name.com Account Code, and we’ll transfer the domain to your account.

Learn more in the docs


NVM Im transfering the domain to name.com!


PS C:\Users\ezsin\Desktop\sinehanllm> cloudflared tunnel route dns api api.sinehan.dev
2026-03-31T21:40:14Z INF api.sinehan.dev is already configured to route to your tunnel tunnelID=0de7fad1-b29c-471e-997a-e6b7da4e57c5

Okay it seems pretty easy to set up and it seems its running on a local port and just being exposed with cloudflare tunnel not much setup just run a couple commands and set up the config file

possible production checklist
  Security:
  - CORS — restricted to sinehan.dev origins, POST only
  - Rate limiting — add middleware to prevent abuse (e.g., slowapi)
  - Input validation — max question length on /answer and /query
  - File upload limits — max file size on /ingest (or disable it publicly)
  - Qdrant auth — set QDRANT_API_KEY if Qdrant port is exposed

  Reliability:
  - Cloudflared as a Windows service — so the tunnel survives reboots
  - Docker restart policy — docker update --restart unless-stopped qdrant
  - Ollama auto-start — verify it's set to launch on boot
  - Health check endpoint — add a GET /health that pings Qdrant + Ollama

  Operational:
  - HTTPS only — tunnel handles this, but verify no HTTP fallback
  - Logging — structured request logging for debugging
  - .env not in git — verify it stays out of version control

A lot of junk BUT THIS IS IMPORTANT

Securing my system:
1. I added rate limiting so load abuse couldn't occur there also exists cors restrictions which only block browser access not stopping curls or postman use, but rate limiting should be enough to avoid abuse
2. Length Input validation, I don't allow empty or long inputs to overload the system, I don't worry about prompt injection as this isn't a secruity risk as the documents are not secure but maybe in the future for quality
3. Qdrant risk -> Qdrant was listening on 0.0.0.0:6333 which means any device on the network could read chunks delete inject, basically full admin access, not that big of deal since random internet attackers probably couldnt reach it, basically rebinded it to localhost only same with ollama