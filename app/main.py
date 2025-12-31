from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    return {"status": "recieved", "filename": file.filename}
