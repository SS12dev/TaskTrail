# TaskTrail - AI-Powered Task Management

A modern, full-stack task management application with AI-powered assistance using multi-agent systems, real-time collaboration, and responsive design.

## 🌟 Features

- **Authentication & Authorization**: Secure Firebase authentication
- **Task Management**: Create, update, delete, and organize tasks with priorities and due dates
- **Project Management**: Organize tasks into projects with full CRUD operations
- **AI-Powered Assistance**: Multi-agent system for intelligent task suggestions and planning
- **Multiple Views**: 
  - Dashboard for overview
  - Calendar view for deadline tracking
  - Kanban board for task organization
  - Today view for daily focus
- **Real-time Updates**: WebSocket support for live collaboration
- **Theme Support**: Dark and light themes with persistent storage
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## 📋 Project Structure

```
TaskTrail/
├── backend/                      # FastAPI Python backend
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration settings
│   │   ├── firebase.py          # Firebase initialization
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── agents/              # Multi-agent system
│   │   │   ├── supervisor_agent.py
│   │   │   ├── conversation_agent.py
│   │   │   ├── executor_agent.py
│   │   │   ├── planner_agent.py
│   │   │   ├── query_agent.py
│   │   │   ├── multi_agent_system.py
│   │   │   └── tools/           # Agent tools
│   │   ├── routes/              # API endpoints
│   │   ├── models/              # Data models
│   │   ├── services/            # Business logic
│   │   └── a2a/                 # Agent-to-Agent communication
│   ├── requirements.txt         # Python dependencies
│   └── serviceAccountKey.json   # Firebase credentials (DO NOT COMMIT)
│
├── frontend/                     # React + TypeScript frontend
│   ├── src/
│   │   ├── main.tsx             # Application entry point
│   │   ├── App.tsx              # Root component
│   │   ├── components/          # Reusable components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API services
│   │   ├── stores/              # Zustand stores (state management)
│   │   ├── types/               # TypeScript types
│   │   ├── contexts/            # React contexts
│   │   └── styles/              # Design system
│   ├── package.json             # Node dependencies
│   ├── vite.config.ts           # Vite configuration
│   ├── tailwind.config.js       # Tailwind CSS configuration
│   └── tsconfig.json            # TypeScript configuration
│
├── mcp-server/                   # MCP server exposing the API to MCP clients
│   ├── src/tasktrail_mcp/
│   │   ├── server.py             # Entry point — wires up tools/resources/prompts
│   │   ├── client.py             # HTTP client for the backend REST API
│   │   ├── auth.py               # Firebase refresh-token -> ID token manager
│   │   ├── tools/                # tasks / projects / agent tool wrappers
│   │   ├── resources.py          # tasktrail:// read-only resources
│   │   └── prompts.py            # daily_standup, weekly_review, plan_project
│   ├── scripts/get_refresh_token.py  # one-time auth setup helper
│   └── tests/                    # mocked, no live backend required
│
└── docs/
    └── MCP_DESIGN.md              # MCP server design & architecture decisions
```

## 🔧 Tech Stack

### Backend
- **Framework**: FastAPI 0.115.6
- **Server**: Uvicorn
- **AI/ML**: LangChain, LangGraph, OpenAI
- **Authentication**: Firebase Admin SDK
- **Database**: Firebase Realtime Database
- **Language**: Python 3.x

### Frontend
- **Framework**: React 19
- **Language**: TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4
- **State Management**: Zustand
- **UI Components**: Lucide React (icons)
- **Drag & Drop**: dnd-kit
- **Routing**: React Router v7
- **Date Handling**: date-fns
- **HTTP Client**: Axios

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm/yarn
- Python 3.8+
- Firebase project with credentials

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (create `.env`):
   ```env
   FIREBASE_CREDENTIALS=path/to/serviceAccountKey.json
   OPENAI_API_KEY=your_openai_key
   FRONTEND_URL=http://localhost:5173
   ```

5. **Start the server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

Server will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure Firebase** (update `src/config/firebase.ts`):
   ```typescript
   export const firebaseConfig = {
     apiKey: "YOUR_API_KEY",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-project.appspot.com",
     messagingSenderId: "YOUR_SENDER_ID",
     appId: "YOUR_APP_ID"
   };
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

Application will be available at `http://localhost:5173`

### MCP Server Setup

Exposes TaskTrail to MCP clients (Claude Desktop, Claude Code) so an LLM can
manage your tasks conversationally. Requires the backend running and a
Firebase user account. Full design: [`docs/MCP_DESIGN.md`](./docs/MCP_DESIGN.md).

1. **Install [uv](https://docs.astral.sh/uv/)**, then:
   ```bash
   cd mcp-server
   uv sync --extra dev
   ```

2. **Get a refresh token** (one-time, needs your Firebase Web API key and a
   TaskTrail account email/password):
   ```bash
   uv run python scripts/get_refresh_token.py
   ```

3. **Configure** — copy `.env.example` to `.env` and fill in
   `FIREBASE_WEB_API_KEY` and `FIREBASE_REFRESH_TOKEN` from step 2.

4. **Run**:
   ```bash
   uv run tasktrail-mcp
   ```

See [`mcp-server/README.md`](./mcp-server/README.md) for the Claude Desktop
config snippet and full tool/resource/prompt reference.

## 🤖 AI Agent System

TaskTrail uses a multi-agent system architecture:

### Agents

1. **Supervisor Agent**: Routes user queries to appropriate agents
2. **Conversation Agent**: Maintains context-aware conversations
3. **Executor Agent**: Creates and modifies tasks and projects
4. **Planner Agent**: Suggests task organization and planning strategies
5. **Query Agent**: Retrieves and analyzes data

### How It Works

1. User sends a message to the AI assistant
2. Supervisor agent receives the message and routes it
3. Appropriate agents process the request (may chain multiple agents)
4. Response is formatted and sent back to frontend
5. Conversation history is maintained for context

### Agent Tools

- `create_task`: Create new tasks with details
- `update_task`: Modify existing tasks
- `delete_task`: Remove tasks
- `get_tasks`: Query tasks with filters
- `create_project`: Create new projects
- `query_projects`: Search and retrieve projects

## 📱 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout

### Tasks
- `GET /api/v1/tasks` - List all tasks
- `POST /api/v1/tasks` - Create task
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Agent
- `POST /api/v1/agent/chat` - Send message to AI agent
- `GET /api/v1/agent/capabilities` - List agent capabilities
- `GET /api/v1/agent/history` - Get conversation history
- `DELETE /api/v1/agent/history` - Clear conversation history

### A2A (Agent-to-Agent)
- `WebSocket /ws/a2a` - Agent communication channel

## 🧪 Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm run test
```

MCP server (mocked, no live backend needed):
```bash
cd mcp-server
uv run pytest
```

### Code Style

**Backend**: Follow PEP 8 with Black formatter
```bash
pip install black pylint
black app/
```

**Frontend**: Follow ESLint configuration
```bash
cd frontend
npm run lint
npm run lint -- --fix
```

### Building for Production

**Backend**: Deploy using any Python ASGI server (Heroku, PythonAnywhere, etc.)

**Frontend**:
```bash
cd frontend
npm run build
# dist/ folder contains optimized production build
```

## 🔐 Security

- **Never commit** `serviceAccountKey.json` or `.env` files
- Use environment variables for sensitive data
- Firebase security rules should be configured in Firebase Console
- API routes use Firebase authentication tokens
- CORS is configured for allowed origins only

## 📝 Environment Variables

### Backend (.env)
```
FIREBASE_CREDENTIALS=path/to/serviceAccountKey.json
OPENAI_API_KEY=your_openai_api_key
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=INFO
```

### Frontend (.env.local)
```
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

## 🐛 Troubleshooting

### Backend Issues

**CORS errors**:
- Ensure `FRONTEND_URL` is set correctly in `.env`
- Check `allowed_origins` in `app/main.py`

**Firebase connection failed**:
- Verify `serviceAccountKey.json` exists and is valid
- Check Firebase project is initialized
- Ensure Firebase credentials have proper permissions

**Agent not responding**:
- Check OpenAI API key is set
- Verify agent tools are registered
- Check application logs for detailed errors

### Frontend Issues

**Blank page on load**:
- Check browser console for errors
- Verify Firebase configuration in `src/config/firebase.ts`
- Ensure backend is running

**Theme not persisting**:
- Check browser localStorage is enabled
- Verify `ThemeContext` is properly initialized

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev)
- [Firebase Documentation](https://firebase.google.com/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [Tailwind CSS](https://tailwindcss.com/)

## 📄 License

This project is private and confidential.

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

---

**Last Updated**: January 2026
