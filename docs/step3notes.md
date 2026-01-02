Now we are onto step three building the ingestion endpoint...

For this we need to create a FastAPI endpoint that accepts document uploads, which includes FastAPI application with an ingestion endpoint, an HTTP endpoint accepting pdfs, text, etc returning a success response. 

For this we need a couple dependencies, fastapi(the web framework), uvicorn(ASGI server to run FastAPI), python-multipart(required for file uploads in FastAPI)

Starting with a blank ingestion http endpoint which will simply take the document in and return success

Lets test this first go into to the venv (./venv/Scripts/Activate.ps1(for windows)) then run uvicorn app.main:app --reload, then go to http://127.0.0.1:8000/docs for the interactive API docs that FastAPI generates, you can test the endpoint on the gui and it works there.