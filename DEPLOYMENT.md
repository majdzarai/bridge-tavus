# Quick Deployment Guide - Tavus Bridge

## 🚀 Deploy to Railway (3 Methods)

### Method 1: Railway CLI (Fastest - Recommended)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project in this directory
railway init
# Select "Create New Project" or choose existing

# 4. Deploy
railway up

# 5. Add environment variable
railway variables set TEACHER_API_URL=https://backend-teacher-production.up.railway.app

# 6. Get your deployment URL
railway domain
# Copy this URL for Tavus configuration
```

### Method 2: Railway Dashboard (GUI)

1. **Create Project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Click "Deploy from GitHub repo"

2. **Connect Repository**
   - Click "New Repo" or select existing
   - Choose this project directory
   - Or push to GitHub first and select that repo

3. **Configure**
   - Railway will auto-detect Python
   - Go to "Variables" tab
   - Add: `TEACHER_API_URL` = `https://backend-teacher-production.up.railway.app`

4. **Deploy**
   - Click "Deploy" button
   - Wait 1-2 minutes
   - Copy the generated URL

### Method 3: Direct Upload (No GitHub)

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Create and Deploy**
   ```bash
   railway init
   railway up
   railway variables set TEACHER_API_URL=https://backend-teacher-production.up.railway.app
   ```

## 📋 Verify Deployment

```bash
# Replace YOUR_URL with your actual Railway URL
curl https://YOUR-URL.up.railway.app/health
```

Expected response:
```json
{"status": "healthy"}
```

## 🔗 Configure Tavus

1. **Open Tavus Dashboard**
   - Go to Personas
   - Select your Physics Teacher persona

2. **Edit LLM Settings**
   - Model: `ai-teacher`
   - Base URL: `https://YOUR-URL.up.railway.app`
   - API Key: `not-needed` (any string works)
   - Speculative Inference: `true`

3. **Update System Prompt**
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

## 🧪 Test Locally Before Deploying

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables (Windows Command Prompt)
set TEACHER_API_URL=https://backend-teacher-production.up.railway.app
set PORT=8080

# Or Windows PowerShell
$env:TEACHER_API_URL="https://backend-teacher-production.up.railway.app"
$env:PORT="8080"

# 3. Run the server
python main.py

# 4. Test in another terminal
curl http://localhost:8080/health

# 5. Test chat endpoint
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai-teacher",
    "stream": false,
    "messages": [
      {
        "role": "system",
        "content": "You are a physics teacher. [SUBJECT: Physics] [LANGUAGE: en]"
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TEACHER_API_URL` | Yes | - | Your LangGraph backend URL |
| `PORT` | No | 8080 | Port to run the server on |

## 📊 Monitor Your Deployment

```bash
# View logs
railway logs

# View status
railway status

# Open in browser
railway open

# View domains
railway domain
```

## 🐛 Troubleshooting

### Deployment Fails
- Check Railway logs: `railway logs`
- Verify requirements.txt is correct
- Ensure Python 3.10+ is available

### Health Check Fails
- Verify backend is accessible: `curl https://backend-teacher-production.up.railway.app/health`
- Check TEACHER_API_URL environment variable
- Review Railway deployment logs

### Tavus Not Responding
- Verify Base URL is correct (no trailing slash)
- Check Model name is "ai-teacher"
- Verify Speculative Inference is enabled
- Check Tavus logs for errors

### Streaming Issues
- Ensure `stream: true` in request
- Check network connectivity
- Verify CORS is enabled (should be by default)

## 📝 Post-Deployment Checklist

- [ ] Health check returns `{"status": "healthy"}`
- [ ] `/v1/models` endpoint returns models list
- [ ] Chat completions work (test with curl)
- [ ] Streaming works (test with `-N` flag)
- [ ] Tavus persona configured with bridge URL
- [ ] Tavus avatar speaks responses correctly
- [ ] Multi-language support works (test with different [LANGUAGE: xx] tags)

## 🎯 Quick Test Commands

```bash
# Test 1: Health Check
curl https://YOUR-URL.up.railway.app/health

# Test 2: List Models
curl https://YOUR-URL.up.railway.app/v1/models

# Test 3: Simple Chat (Non-Streaming)
curl -X POST https://YOUR-URL.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"ai-teacher","stream":false,"messages":[{"role":"system","content":"You are a teacher. [SUBJECT: Physics] [LANGUAGE: en]"},{"role":"user","content":"Hello!"}]}'

# Test 4: Streaming Chat
curl -X POST https://YOUR-URL.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"ai-teacher","stream":true,"messages":[{"role":"system","content":"You are a teacher. [SUBJECT: Physics] [LANGUAGE: en]"},{"role":"user","content":"Hello!"}]}' -N

# Test 5: Arabic Language
curl -X POST https://YOUR-URL.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"ai-teacher","stream":false,"messages":[{"role":"system","content":"أنت مدرس فيزياء. [SUBJECT: Physics] [LANGUAGE: ar]"},{"role":"user","content":"مرحبا!"}]}'
```

## 🔄 Update Deployment

```bash
# Make changes to code
# Then redeploy
railway up
```

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Tavus Documentation](https://docs.tavus.ai)

## 💡 Tips

1. **Use Railway CLI** for faster deployments
2. **Test locally first** to catch issues early
3. **Monitor logs** during initial testing
4. **Keep backups** of working configurations
5. **Use environment variables** for all configuration

## 🎉 Success!

If you've completed all steps, your Tavus Bridge should be:
- ✅ Deployed on Railway
- ✅ Connected to your backend
- ✅ Ready for Tavus integration
- ✅ Serving teacher responses to avatars

Enjoy your AI Teacher integration with Tavus! 🚀
