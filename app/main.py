# FastAPI is the main class to create the app instance
# UploadFile  type for upload files
# File(...) dependencies to mark a parameter as a file upload
from fastapi import FastAPI, UploadFile, File

# Creates the app instance, app is used to register routes and configure the API
app = FastAPI()

# @app.post is a decorator that registers a post endpoint!
# /ingest is the url path that becomes localhost:8000/ingest
# async is supported by FastAPI

#UploadFile provides: filename, content_type(MIMI type), size, read(read content as bytes then decode for text)
@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    # Return response is a JSON response, fastAPI serializes the dict to JSON, and we access the name
    return {"status": "recieved", "filename": file.filename}
