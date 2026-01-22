# Tavus Bridge - AI Teacher Integration

## What This Project Does

The Tavus Bridge is an OpenAI-compatible server that acts as a translation layer between Tavus avatar systems and your LangGraph AI Teacher backend.

**Problem Solved:**
- Tavus expects OpenAI API format (`/v1/chat/completions`)
- Your backend uses custom API format (`/api/v1/teacher/message`)
- This bridge translates between the two formats seamlessly

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────────────────────────┐
│    TAVUS     │────▶│    BRIDGE    │────▶│   LANGGRAPH BACKEND                 │
│   (Avatar)   │     │  (This app)  │     │   backend-teacher-production.       │
│              │◀────│              │◀────│   up.railway.app                    │
└──────────────┘     └──────────────┘     └─────────────────────────────────────┘
```

## Features

- ✅ OpenAI-compatible `/v1/chat/completions` endpoint
- ✅ Server-Sent Events (SSE) streaming support
- ✅ Automatic session management
- ✅ Configuration parsing from system prompts
- ✅ Multi-language support (English, Arabic, French)
- ✅ Health check endpoints
- ✅ Error handling with friendly messages
- ✅ CORS enabled for cross-origin requests

## How to Run Locally

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   # Windows (Command Prompt)
   set TEACHER_API_URL=https://backend-teacher-production.up.railway.app
   set PORT=8080

   # Windows (PowerShell)
   $env:TEACHER_API_URL="https://backend-teacher-production.up.railway.app"
   $env:PORT="8080"

   # Linux/Mac
   export TEACHER_API_URL=https://backend-teacher-production.up.railway.app
   export PORT=8080
   ```

3. **Run the server:**
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Verify it's running:**
   ```bash
   curl http://localhost:8080/health
   ```

   Expected response:
   ```json
   {"status": "healthy"}
   ```

## Testing the Bridge

### Test 1: Health Check
```bash
curl http://localhost:8080/health
```

### Test 2: List Models
```bash
curl http://localhost:8080/v1/models
```

### Test 3: Chat Completions (Non-Streaming)
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai-teacher",
    "stream": false,
    "messages": [
      {
        "role": "system",
        "content": "You are a physics teacher. [SUBJECT: Physics] [CHAPTER: Mechanics] [LESSON: Newton'\''s Laws] [LEVEL: High School] [LANGUAGE: en] [STUDENT: Ahmed]"
      },
      {
        "role": "user",
        "content": "Hello! What is Newton'\''s first law?"
      }
    ]
  }'
```

### Test 4: Chat Completions (Streaming)
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai-teacher",
    "stream": true,
    "messages": [
      {
        "role": "system",
        "content": "You are a physics teacher. [SUBJECT: Physics] [LANGUAGE: en]"
      },
      {
        "role": "user",
        "content": "Explain gravity in simple terms."
      }
    ]
  }' -N
```

Note: The `-N` flag disables buffering to see the streaming output in real-time.

## How to Deploy to Railway

### Method 1: Using Railway CLI (Recommended)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Initialize project:**
   ```bash
   railway init
   ```
   Follow the prompts to create/select a project

4. **Deploy:**
   ```bash
   railway up
   ```

5. **Add environment variable:**
   ```bash
   railway variables set TEACHER_API_URL=https://backend-teacher-production.up.railway.app
   ```

6. **Get your deployment URL:**
   ```bash
   railway domain
   ```

### Method 2: Using Railway Dashboard

1. Go to [railway.app](https://railway.app) and log in
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Connect your GitHub repository containing these files
4. Railway will automatically detect the Python setup
5. Add environment variable:
   - Go to **Variables** tab
   - Add: `TEACHER_API_URL` = `https://backend-teacher-production.up.railway.app`
6. Click **"Deploy"**
7. Wait for deployment to complete (1-2 minutes)
8. Copy the generated URL (e.g., `https://your-project.up.railway.app`)

### Verify Deployment

```bash
curl https://your-project.up.railway.app/health
```

Should return: `{"status": "healthy"}`

## Configuring Tavus

After deploying the bridge, configure your Tavus persona:

1. **Go to Tavus Dashboard**
   - Navigate to **Personas**
   - Select or create your Physics Teacher persona

2. **Configure LLM Settings**
   - Click **"Edit"** on the persona
   - Find the **"Language Model (LLM)"** section
   - Set these values:
     ```
     Model: ai-teacher
     Base URL: https://your-project.up.railway.app
     API Key: not-needed (any string works)
     Speculative Inference: true
     ```

3. **Update System Prompt**
   Add configuration tags to the system prompt:
   ```
   You are an expert Physics teacher for high school students.

   [SUBJECT: Physics]
   [CHAPTER: Mechanics]
   [LESSON: Newton's Laws]
   [LEVEL: High School]
   [LANGUAGE: en]
   [STUDENT: Student]
   ```

4. **Save and Test**
   - Save the persona
   - Test with the Tavus avatar
   - The avatar should now speak responses from your AI Teacher backend

## Configuration Options

### System Prompt Tags

Include these tags in the Tavus system prompt to configure the session:

- `[SUBJECT: Physics]` - The subject being taught
- `[CHAPTER: Mechanics]` - Current chapter/topic
- `[LESSON: Newton's Laws]` - Specific lesson
- `[LEVEL: High School]` - Education level
- `[LANGUAGE: en]` - Language code (en, ar, fr)
- `[STUDENT: Ahmed]` - Student's name

### Environment Variables

- `TEACHER_API_URL` - Your backend API URL (required)
- `PORT` - Port to run on (default: 8080)

## API Endpoints

### GET /
Service information
```json
{
  "service": "Tavus Bridge",
  "version": "1.0.0",
  "status": "running",
  "description": "OpenAI-compatible bridge for Tavus avatars",
  "backend": "https://backend-teacher-production.up.railway.app"
}
```

### GET /health
Health check
```json
{
  "status": "healthy"
}
```

### GET /v1/models
List available models
```json
{
  "object": "list",
  "data": [
    {"id": "ai-teacher", "object": "model"},
    {"id": "tavus-bridge", "object": "model"}
  ]
}
```

### POST /v1/chat/completions
Main chat endpoint (OpenAI-compatible)

**Request:**
```json
{
  "model": "ai-teacher",
  "stream": true,
  "messages": [
    {"role": "system", "content": "You are a teacher. [SUBJECT: Physics] [LANGUAGE: en]"},
    {"role": "user", "content": "Hello!"}
  ]
}
```

**Response (Streaming):**
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"ai-teacher","choices":[{"index":0,"delta":{"content":"Hello "},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"ai-teacher","choices":[{"index":0,"delta":{"content":"world!"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"ai-teacher","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

## Troubleshooting

### Bridge returns "I'm having a small issue"
- Check your backend is accessible: `curl https://backend-teacher-production.up.railway.app/health`
- Verify `TEACHER_API_URL` environment variable is set correctly
- Check Railway logs for error details

### Streaming not working
- Ensure `stream: true` is in the request
- Use `-N` flag with curl to disable buffering
- Check network/firewall settings

### Session not persisting
- The bridge uses in-memory storage
- Sessions reset on redeployment
- This is expected behavior for stateless deployment

### CORS errors
- The bridge has CORS enabled for all origins
- If you still see errors, check browser console for details

## Project Structure

```
tavus-bridge/
├── main.py           # FastAPI application with all logic
├── requirements.txt  # Python dependencies
├── Procfile          # Railway start command
├── railway.json      # Railway configuration
├── README.md         # This file
└── claude.md         # Original specification
```

## Technical Details

- **Framework**: FastAPI
- **HTTP Client**: httpx (async)
- **Session Management**: In-memory dictionary
- **Streaming**: Word-by-word with 20ms delays
- **Conversation Tracking**: MD5 hash of system prompt
- **Error Handling**: Graceful degradation with user-friendly messages

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Railway logs in the dashboard
3. Verify backend API is accessible
4. Test with curl examples provided

## License

This project is part of the AI Teacher system.
