from fastapi import UploadFile

async def extract_text_from_markdown(file: UploadFile) -> str:
    """Extract text content from markdown file"""
    # read() returns bytes in an async manner, then decode converts bytes to string, done async to avoid blocking server
    content = await file.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        # Handle encoding errors gracefully
        raise ValueError(f"File {file.filename} is not valid UTF-8 text")