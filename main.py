# main.py
from fastapi import FastAPI, Form, Request, File, UploadFile, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from agent.core import process_user_input
# Imports needed for local file handling
import shutil 
import os
import uuid
# from config import settings # Not needed in this local version
# from google.cloud import storage # i will uncomment when the cloud is set up

# Setup the FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# storage_client = storage.Client() (# i will uncomment when the cloud is set up)
# GCS_BUCKET_NAME = settings.gcs_bucket_name (# i will uncomment when the cloud is set up)

# LOCAL STORAGE SETUP

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


app.mount("/static", StaticFiles(directory="static"), name="static")


MAX_FILE_SIZE = 5 * 1024 * 1024  
ALLOWED_TYPES = ["image/jpeg", "image/png"]


@app.get("/")
async def home(request: Request):
    source = request.headers.get("referer", "Direct Access")
    return templates.TemplateResponse("index.html", {"request": request, "source": source})

@app.post("/chat")
async def chat(request: Request, message: str = Form(...)):
    source = request.headers.get("referer", "Unknown")
    user_input_data = {
        "role": "user",
        "content": message
    }
    reply = process_user_input(user_input_data, source)
    return {"reply": reply}


@app.post("/upload-proof")
async def upload_proof(request: Request, file: UploadFile = File(...), message: str = Form(...)):
    """Handles the file upload, validates it, saves it locally, and calls core logic."""
    source = request.headers.get("referer", "Unknown")

    
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type ({file.content_type}). Only JPEG and PNG are allowed."
        )

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size too large. Must be less than {MAX_FILE_SIZE / 1024 / 1024:.0f} MB."
        )
    await file.seek(0) 

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer) 
        
        file_url = f"/static/uploads/{unique_filename}"
        
        user_input_data = {
            "role": "user",
            "content": message,
            "image_url": file_url
        }

        reply = process_user_input(user_input_data, source)
        
    except Exception as e:
        print(f"Error during file upload or processing: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading file: {str(e)}")
    finally:
        await file.close()

    return {"reply": reply}
