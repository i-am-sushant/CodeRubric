# CodeRubric - Presentation Script

## Project Overview

**Project Name:** CodeRubric  
**Tagline:** Context-Aware AI Code Review via RAG  
**Type:** Major Project / Final Year Project  

---

## Slide-by-Slide Presentation Script (10-15 minutes)

---

### **Slide 1: Title Slide**

**Content:**
- Title: CodeRubric
- Subtitle: Context-Aware AI Code Review via RAG
- Your Name, Roll Number, Institution
- GitHub: github.com/i-am-sushant/CodeRubric

**Speaker Notes:**
> "Good morning/afternoon everyone. Today I'll present my major project - CodeRubric, an intelligent code review system that solves a critical problem in AI-powered code reviews: the lack of codebase context."

---

### **Slide 2: The Problem**

**Content:**
- Traditional AI code reviews analyze code in isolation
- No understanding of project patterns, conventions, or existing architecture
- Generic suggestions that don't fit the codebase style
- Missed bugs due to lack of cross-file context

**Speaker Notes:**
> "Current AI code review tools like GitHub Copilot or ChatGPT analyze code snippets in isolation. They don't know your project's patterns, your team's coding conventions, or how different parts of your codebase interact. This leads to generic suggestions that often miss the bigger picture."

---

### **Slide 3: The Solution - RAG**

**Content:**
- **RAG** = Retrieval-Augmented Generation
- Index entire codebase into vector database
- Retrieve semantically similar code during review
- Enrich LLM prompts with relevant context

**Speaker Notes:**
> "CodeRubric solves this using RAG - Retrieval-Augmented Generation. Instead of reviewing code blindly, we first index the entire repository into a vector database. During review, we retrieve semantically similar code patterns and feed them to the AI along with the code being reviewed. This gives the AI context about your project's conventions and patterns."

---

### **Slide 4: System Architecture**

**Content:** [Architecture Diagram from README]

- Frontend: React + Nginx (Port 3000)
- Backend: FastAPI + Uvicorn (Port 8000)
- Database: PostgreSQL for reviews/repos (Port 5432)
- Vector Store: ChromaDB for RAG embeddings (Port 8001)
- Queue: Redis for background tasks (Port 6379)

**Speaker Notes:**
> "Our architecture uses a modern microservices approach. The React frontend communicates with a FastAPI backend. PostgreSQL stores review metadata, Redis handles background job queuing, and ChromaDB - a vector database - stores the code embeddings for our RAG pipeline. Everything runs in Docker containers for easy deployment."

---

### **Slide 5: Key Features**

**Content:**
1. **Dual-Mode Reviews**: Standard (fast) vs RAG-enhanced (context-aware)
2. **Web Dashboard**: Repository management, review configuration, real-time progress
3. **Quick Review**: Paste GitHub URL → get review in one step
4. **Ask About Code**: Natural language questions about code changes
5. **CLI Tool**: `gito review`, `gito answer` commands
6. **CI/CD Integration**: GitHub Actions for automated PR reviews

**Speaker Notes:**
> "CodeRubric offers dual-mode reviews - you can use standard mode for quick feedback, or enable RAG for deeper, context-aware analysis. The web dashboard lets you manage repositories and track reviews in real-time. We also provide a CLI tool called 'gito' for developers who prefer command-line workflows, and GitHub Actions integration for automated PR reviews."

---

### **Slide 6: RAG Pipeline Deep Dive**

**Content:**
```
Repository → Chunk Code → Generate Embeddings → Store in ChromaDB
                                            ↓
Review Request → Retrieve Similar Code → Enrich Prompt → AI Review
```

- Local embeddings using sentence-transformers (no API cost)
- Default model: all-MiniLM-L6-v2
- Semantic chunking of source files

**Speaker Notes:**
> "Let me explain our RAG pipeline. First, we clone and chunk the repository into meaningful code segments. We generate embeddings using a local sentence-transformers model - this means no additional API costs for embeddings. These are stored in ChromaDB. During review, we retrieve the most semantically similar code chunks and inject them into the LLM prompt, giving the AI crucial context."

---

### **Slide 7: Tech Stack**

**Content:**

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| Database | PostgreSQL 15, SQLAlchemy |
| Vector DB | ChromaDB |
| Queue | Redis |
| AI/ML | OpenAI/Google/Anthropic APIs, sentence-transformers |
| DevOps | Docker, Docker Compose, GitHub Actions |
| LLM Abstraction | ai-microcore (vendor-agnostic) |

**Speaker Notes:**
> "Our tech stack is modern and production-ready. React with TypeScript for the frontend, FastAPI for the backend, PostgreSQL and ChromaDB for data storage, and Redis for task queuing. We use ai-microcore for vendor-agnostic LLM access - users can switch between OpenAI, Google Gemini, Anthropic, or even local models with just environment variable changes."

---

### **Slide 8: Supported Providers**

**Content:**

**LLM Providers:**
- Google Gemini (free tier available)
- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude)
- OpenRouter / Mistral
- Azure OpenAI
- Local models (Ollama, vLLM)

**Git Platforms:**
- GitHub ✅
- GitLab ✅ (Beta)
- Bitbucket (Planned)

**Speaker Notes:**
> "CodeRubric is provider-agnostic. Users can choose from multiple LLM providers - even the free tier of Google Gemini works great. We support GitHub and GitLab for repository integration, with Bitbucket support planned."

---

### **Slide 9: Security & Privacy**

**Content:**
- **Zero-retention policy**: Code is never stored or logged
- **No middleman**: Direct transmission to your chosen LLM provider
- **Fully open source**: 100% auditable code
- **Self-hostable**: Run everything on your own infrastructure

**Speaker Notes:**
> "Security is a core principle. Unlike cloud-based tools that store your code, CodeRubric has a strict zero-retention policy. Your code is transmitted directly from your environment to your chosen LLM provider - no middleman, no storage, no logging. It's fully open source and self-hostable, so you maintain complete control."

---

### **Slide 10: Demo - Web Dashboard**

**Content:** [Screenshots of key pages]
- Dashboard with statistics
- Repository management page
- New Review configuration
- Review results with severity levels

**Speaker Notes:**
> "Let me walk you through the web dashboard. [Navigate to localhost:3000 if demoing live]. The dashboard shows statistics and quick actions. You can add repositories, configure reviews with RAG toggling, and view detailed results with severity indicators and proposed fixes."

---

### **Slide 11: Demo - CLI Tool**

**Content:**
```bash
# Standard review
gito review

# RAG-enhanced review
gito review --rag

# Review entire codebase
gito review --all

# Review remote repository
gito review --url https://github.com/user/repo

# Ask questions about code
gito answer "What does this function do?"
```

**Speaker Notes:**
> "For developers who prefer the command line, we offer the 'gito' CLI. Standard review compares your current branch to main. Add --rag for context-aware analysis. You can review entire codebases, remote repositories, or even ask natural language questions about your code changes."

---

### **Slide 12: GitHub Actions Integration**

**Content:**
```yaml
name: CodeRubric PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run CodeRubric Review
        uses: i-am-sushant/coderubric-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          llm-api-key: ${{ secrets.LLM_API_KEY }}
```

**Speaker Notes:**
> "For CI/CD integration, we provide a GitHub Action that automatically reviews pull requests and posts feedback as comments. This brings context-aware AI review directly into your development workflow."

---

### **Slide 13: Project Structure**

**Content:**
```
CodeRubric/
├── frontend/          # React web application
├── backend/           # FastAPI REST API
├── coderubric/        # Core RAG engine
├── gito/             # CLI tool
├── tests/            # Test suite
├── documentation/    # User guides
└── docker-compose.yml # One-command deployment
```

**Speaker Notes:**
> "Our codebase is well-organized. The frontend contains the React app, backend has the FastAPI server, coderubric/ contains the core RAG engine, and gito/ is the CLI tool. Everything is containerized with Docker Compose for easy deployment."

---

### **Slide 14: Development Timeline**

**Content:** [Adjust based on your actual timeline]

| Phase | Duration | Tasks |
|-------|----------|-------|
| Research | 2 weeks | RAG research, LLM comparison |
| Architecture | 1 week | System design, tech stack selection |
| Core Engine | 4 weeks | RAG pipeline, embeddings, vector DB |
| Web Dashboard | 3 weeks | Frontend, backend API, integration |
| CLI Tool | 2 weeks | Gito commands, packaging |
| Testing | 2 weeks | Unit tests, integration tests, bug fixes |
| Documentation | 1 week | README, guides, presentation |

**Speaker Notes:**
> "The project took approximately 15 weeks. We started with research on RAG techniques and LLM providers, then designed the architecture. The core RAG engine took the most time - implementing code chunking, embeddings, and vector storage. Then we built the web interface and CLI tool, followed by testing and documentation."

---

### **Slide 15: Challenges Faced**

**Content:**
1. **Code Chunking**: Determining optimal chunk sizes for different languages
2. **Embedding Quality**: Balancing speed vs accuracy for local embeddings
3. **Context Window**: Managing token limits when injecting context
4. **Real-time Updates**: WebSocket implementation for review progress
5. **Provider Abstraction**: Supporting multiple LLM APIs uniformly

**Speaker Notes:**
> "We faced several challenges. Code chunking was tricky - different languages need different strategies. We had to balance embedding quality with speed. Managing context window limits when injecting retrieved code required careful prompt engineering. WebSocket implementation for real-time progress tracking and creating a unified interface for multiple LLM providers were also significant challenges."

---

### **Slide 16: Results & Impact**

**Content:**
- Successfully implemented end-to-end RAG pipeline
- Context-aware reviews show improved relevance in testing
- Multiple LLM provider support gives users flexibility
- Open source with active documentation
- Docker-based deployment for easy adoption

**Speaker Notes:**
> "Our results: We successfully built a complete RAG-based code review system. Testing shows that RAG-enhanced reviews provide more relevant, context-aware feedback compared to standard AI reviews. The multi-provider support and Docker deployment make it accessible to a wide range of users."

---

### **Slide 17: Future Enhancements**

**Content:**
- Multi-language support expansion
- IDE plugins (VS Code, JetBrains)
- Advanced filtering and custom rules
- Team collaboration features
- Analytics dashboard for code quality trends
- Bitbucket and other Git platform support

**Speaker Notes:**
> "Future work includes IDE plugins for inline reviews, team collaboration features, analytics for tracking code quality over time, and expanding support to more Git platforms like Bitbucket."

---

### **Slide 18: Conclusion**

**Content:**
- CodeRubric brings context to AI code reviews via RAG
- Available as web dashboard, CLI, and GitHub Action
- Privacy-first, open source, self-hostable
- Demo: [http://localhost:3000] or [Your deployed URL]
- Repository: github.com/i-am-sushant/CodeRubric

**Speaker Notes:**
> "To conclude, CodeRubric addresses a real gap in AI code review tools by bringing codebase context through RAG. It's available as a web dashboard, CLI tool, and GitHub Action. It's privacy-first, fully open source, and easy to self-host. Thank you, and I'll now take any questions."

---

### **Slide 19: Q&A**

**Content:**
- Questions?
- Contact: [Your Email]
- GitHub: github.com/i-am-sushant/CodeRubric

---

## Additional Notes for Live Demo

### Pre-demo Checklist:
1. Start Docker containers: `docker compose up -d`
2. Verify all services are running
3. Have a sample repository ready for review
4. Clear browser cache if needed

### Demo Flow (5 minutes):
1. **Dashboard** (30 sec) - Show overview and stats
2. **Add Repository** (1 min) - Clone and index a repo
3. **New Review** (1 min) - Configure and start a review
4. **Results** (1 min) - Show issue details and severity
5. **Quick Review** (1 min) - Paste URL and review
6. **Settings** (30 sec) - Show LLM provider switching

### Backup Plan:
- If live demo fails, use pre-recorded screenshots
- Have slides with screenshot annotations ready

---

## Appendix: Key Talking Points

### What makes CodeRubric unique?
1. **True RAG implementation** - Not just prompt engineering, actual vector retrieval
2. **Privacy by design** - Zero retention, self-hostable
3. **Multi-modal** - Web, CLI, and CI/CD integration
4. **Provider agnostic** - Works with any major LLM provider

### Technical Depth Questions:
- **How does chunking work?** - We use semantic chunking based on AST parsing for supported languages, falling back to sliding window for others.
- **What's the embedding model?** - Default is all-MiniLM-L6-v2 (384 dimensions), runs locally.
- **How is context selected?** - Semantic similarity search + deduplication, top-k chunks within token budget.

### Comparison with existing tools:
- **vs GitHub Copilot**: Copilot doesn't use RAG for reviews, analyzes in isolation
- **vs CodeRabbit**: CodeRabbit is proprietary and stores code; we're open source with zero retention
- **vs SonarQube**: SonarQube uses static analysis rules; we use AI with RAG-enhanced context

---

## Estimated Timing

| Section | Duration |
|---------|----------|
| Introduction & Problem | 2 min |
| Solution & Architecture | 3 min |
| Features & RAG Pipeline | 3 min |
| Tech Stack & Security | 2 min |
| Demo | 5 min |
| Challenges & Results | 2 min |
| Conclusion & Q&A | 3 min |
| **Total** | **~20 min** |

---

Good luck with your presentation! 🎉
