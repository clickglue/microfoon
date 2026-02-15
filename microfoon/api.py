from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os

from microfoon.service import MicrofoonService
from microfoon.config import TARGET_VOLUME_NAME

app = FastAPI()
service = MicrofoonService()

# Models
class FileItem(BaseModel):
    filename: str
    path: str
    size_mb: float

class ProcessingRequest(BaseModel):
    filename: str

class ProcessedFile(BaseModel):
    id: int
    title: str
    status: str
    date: str
    obsidian_path: Optional[str]

# API Endpoints
@app.get("/api/scan", response_model=List[FileItem])
def scan_drive():
    try:
        files = service.scan_files()
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
def process_file(request: ProcessingRequest, background_tasks: BackgroundTasks):
    # For now, process synchronously to keep it simple, or use background tasks
    # Async processing is better for UX so the UI doesn't hang
    # But for MVP, synchronous might be easier to debug.
    # Let's try synchronous first as per CLI behavior.
    try:
        result = service.process_file(request.filename)
        if result.get("status") == "error":
             raise HTTPException(status_code=500, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processed", response_model=List[ProcessedFile])
def get_processed():
    return service.get_processed_files()

@app.delete("/api/delete/{filename}")
def delete_file(filename: str):
    success = service.delete_original(filename)
    if not success:
        raise HTTPException(status_code=404, detail="File not found or could not be deleted")
    return {"status": "success"}

# Serve Frontend
# Ensure the static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_server()
