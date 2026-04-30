# CodeRubric: Context-Aware Code Review via RAG

**Final Year Major Project** - An intelligent code review system that uses Retrieval-Augmented Generation (RAG) to provide context-aware analysis of code changes.

## Project Overview

CodeRubric enhances traditional AI code review by:
1. **Indexing** entire code repositories into a vector database (ChromaDB)
2. **Retrieving** semantically similar code patterns during review
3. **Enriching** LLM prompts with relevant context from the codebase
4. **Generating** more accurate, context-aware code review feedback

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI      │────▶│  FastAPI Backend  │────▶│  PostgreSQL DB  │
│   (Port 3000)   │     │   (Port 8000)    │     │   (Port 5432)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  RAG Pipeline    │
                        │  - OpenAI Embed   │
                        │  - ChromaDB Store │
                        │  - Context Retr.  │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Gito Core       │
                        │  - Git diff       │
                        │  - LLM review     │
                        │  - Report gen     │
                        └──────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- Git

### 1. Clone and Setup

```bash
git clone https://github.com/Sushant/CodeRubric.git
cd CodeRubric

# Create environment file
cp .env.example .env

# Edit .env with your API keys
# OPENAI_API_KEY=sk-your-key-here
```

### 2. Build and Run (Docker)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d
```

### 3. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Development Setup

### Backend Development

```bash
# Install Python dependencies
poetry install

# Run database migrations (if using PostgreSQL)
# Database tables are auto-created on startup

# Start backend in development mode
python backend/run.py
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
coderubric/
├── coderubric/              # RAG engine module
│   ├── rag/                # RAG components
│   │   ├── chunker.py     # Code chunking
│   │   ├── embedder.py    # OpenAI embeddings
│   │   ├── vector_store.py # ChromaDB wrapper
│   │   └── retriever.py   # Context retrieval
│   └── core/              # Enhanced review engine
│       └── rag_review.py  # RAG-enhanced review
│
├── backend/                # FastAPI backend
│   ├── api/               # API routes
│   │   ├── main.py       # FastAPI app
│   │   └── routes/       # Route handlers
│   ├── services/         # Business logic
│   └── database.py       # Database models
│
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Page components
│   │   └── api/          # API client
│   └── package.json
│
├── gito/                  # Original Gito codebase
│   ├── core.py           # Core review logic
│   └── cli.py            # CLI (now with --rag flag)
│
├── docker-compose.yml     # Docker orchestration
└── pyproject.toml        # Python dependencies
```

## Key Features

### 1. RAG-Enhanced Code Review
- **Embeddings**: Code chunks embedded using OpenAI `text-embedding-3-small`
- **Vector Store**: ChromaDB for efficient similarity search
- **Context Retrieval**: Retrieves relevant code patterns during review
- **Prompt Enhancement**: Injects retrieved context into LLM prompts

### 2. Web Dashboard
- **Repository Management**: Add and index repositories
- **Review Interface**: Start and monitor code reviews
- **Issue Visualization**: View detailed issue reports with code snippets
- **Real-time Progress**: WebSocket-based progress updates

### 3. Multiple Interfaces
- **Web UI**: Beautiful React dashboard
- **CLI**: Enhanced original `gito` CLI with `--rag` flag
- **API**: RESTful API for integration

## API Endpoints

### Repositories
- `GET /api/repos` - List repositories
- `POST /api/repos` - Add new repository
- `GET /api/repos/{id}/status` - Indexing status

### Reviews
- `GET /api/reviews` - List reviews
- `POST /api/reviews` - Create new review
- `GET /api/reviews/{id}` - Get review details
- `GET /api/reviews/{id}/issues` - Get review issues
- `WS /ws/review/{id}` - WebSocket for progress

### Statistics
- `GET /api/stats` - Overall statistics

## CLI Usage

### Standard Review (Original)
```bash
gito review
```

### RAG-Enhanced Review
```bash
# Index repository first
gito review --rag --rag-index-only

# Run RAG-enhanced review
gito review --rag
```

### Index Only
```bash
gito review --rag --rag-index-only
```

## Azure Deployment

### Option 1: Azure Container Apps

```bash
# Build and push images
az acr build --registry <your-registry> --image coderubric-backend:latest --file backend/Dockerfile .

# Deploy to Container Apps
az containerapp up \
  --resource-group myResourceGroup \
  --name coderubric \
  --image <your-registry>.azurecr.io/coderubric-backend:latest \
  --target-port 8000 \
  --env-vars "OPENAI_API_KEY=secretref:openai-key"
```

### Option 2: Docker Compose on Azure VM

```bash
# SSH into Azure VM
git clone <repo>
cd Gito
cp .env.example .env
# Edit .env with production values

docker-compose -f docker-compose.yml up -d
```

### Option 3: Azure Kubernetes Service (AKS)

See `k8s/` directory for Kubernetes manifests (if created).

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Yes |
| `LLM_API_KEY` | LLM API key for code review | Yes |
| `LLM_API_TYPE` | LLM provider (openai, anthropic, etc) | No (default: openai) |
| `MODEL` | Model name for code review | No (default: gpt-4o-mini) |
| `DATABASE_URL` | PostgreSQL connection string | No (default: local SQLite) |
| `REDIS_URL` | Redis connection string | No (default: local) |
| `VECTOR_STORE_PATH` | ChromaDB persistence path | No |

## Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **ChromaDB**: Vector database for embeddings
- **OpenAI**: Embeddings and LLM inference
- **GitPython**: Git repository operations

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **TanStack Query**: Server state management
- **TailwindCSS**: Styling
- **Lucide React**: Icons

### Infrastructure
- **Docker**: Containerization
- **PostgreSQL**: Relational database
- **Redis**: Caching and background tasks
- **Nginx**: Reverse proxy

## Project Report Sections

### 1. Introduction
- Problem statement: Traditional AI code reviews lack context
- Solution: RAG-enhanced context awareness
- Objectives and scope

### 2. Literature Review
- Existing code review tools
- RAG applications in software engineering
- Vector database technologies

### 3. System Design
- Architecture diagram
- Component interaction
- Data flow

### 4. Implementation
- RAG pipeline details
- Frontend dashboard design
- API design

### 5. Testing and Evaluation
- Test cases
- Performance metrics
- Comparison with non-RAG approach

### 6. Conclusion
- Summary of contributions
- Future enhancements

## Future Enhancements

1. **Multi-language support**: Expand chunking for more languages
2. **GitHub App**: Direct GitHub integration
3. **IDE Plugin**: VSCode/JetBrains extensions
4. **Custom Rules**: User-defined review rules
5. **Team Collaboration**: Multi-user support
6. **Advanced Analytics**: Code quality trends

## License

MIT License - See LICENSE file

## Contributors

- **Student**: [Your Name]
- **Guide**: [Guide Name]
- **Institution**: [Your College/University]

## Acknowledgments

This project is built upon the original **Gito** codebase by Vitalii Stepanenko and contributors.
