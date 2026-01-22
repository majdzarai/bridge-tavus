import os
import json
import asyncio
import time
import uuid
import hashlib
from typing import Dict, List, Optional, AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

# Configuration
TEACHER_API_URL = os.getenv("TEACHER_API_URL", "https://backend-teacher-production.up.railway.app")
PORT = int(os.getenv("PORT", "8080"))

# Initialize FastAPI app
app = FastAPI(title="Tavus Bridge", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions: Dict[str, Dict] = {}

# HTTP client for backend requests
http_client = httpx.AsyncClient(timeout=60.0)


# ============== Pydantic Models ==============

class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]


class Model(BaseModel):
    id: str
    object: str = "model"


class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[Model]


# ============== Helper Functions ==============

def extract_config_from_system_prompt(messages: List[Message]) -> Dict:
    """Extract configuration tags from the system prompt."""
    config = {
        "subject": "Physics",
        "chapter": "General",
        "lesson": "Introduction",
        "level": "High School",
        "language": "en",
        "student": "Student",
        "competence": ["Understanding the core concepts"]
    }
    
    # Find the system message
    system_content = ""
    for msg in messages:
        if msg.role == "system":
            system_content = msg.content
            break
    
    # Parse tags
    import re
    patterns = {
        "subject": r"\[SUBJECT:\s*([^\]]+)\]",
        "chapter": r"\[CHAPTER:\s*([^\]]+)\]",
        "lesson": r"\[LESSON:\s*([^\]]+)\]",
        "level": r"\[LEVEL:\s*([^\]]+)\]",
        "language": r"\[LANGUAGE:\s*([^\]]+)\]",
        "student": r"\[STUDENT:\s*([^\]]+)\]",
        "competence": r"\[COMPETENCE:\s*([^\]]+)\]"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, system_content)
        if match:
            value = match.group(1).strip()
            if key == "competence":
                # Competence should be an array
                config[key] = [value]
            else:
                config[key] = value
    
    # If no competence found, create one based on lesson
    if config["competence"] == ["Understanding the core concepts"] and config["lesson"]:
        config["competence"] = [f"Understanding {config['lesson']}"]
    
    return config


def get_conversation_id(messages: List[Message]) -> str:
    """Generate a unique conversation ID based on the system prompt."""
    system_content = ""
    for msg in messages:
        if msg.role == "system":
            system_content = msg.content
            break
    
    # Create hash of system prompt for consistent conversation ID
    return hashlib.md5(system_content.encode()).hexdigest()


def get_last_user_message(messages: List[Message]) -> str:
    """Get the last user message from the conversation."""
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


async def start_teacher_session(config: Dict) -> Dict:
    """Start a new teaching session on the backend."""
    url = f"{TEACHER_API_URL}/api/v1/teacher/start"
    
    payload = {
        "subject": config.get("subject", "Physics"),
        "chapter": config.get("chapter", "General"),
        "lesson": config.get("lesson", "Introduction"),
        "level": config.get("level", "High School"),
        "student_name": config.get("student", "Student"),
        "teacher_language": config.get("language", "en"),
        "competence": config.get("competence", ["Understanding the topic"])
    }
    
    print(f"[BRIDGE] Starting session with payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = await http_client.post(url, json=payload)
        print(f"[BRIDGE] Backend response status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"[BRIDGE] Backend error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
    except httpx.HTTPError as e:
        print(f"[BRIDGE] HTTP Error starting session: {e}")
        raise


async def send_message_to_teacher(session_id: str, message: str) -> Dict:
    """Send a message to the backend and get response."""
    url = f"{TEACHER_API_URL}/api/v1/teacher/message"
    
    payload = {
        "session_id": session_id,
        "message": message
    }
    
    print(f"[BRIDGE] Sending message to session {session_id}: {message[:50]}...")
    
    try:
        response = await http_client.post(url, json=payload)
        print(f"[BRIDGE] Message response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[BRIDGE] Backend error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
    except httpx.HTTPError as e:
        print(f"[BRIDGE] HTTP Error sending message: {e}")
        raise


async def stream_response(text: str, chat_id: str, model: str) -> AsyncGenerator[str, None]:
    """Stream text word-by-word in OpenAI SSE format."""
    words = text.split()
    created = int(time.time())
    
    for i, word in enumerate(words):
        chunk_data = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": word + " "},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"
        await asyncio.sleep(0.02)  # Small delay for natural speech pacing
    
    # Send final chunk with finish_reason
    final_chunk = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


# ============== Endpoints ==============

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Tavus Bridge",
        "version": "1.0.0",
        "status": "running",
        "description": "OpenAI-compatible bridge for Tavus avatars",
        "backend": TEACHER_API_URL
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/v1/models")
async def list_models():
    """List available models (Tavus may call this)."""
    return ModelsResponse(
        data=[
            Model(id="ai-teacher"),
            Model(id="tavus-bridge")
        ]
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Main endpoint - handles chat completions from Tavus."""
    
    print(f"\n[BRIDGE] ========== New Request ==========")
    print(f"[BRIDGE] Model: {request.model}, Stream: {request.stream}")
    
    # Extract configuration from system prompt
    config = extract_config_from_system_prompt(request.messages)
    print(f"[BRIDGE] Extracted config: {json.dumps(config, indent=2)}")
    
    # Get or create conversation ID
    conversation_id = get_conversation_id(request.messages)
    print(f"[BRIDGE] Conversation ID: {conversation_id}")
    
    # Get user message (the LAST one)
    user_message = get_last_user_message(request.messages)
    print(f"[BRIDGE] User message: {user_message}")
    
    # Check if session exists
    session = sessions.get(conversation_id)
    
    try:
        if not session:
            # Start new session
            print(f"[BRIDGE] No existing session, creating new one...")
            session_data = await start_teacher_session(config)
            session = {
                "session_id": session_data["session_id"],
                "config": config,
                "created": time.time(),
                "initial_message": session_data.get("initial_message", "Hello! I'm your AI teacher.")
            }
            sessions[conversation_id] = session
            print(f"[BRIDGE] Created new session: {session['session_id']}")
            
            # For the first message, return the initial greeting
            teacher_message = session["initial_message"]
            print(f"[BRIDGE] Returning initial message: {teacher_message[:50]}...")
            
        else:
            # Use existing session - send the message
            print(f"[BRIDGE] Using existing session: {session['session_id']}")
            response_data = await send_message_to_teacher(session["session_id"], user_message)
            teacher_message = response_data.get("teacher_message", "I apologize, but I didn't catch that. Could you please repeat?")
            print(f"[BRIDGE] Teacher response: {teacher_message[:100]}...")
            
    except Exception as e:
        print(f"[BRIDGE] ERROR: {e}")
        teacher_message = "I'm having a small technical issue. Could you repeat that?"
    
    # Generate chat completion ID
    chat_id = str(uuid.uuid4())
    
    # Return response (streaming or non-streaming)
    if request.stream:
        return StreamingResponse(
            stream_response(teacher_message, chat_id, request.model),
            media_type="text/event-stream"
        )
    else:
        return ChatCompletionResponse(
            id=chat_id,
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": teacher_message},
                "finish_reason": "stop"
            }]
        )


# ============== Startup/Shutdown ==============

@app.on_event("startup")
async def startup_event():
    print(f"🚀 Tavus Bridge starting on port {PORT}")
    print(f"📡 Backend URL: {TEACHER_API_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()
    print("🛑 Tavus Bridge shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)