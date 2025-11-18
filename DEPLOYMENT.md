
# Deployment & Setup Guide

## Quick Start (Local Development)

### 1. Prerequisites
```bash
# Required
- Node.js 18+
- Python 3.10+
- Git

# External Services
- Supabase account (free tier OK)
- LM Studio running on localhost:1234
```

### 2. Clone & Install

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Setup

```bash
# Copy example env
cp .env.example .env

# Edit .env with your Supabase credentials
nano .env
```

**Required environment variables:**
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_LMSTUDIO_URL=http://localhost:1234/v1
VITE_DEFAULT_MODEL=gpt-oss-20b
PYTHON_LMSTUDIO_URL=http://localhost:1234/v1
PYTHON_DEFAULT_MODEL=gpt-oss-20b
```

### 4. Start LM Studio

```bash
# Ensure LM Studio is running on port 1234
# See: https://lmstudio.ai/
```

### 5. Run Application

```bash
# Terminal 1: Frontend (port 3000)
npm run dev

# Terminal 2: Backend (port 5000)
npm run backend

# Or run both in one command
npm run dev-all
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

---

## Production Deployment

### Option 1: Docker Deployment

```dockerfile
# Dockerfile
FROM node:18-alpine as frontend-build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.10-slim
WORKDIR /app
COPY --from=frontend-build /app/dist /app/dist
COPY backend/ /app/backend/
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "backend/app.py"]
```

### Option 2: Vercel + Render

**Frontend (Vercel):**
```bash
# Configure build settings
- Framework: Vite
- Build: npm run build
- Output: dist
```

**Backend (Render):**
```bash
# Configure
- Runtime: Python 3.10
- Build: pip install -r requirements.txt
- Start: python backend/app.py
```

### Option 3: AWS Deployment

**Using EC2 + ALB:**

```bash
# Install on EC2 Ubuntu instance
sudo apt update
sudo apt install nodejs python3-pip git nginx

# Clone repo
git clone <repo-url>
cd ai-project-agent

# Install dependencies
npm install
pip install -r backend/requirements.txt

# Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/default
sudo systemctl start nginx

# Run with PM2
npm install -g pm2
pm2 start backend/app.py --name "backend"
pm2 start npm --name "frontend" -- run preview
pm2 save
```

---

## Supabase Setup

### 1. Create Project
- Go to https://supabase.com
- Create new project
- Save credentials to .env

### 2. Apply Migrations

```bash
# Using Supabase CLI
npm install -g @supabase/cli
supabase db push

# Or manually in Supabase SQL editor
# Copy content from supabase/migrations/*.sql
```

### 3. Enable RLS

All tables have RLS enabled with policies pre-configured. Verify in Supabase dashboard:
- Auth → Security Policies
- Confirm policies are active for each table

---

## LM Studio Setup

### 1. Install LM Studio
- Download from https://lmstudio.ai/
- Install for your OS

### 2. Load Model
1. Open LM Studio
2. Search for "gpt-oss-20b" (or preferred model)
3. Download model
4. Configure: Settings → Server → Port 1234
5. Click "Start Server"

### 3. Verify Connection
```bash
curl http://localhost:1234/v1/models
```

---

## Database Migrations

### Manual Migration

```bash
# If using Supabase CLI
supabase migration new create_conversations
# Add SQL to new file
supabase db push

# Or directly in SQL editor
# Copy from supabase/migrations/001_init_conversations_and_messages.sql
```

### Verify Migrations

```bash
# Check tables in Supabase
psql postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres

# List tables
\dt

# Verify RLS
\d+ conversations
```

---

## Environment Variables

### Frontend (.env)
```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_LMSTUDIO_URL=http://localhost:1234/v1
VITE_DEFAULT_MODEL=gpt-oss-20b
VITE_WEB_SEARCH_API=duckduckgo
```

### Backend (environment)
```
PYTHON_LMSTUDIO_URL=http://localhost:1234/v1
PYTHON_DEFAULT_MODEL=gpt-oss-20b
PYTHON_CHROMA_DIR=./chroma_db
PYTHON_AGENT_DB=./agent_data.db
WEB_SEARCH_API=duckduckgo
```

---

## Monitoring & Logs

### Frontend
```bash
# Dev mode logs
npm run dev

# Build logs
npm run build
```

### Backend
```bash
# Check server status
curl http://localhost:5000/health

# View logs
tail -f /var/log/backend.log
```

### Database
```bash
# Monitor real-time changes
supabase realtime on

# View query logs
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC;
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 3000
lsof -i :3000
# Kill it
kill -9 <PID>

# Find process using port 5000
lsof -i :5000
kill -9 <PID>
```

### Supabase Connection Failed

```bash
# Verify credentials
echo $VITE_SUPABASE_URL
echo $VITE_SUPABASE_ANON_KEY

# Test connection
curl -X GET https://your-project.supabase.co/rest/v1/projects \
  -H "apikey: $VITE_SUPABASE_ANON_KEY"
```

### LM Studio Not Responding

```bash
# Check if running
curl http://localhost:1234/v1/models

# Restart LM Studio
# Kill existing process and restart
pkill -f "lm-studio"
# Then restart LM Studio app
```

### Build Errors

```bash
# Clear cache
rm -rf node_modules dist .vite
npm install
npm run build

# Check Node version
node --version  # Should be 18+

# Check Python version
python --version  # Should be 3.10+
```

---

## Performance Optimization

### Frontend
```bash
# Build analysis
npm install -g webpack-bundle-analyzer
npm run build -- --visualizer

# Production build
npm run build

# Serve locally
npm run preview
```

### Backend
```bash
# Enable caching
# In Flask app
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Use database indexing
CREATE INDEX idx_conversation_user ON conversations(user_id);
```

### Database
```bash
# Optimize queries
ANALYZE;
VACUUM;

# Monitor slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

---

## Security

### API Keys
- Never commit `.env` to version control
- Use environment variables in production
- Rotate keys regularly

### Database
- Enable RLS on all tables (default: enabled)
- Use read-only keys for frontend
- Restrict IP access where possible

### Authentication
- Use Supabase Auth (built-in)
- Enable 2FA for accounts
- Use strong passwords

---

## Backup & Recovery

### Database Backup
```bash
# Automatic backups (Supabase)
# Enable in Settings → Database → Backups

# Manual backup
pg_dump postgresql://user:password@host:5432/db > backup.sql

# Restore
psql postgresql://user:password@host:5432/db < backup.sql
```

### Vector DB Backup
```bash
# Backup Chromadb
tar -czf chroma_backup.tar.gz chroma_db/

# Restore
tar -xzf chroma_backup.tar.gz
```

---

## Maintenance

### Weekly
- Check error logs
- Monitor LM Studio performance
- Verify backups

### Monthly
- Update dependencies (npm update, pip install --upgrade)
- Review security advisories
- Test disaster recovery

### Quarterly
- Database optimization
- Performance profiling
- Security audit

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npm run build
      - run: npm run type-check
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
```

---

**Last Updated**: 2024
**Status**: Ready for deployment
