# CLAUDE.md - Tavus Bridge for AI Teacher

## Project Overview

Build an OpenAI-compatible bridge server that connects a Tavus avatar to an existing LangGraph AI Teacher backend.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────────────────────────┐
│    TAVUS     │────▶│    BRIDGE    │────▶│   LANGGRAPH BACKEND                 │
│   (Avatar)   │     │  (This app)  │     │   backend-teacher-production.       │
│              │◀────│              │◀────│   up.railway.app                    │
└──────────────┘     └──────────────┘     └─────────────────────────────────────┘

Tavus sends:                              Your backend expects:
POST /v1/chat/completions                 POST /api/v1/teacher/start
{                                         POST /api/v1/teacher/message
  "messages": [...],                      {
  "model": "ai-teacher",                    "session_id": "uuid",
  "stream": true                            "message": "student text"
}                                         }
```

## The Problem We're Solving

- **Tavus** speaks OpenAI format (`/v1/chat/completions`)
- **Your Backend** speaks your custom format (`/api/v1/teacher/message`)
- **This Bridge** translates between them

## Backend API Reference

Your existing backend at `https://backend-teacher-production.up.railway.app`:

### Start Session
```
POST /api/v1/teacher/start
Content-Type: application/json

Request:
{
  "subject": "Physics",
  "chapter": "Mechanics",
  "lesson": "Newton's Laws",
  "level": "Grade 10",
  "student_name": "Ahmed",
  "teacher_language": "en",
  "competence": ["Understanding Newton's Laws of Motion"]
}

Response (201):
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "onboarding",
  "student_name": "Ahmed",
  "initial_message": "Hello Ahmed! I'm your AI teacher...",
  "curriculum": {
    "subject": "Physics",
    "chapter": "Mechanics",
    "lesson": "Newton's Laws",
    "level": "Grade 10"
  }
}
```

### Send Message
```
POST /api/v1/teacher/message
Content-Type: application/json

Request:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What is Newton's first law?"
}

Response (200):
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "teaching",
  "teacher_message": "Great question! Newton's first law states that...",
  "emotional_ready": true,
  "is_awaiting_input": true
}
```

## Bridge Requirements

### Endpoints to Implement

1. `GET /` - Health check / info
2. `GET /health` - Health status
3. `GET /v1/models` - List models (Tavus may call this)
4. `POST /v1/chat/completions` - Main endpoint Tavus calls

### POST /v1/chat/completions Behavior

1. **Extract config from system prompt** - Parse tags like `[SUBJECT: Physics]`
2. **Check if session exists** - Use conversation ID to track sessions
3. **If new conversation** - Call `/api/v1/teacher/start` on backend
4. **If existing conversation** - Call `/api/v1/teacher/message` on backend
5. **Return response** - Stream in OpenAI SSE format

### System Prompt Parsing

The Tavus persona will include config in the system prompt:
```
You are a physics teacher.
[SUBJECT: Physics]
[CHAPTER: Newton's Laws]
[LESSON: First Law of Motion]
[LEVEL: Grade 10]
[LANGUAGE: en]
[STUDENT: Ahmed]
```

Parse these tags to configure the teaching session.

### OpenAI Streaming Format (SSE)

Tavus expects Server-Sent Events format:
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"ai-teacher","choices":[{"index":0,"delta":{"content":"Hello "},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"ai-teacher","choices":[{"index":0,"delta":{"content":"world!"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"ai-teacher","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

## Tech Stack

- **Framework**: FastAPI
- **HTTP Client**: httpx (async)
- **Deployment**: Railway
- **Python**: 3.10+

## Environment Variables

```
TEACHER_API_URL=https://backend-teacher-production.up.railway.app
PORT=8080
```

## File Structure

```
tavus-bridge/
├── main.py           # FastAPI application (ALL code in one file)
├── requirements.txt  # Dependencies
├── Procfile          # Railway start command
└── railway.json      # Railway config (optional)
```

## Dependencies (requirements.txt)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
```

## Procfile

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Key Implementation Details

### Session Management

- Store sessions in memory: `Dict[str, Dict]`
- Key: hash of system prompt (consistent per Tavus conversation)
- Value: `{"session_id": "uuid", "config": {...}, "created": timestamp}`

### Error Handling

- If backend fails, return friendly message: "I'm having a small issue, could you repeat that?"
- Always return valid OpenAI format even on errors
- Log errors for debugging

### Streaming

- Stream word-by-word for natural speech pacing
- Small delay between words (~20-30ms)
- Proper SSE format with `data: ` prefix and `\n\n` suffix

### Multi-Language Support

Your backend supports `teacher_language` parameter:
- `en` - English
- `ar` - Arabic  
- `fr` - French

Parse `[LANGUAGE: xx]` from system prompt and pass to backend.

## Testing

After deployment, test with curl:

```bash
# Health check
curl https://my-bridge.up.railway.app/health

# Test chat (non-streaming)
curl -X POST https://your-bridge.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai-teacher",
    "stream": false,
    "messages": [
      {"role": "system", "content": "You are a teacher. [SUBJECT: Physics] [LANGUAGE: en]"},
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## Tavus Configuration

After deploying the bridge, update your Tavus Persona:

1. Go to Tavus → Personas → Your Physics Teacher
2. Click "Edit" or create new
3. In the **Layers** section, click **Language Model (LLM)**
4. Set:
   - **Model**: `ai-teacher`
   - **Base URL**: `https://your-bridge.up.railway.app`
   - **API Key**: `not-needed` (any string works)
   - **Speculative Inference**: `true`

5. Update **System Prompt** to include:
```
You are an expert Physics teacher.

[SUBJECT: Physics]
[CHAPTER: Mechanics]
[LESSON: Newton's Laws]
[LEVEL: High School]
[LANGUAGE: en]
[STUDENT: Student]
```

6. Save and test!

## Complete main.py Template

The main.py should:

1. Import: fastapi, httpx, json, asyncio, uuid, time, os
2. Create FastAPI app with CORS
3. Define Pydantic models for OpenAI format
4. Implement helper functions:
   - `extract_config_from_system_prompt()`
   - `get_conversation_id()`
   - `start_teacher_session()`
   - `send_message_to_teacher()`
   - `stream_response()`
5. Implement endpoints:
   - `GET /`
   - `GET /health`
   - `GET /v1/models`
   - `POST /v1/chat/completions`
6. Run with uvicorn

## Deployment Steps

1. Create new Railway project
2. Add new service (empty)
3. Connect GitHub repo OR upload files
4. Add environment variable: `TEACHER_API_URL=https://backend-teacher-production.up.railway.app`
5. Deploy
6. Copy the generated URL
7. Update Tavus persona with bridge URL

## Success Criteria

- [ ] Bridge responds to `/health` with `{"status": "healthy"}`
- [ ] Bridge can start sessions on your backend
- [ ] Bridge can send messages and get responses
- [ ] Streaming works (test with curl -N)
- [ ] Tavus avatar speaks the teacher responses
- [ ] Multi-language works (test with Arabic/French)