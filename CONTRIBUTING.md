# Contributing to TaskTrail

## Development Guidelines

### Code Standards

#### Backend (Python)
- Follow PEP 8 style guide
- Use type hints for all functions
- Document functions with docstrings
- Keep functions focused and small
- Use meaningful variable names

Example:
```python
def create_task(
    user_id: str,
    title: str,
    priority: str = "medium"
) -> Task:
    """Create a new task for the user.
    
    Args:
        user_id: Firebase user ID
        title: Task title
        priority: Priority level (low, medium, high)
        
    Returns:
        Created Task object
    """
    # Implementation
    pass
```

#### Frontend (TypeScript/React)
- Use functional components with hooks
- Define proper TypeScript types
- Use meaningful component names
- Keep components focused on single responsibility
- Extract reusable logic into custom hooks

Example:
```typescript
interface TaskProps {
  taskId: string;
  onComplete: (id: string) => void;
}

export const TaskCard: React.FC<TaskProps> = ({ taskId, onComplete }) => {
  // Implementation
};
```

### Commit Message Format

Follow conventional commit format:

```
type(scope): subject

body

footer
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding/updating tests
- `chore`: Build, dependencies, etc.

**Examples**:
```
feat(agent): add planner agent for task suggestions
fix(tasks): resolve date picker timezone issue
docs(readme): update installation instructions
refactor(services): simplify agent service architecture
```

### Branch Naming

Use descriptive branch names:
- `feature/agent-improvements`
- `fix/theme-toggle-bug`
- `docs/api-documentation`
- `refactor/task-service`

### Testing

**Backend**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_supervisor_routing
```

**Frontend**:
```bash
# Run tests
npm run test

# Run with coverage
npm run test -- --coverage
```

### Code Review Checklist

Before submitting changes:

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] No console errors or warnings
- [ ] Commit messages are descriptive
- [ ] Documentation is updated if needed
- [ ] No sensitive data in commits (keys, tokens, passwords)
- [ ] Breaking changes are documented

### Working on Features

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit regularly:
   ```bash
   git add .
   git commit -m "feat(scope): description of change"
   ```

3. **Keep your branch updated**:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Working on Bugs

1. **Create a fix branch**:
   ```bash
   git checkout -b fix/bug-description
   ```

2. **Write a test that reproduces the bug** (if applicable)

3. **Fix the bug** and ensure tests pass

4. **Commit and push**:
   ```bash
   git commit -m "fix(scope): description of fix"
   git push origin fix/bug-description
   ```

## Architecture

### Backend Structure

```
app/
├── agents/              # Multi-agent system (LangChain/LangGraph)
├── routes/              # API endpoints
├── models/              # Data models/schemas
├── services/            # Business logic
├── a2a/                 # Agent-to-Agent communication
└── tools/               # Agent tools
```

### Adding a New Agent

1. Create new file in `backend/app/agents/your_agent.py`
2. Extend `BaseSupervisor` or implement agent interface
3. Define agent prompt and tools
4. Register in `multi_agent_system.py`
5. Add tests

### Adding a New API Route

1. Create route file in `backend/app/routes/`
2. Define request/response models in `models/`
3. Implement service logic in `services/`
4. Add appropriate authentication checks
5. Document endpoints

### Frontend Structure

```
src/
├── components/          # Reusable UI components
├── pages/              # Page-level components
├── hooks/              # Custom React hooks
├── services/           # API communication
├── stores/             # State management (Zustand)
├── types/              # TypeScript definitions
└── contexts/           # React contexts
```

### Adding a New Page

1. Create component in `src/pages/YourPage.tsx`
2. Add route in `App.tsx`
3. Create corresponding store if needed
4. Add to navigation/menu
5. Add types in `src/types/`

### Adding a New Component

1. Create component in `src/components/`
2. Define TypeScript interface for props
3. Use Tailwind for styling
4. Document props with JSDoc comments
5. Export from `index.ts` if in subdirectory

## Common Tasks

### Adding a New Dependency

**Backend**:
```bash
cd backend
pip install package-name
pip freeze > requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install package-name
```

### Running Backend in Debug Mode

```bash
cd backend
uvicorn app.main:app --reload --log-level debug
```

### Running Frontend with React DevTools

DevTools browser extension will automatically work with development build.

### Checking for Type Errors

**Frontend**:
```bash
cd frontend
npx tsc --noEmit
```

## Common Issues

### Backend won't start
- Check if port 8000 is available
- Verify Python version is 3.8+
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`
- Check if port 5173 is available

### API calls failing
- Verify backend is running
- Check CORS settings in `app/main.py`
- Verify Firebase configuration

## Questions?

- Check existing code for similar implementations
- Review commit history for context
- Ask in team discussions
- Check documentation in code comments

---

**Last Updated**: January 2026
