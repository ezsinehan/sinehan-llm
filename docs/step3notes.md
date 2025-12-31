Now we are onto step three building the ingestion endpoint...

For this we need to create a FastAPI endpoint that accepts document uploads, which includes FastAPI application with an ingestion endpoint, an HTTP endpoint accepting pdfs, text, etc returning a success response. 

For this we need a couple dependencies, fastapi(the web framework), uvicorn(ASGI server to run FastAPI), python-multipart(required for file uploads in FastAPI)

Starting with a blank ingestion http endpoint which will simply take the document in and return success