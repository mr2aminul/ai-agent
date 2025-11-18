# AI Pr
oject Agent - Enterprise Development Platform

An advanced AI-powered development platform combining streaming chat, real-time collaboration, and intelligent code generation.

## Features

✨ **Streaming Chat**
- Token-by-token response display like ChatGPT
- Real-time processing indicators
- Multi-role message system (user, assistant, code-reviewer)

🔍 **Web Search Integration**
- Live information retrieval
- Latest documentation & libraries
- Source attribution

📋 **Auto-Workplan Generation**
- Multi-step task breakdown
- Priority & dependency management
- Multi-agent assignment

👥 **Multi-Agent Collaboration**
- Coder agent (code generation & implementation)
- Reviewer agent (code review & feedback)
- Tester agent (test generation & validation)
- Analyst agent (metrics & performance analysis)

📊 **Project Metrics Dashboard**
- Code coverage tracking
- Complexity analysis
- Dependency management
- Security vulnerability detection

🔀 **Advanced Code Management**
- Git patch generation & application
- Automated branch management
- Code review automation
- Test generation

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Zustand (State Management)
- Supabase JS Client

### Backend
- Flask 2.3
- Server-Sent Events (SSE)
- LM Studio (Local LLM)
- Chromadb (Vector DB)
- GitPython

### Database
- Supabase (PostgreSQL)
- Vector Search (Chromadb)
- Row-Level Security (RLS)

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- LM Studio (running on `localhost:1234`)
- Supabase account with project

### Installation

```bash
# Clone repository
git clone <repo-url>
cd ai-project-agent

# Install dependencies
npm install
pip install -r backend/requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your credentials
```

### Running Locally

```bash
# Terminal 1: Frontend (http://localhost:3000)
npm run dev

# Terminal 2: Backend (http://localhost:5000)
npm run backend

# Or both together
npm run dev-all
```

## Environment Variables

```env
# Frontend
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_LMSTUDIO_URL=http://localhost:1234/v1
VITE_DEFAULT_MODEL=gpt-oss-20b
VITE_WEB_SEARCH_API=duckduckgo

# Backend
PYTHON_LMSTUDIO_URL=http://localhost:1234/v1
PYTHON_DEFAULT_MODEL=gpt-oss-20b
PYTHON_CHROMA_DIR=./chroma_db
PYTHON_AGENT_DB=./agent_data.db
```

## Project Structure

```
ai-project-agent/
├── src/
│   ├── components/          # React components
│   ├── store/              # Zustand store
│   ├── lib/                # Utilities & API clients
│   ├── types/              # TypeScript definitions
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css            # Global styles
├── backend/
│   ├── app.py              # Flask server
│   └── requirements.txt      # Python dependencies
├── supabase/
│   └── migrations/          # Database migrations
├── index.html               # HTML template
├── vite.config.ts           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
├── package.json             # NPM configuration
└── tsconfig.json            # TypeScript configuration
```

## Database Schema

- **Projects**: Project metadata & paths
- **Conversations**: Chat sessions per project
- **Messages**: Chat messages with roles
- **Workplans**: Auto-generated task plans
- **Tasks**: Individual actionable items
- **Patches**: Code changes & diffs
- **Code Reviews**: Automated code reviews
- **Project Metrics**: Code metrics & analytics
- **Processing Logs**: AI processing stages
- **Web Search Results**: Cached search results
- **Indexed Files**: Project file tracking

## API Endpoints

### Chat & Generation
- `GET /api/chat/stream` - Streaming chat with SSE
- `POST /api/workplan/generate` - Generate workplans
- `POST /api/patch/generate` - Generate code patches

### Information
- `GET /api/models` - Available LM Studio models
- `GET /api/logs` - Backend status

## Key Features in Detail

### Streaming Chat
Real-time token-by-token response display with processing indicators showing context fetching, web search, and generation stages.

### Auto-Workplan
Converts instructions into structured workplans with prioritized tasks assigned to specific agents.

### Web Search
Integrates DuckDuckGo (with Google fallback) to fetch latest information and documentation.

### Code Review
Multi-level code review with security scanning, performance analysis, and auto-fix suggestions.

### Task Management
Full lifecycle management: pending → in_progress → completed → verified with agent assignment and priority tracking.

## Development

### Build
```bash
npm run build
```

### Type Check
```bash
npm run type-check
```

### Linting
```bash
npm run lint
```

## Performance Targets

- Chat Response Start: <5s
- Context Retrieval: <1s
- Workplan Generation: <10s
- Patch Generation: <15s

## Known Limitations

- Requires LM Studio running locally
- Chromadb embeddings stored locally
- Single-user per project (auth per project)
- No commercial API support yet

## Roadmap

- [ ] Real-time subscriptions
- [ ] Multi-agent execution
- [ ] Advanced security scanning
- [ ] CI/CD integration
- [ ] Team collaboration features
- [ ] Enterprise deployment

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- GitHub Issues
- Email: support@example.com

---

**Status**: Active Development
**Last Updated**: 2024
