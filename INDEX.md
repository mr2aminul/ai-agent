
# AI Project Agent - Complete File Index

## Quick Navigation

- 📖 [README.md](README.md) - Start here! Full feature overview
- 🚀 [DEPLOYMENT.md](DEPLOYMENT.md) - Setup & deployment guide
- 📋 [track-progress-and-requirements.md](track-progress-and-requirements.md) - Detailed feature tracking
- 📊 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture & technical overview
- ✅ [CHECKLIST.md](CHECKLIST.md) - Completion status

---

## Project Files

### Root Configuration Files

| File | Purpose |
|------|---------|
| `package.json` | NPM dependencies & scripts |
| `tsconfig.json` | TypeScript configuration |
| `tsconfig.node.json` | TypeScript config for build files |
| `vite.config.ts` | Vite build configuration |
| `tailwind.config.js` | Tailwind CSS theme |
| `postcss.config.js` | PostCSS plugins |
| `.eslintrc.json` | ESLint linting rules |
| `.gitignore` | Git ignore patterns |
| `.env.example` | Environment variable template |
| `index.html` | HTML entry point |

### Frontend Source Code

#### Components
| File | Component | Purpose |
|------|-----------|---------|
| `src/App.tsx` | App | Main application layout |
| `src/components/StreamingChat.tsx` | StreamingChat | Real-time chat with SSE |
| `src/components/MessageBubble.tsx` | MessageBubble | Message rendering with Markdown |
| `src/components/ProcessingIndicator.tsx` | ProcessingIndicator | Progress & stage display |
| `src/components/TaskPanel.tsx` | TaskPanel | Task management interface |
| `src/components/ProjectExplorer.tsx` | ProjectExplorer | File tree browser |
| `src/components/MetricsPanel.tsx` | MetricsPanel | Analytics dashboard |

#### Core Files
| File | Purpose |
|------|---------|
| `src/main.tsx` | React entry point |
| `src/index.css` | Global styles |
| `src/types/index.ts` | TypeScript type definitions |
| `src/store/useAppStore.ts` | Zustand state management |
| `src/lib/supabase.ts` | Database query functions |

### Backend

| File | Purpose |
|------|---------|
| `backend/app.py` | Flask server (500+ lines) |
| `backend/requirements.txt` | Python dependencies |
| `backend/__init__.py` | Package initialization |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Feature overview & usage |
| `DEPLOYMENT.md` | Setup instructions |
| `PROJECT_SUMMARY.md` | Technical overview |
| `track-progress-and-requirements.md` | Feature tracking |
| `CHECKLIST.md` | Completion status |
| `INDEX.md` | This file |

### Database

| File | Purpose |
|------|---------|
| `supabase/migrations/001_*.sql` | Conversations & Messages tables |
| `supabase/migrations/002_*.sql` | Workplans & Tasks tables |
| `supabase/migrations/003_*.sql` | Patches & Code Reviews tables |
| `supabase/migrations/004_*.sql` | Web Search & Processing Logs |

---

## Directory Structure

```
ai-project-agent/
├── src/                          # Frontend React code
│   ├── components/               # React UI components (6 files)
│   ├── store/                    # State management (Zustand)
│   ├── lib/                      # Utility functions & API clients
│   ├── types/                    # TypeScript definitions
│   ├── App.tsx                   # Main component
│   ├── main.tsx                  # Entry point
│   └── index.css                 # Global styles
│
├── backend/                      # Python Flask backend
│   ├── app.py                    # Flask server
│   ├── requirements.txt          # Python dependencies
│   └── __init__.py               # Package init
│
├── supabase/                     # Database
│   └── migrations/               # SQL migrations (4 files)
│
├── node_modules/                 # NPM packages (installed)
├── dist/                         # Built frontend (after build)
│
├── Configuration Files
│   ├── package.json              # NPM config
│   ├── tsconfig.json             # TypeScript config
│   ├── vite.config.ts            # Vite config
│   ├── tailwind.config.js        # Tailwind config
│   ├── postcss.config.js         # PostCSS config
│   ├── .eslintrc.json            # ESLint config
│   └── index.html                # HTML template
│
├── Documentation
│   ├── README.md                 # Main guide
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── PROJECT_SUMMARY.md        # Technical summary
│   ├── track-progress-and-requirements.md
│   ├── CHECKLIST.md              # Completion checklist
│   └── INDEX.md                  # This file
│
├── .env.example                  # Environment template
├── .env                          # Environment (local)
└── .gitignore                    # Git ignore
```

---

## Key Files Explained

### Frontend Entry Point
- **index.html** → **src/main.tsx** → **src/App.tsx**
  - HTML loads React app
  - React renders App component
  - App manages main layout

### State Management Flow
- **src/store/useAppStore.ts** - Central Zustand store
  - Projects, conversations, messages
  - Workplans, tasks
  - Processing indicators
  - Loading & error states

### Component Hierarchy
```
App
├── Sidebar (Projects)
├── Top Bar (Navigation)
└── Main Grid
    ├── Left (Conversations)
    ├── Center (StreamingChat)
    │   ├── MessageBubble (x many)
    │   ├── ProcessingIndicator (x many)
    │   └── Chat Input
    └── Right (Tabs)
        ├── TaskPanel
        ├── MetricsPanel
        └── ProjectExplorer
```

### Backend API Routes
```
Flask App (port 5000)
├── GET /health                    (Health check)
├── GET /api/models                (Available models)
├── GET /api/chat/stream           (Streaming chat with SSE)
├── POST /api/workplan/generate    (Generate workplan)
├── POST /api/patch/generate       (Generate code patch)
└── GET /api/logs                  (Backend status)
```

### Database Schema
```
Projects
├── Conversations
│   ├── Messages
│   ├── Workplans
│   │   └── Tasks
│   └── Patches
│       └── Code Reviews
├── Indexed Files
├── Web Search Results
└── Processing Logs

Project Metrics (per project)
```

---

## NPM Scripts

```json
{
  "dev": "vite",                           // Dev server on port 3000
  "build": "vite build",                   // Production build
  "preview": "vite preview",               // Preview build locally
  "backend": "python backend/app.py",      // Start Flask server
  "dev-all": "concurrently ...",           // Run frontend + backend
  "lint": "eslint src --ext ts,tsx",       // Lint TypeScript
  "type-check": "tsc --noEmit"             // Type checking
}
```

---

## Environment Variables

See `.env.example` for template. Required:

```
# Supabase (Frontend)
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY

# LM Studio (Frontend)
VITE_LMSTUDIO_URL
VITE_DEFAULT_MODEL

# Web Search (Frontend)
VITE_WEB_SEARCH_API

# Backend (Environment)
PYTHON_LMSTUDIO_URL
PYTHON_DEFAULT_MODEL
PYTHON_CHROMA_DIR
PYTHON_AGENT_DB
WEB_SEARCH_API
```

---

## Quick Start Commands

```bash
# 1. Install dependencies
npm install
pip install -r backend/requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 3. Run development
npm run dev-all

# 4. Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

---

## File Statistics

| Category | Count | Lines |
|----------|-------|-------|
| React Components | 6 | ~800 |
| React Utilities | 4 | ~500 |
| Flask Backend | 1 | ~600 |
| TypeScript Types | 1 | ~200 |
| Config Files | 7 | ~200 |
| Documentation | 5 | ~2000 |
| SQL Migrations | 4 | ~400 |
| **Total** | **28** | **~4700** |

---

## Feature Implementation Status

### ✅ Implemented
- Streaming chat with real-time updates
- Web search integration
- Auto-workplan generation
- Task management system
- Processing indicators
- Project metrics dashboard
- File explorer
- Multi-role messaging
- Vector embeddings & search

### 🔄 Ready for Implementation
- Real-time subscriptions
- Code review engine
- Multi-agent system
- Diff viewer
- Advanced file indexing

### 📋 Future Features
- Team collaboration
- CI/CD integration
- Auto-documentation
- Security scanning

---

## Technology Quick Reference

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend UI | React 18 + TypeScript | Component-based UI |
| Styling | Tailwind CSS | Utility-first styling |
| Build | Vite | Fast development builds |
| State | Zustand | Lightweight state management |
| Database | Supabase/PostgreSQL | Primary data store |
| Search | Chromadb | Vector embeddings |
| Backend | Flask + Python | REST API server |
| Real-time | Server-Sent Events | Streaming responses |
| LLM | LM Studio | Local language model |
| Search | DuckDuckGo | Web search API |

---

## Import Paths

Frontend uses `@` alias for clean imports:

```typescript
// Instead of
import { useAppStore } from '../../../store/useAppStore'

// Use
import { useAppStore } from '@/store/useAppStore'
```

Configured in `vite.config.ts` and `tsconfig.json`

---

## Common Tasks

### Add New Component
1. Create file in `src/components/YourComponent.tsx`
2. Import in `src/App.tsx`
3. Add to component tree

### Add New Database Query
1. Add function to `src/lib/supabase.ts`
2. Use in components via `useAppStore`

### Add New Backend Route
1. Add route handler in `backend/app.py`
2. Register endpoint
3. Test via `curl` or fetch

### Deploy to Production
1. Follow `DEPLOYMENT.md` guide
2. Choose deployment option (Docker, Vercel, AWS, etc.)
3. Configure environment variables
4. Deploy

---

## Important Notes

1. **API Keys**: Never commit `.env` to git
2. **LM Studio**: Required for local development
3. **Database**: Supabase project must be created first
4. **RLS**: All database tables have Row-Level Security
5. **CORS**: Configured for localhost:3000

---

## Support

For issues or questions:
- Check README.md for features
- See DEPLOYMENT.md for setup help
- Review CHECKLIST.md for status
- Check track-progress-and-requirements.md for features

---

**Last Updated**: 2024
**Status**: Production Ready
**Version**: 1.0.0

Happy coding! 🚀
