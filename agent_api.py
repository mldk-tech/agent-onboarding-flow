from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import io
from typing import Optional
import logging

from agent_onboarding_flow import agent_main_loop

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/run-agent")
async def run_agent(user_input: str = Form(...), user_id: str = Form(...), file: Optional[UploadFile] = None):
    logger.info("Received request to /run-agent")
    logger.info(f"Received user_input: {user_input}")
    logger.info(f"Received user_id: {user_id}")
    logger.info(f"Received file: {file}")
    
    try:
        file_bytes = await file.read() if file else None
        # Add debug logging for the file content
        if file_bytes:
            logger.info(f"File content length: {len(file_bytes)} bytes")
        response = agent_main_loop(user_input, user_id, file_bytes)
        logger.info(f"Generated response: {response}")
        return JSONResponse(content={"response": response})
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    logger.info("Starting server on http://localhost:8003")
    uvicorn.run("agent_api:app", host="localhost", port=8003, reload=True)
