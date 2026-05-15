# CodeRubric

**Context-Aware AI Code Review via RAG**

An intelligent code review system that combines the [Gito](https://github.com/Sushant/CodeRubric) code review engine with Retrieval-Augmented Generation (RAG) to provide context-aware analysis of code changes. Available as a web dashboard, REST API, and CLI.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Supported Platforms & Providers](#supported-platforms--providers)
- [Security & Privacy](#security--privacy)
- [Quickstart (Docker — Web Dashboard)](#quickstart-docker--web-dashboard)
- [Web Dashboard Guide](#web-dashboard-guide)
- [Gito CLI Tool](#gito-cli-tool)
  - [GitHub Actions (PR Reviews)](#github-actions-pr-reviews)
  - [Local Installation](#local-installation)
  - [CLI Commands](#cli-commands)
  - [CLI Configuration](#cli-configuration)
- [API Reference](#api-reference)
- [Configuration (Web App)](#configuration-web-app)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Guides & Reference](#guides--reference)
- [Known Limitations](#known-limitations)
- [Deploying on Azure (Single VM)](#deploying-on-azure-single-vm)
- [CI/CD — GitHub Actions for PR Reviews](#cicd--github-actions-for-pr-reviews)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

CodeRubric enhances traditional AI code review by:

1. **Indexing** entire code repositories into a vector database (ChromaDB)
2. **Retrieving** semantically similar code patterns during review
3. **Enriching** LLM prompts with relevant codebase context
4. **Generating** more accurate, context-aware review feedback

It supports **dual-mode reviews**: standard (lightweight, no indexing required) and RAG-enhanced (uses indexed codebase context for deeper analysis).

---

## Architecture

```
                          ┌────────────────────────────────────────┐
                          │            Docker Compose              │
                          │                                        │
┌──────────────┐          │  ┌─────────────┐    ┌──────────────┐  │
│   Browser    │◄────────►│  │  Nginx      │───►│  FastAPI      │  │
│              │  :3000   │  │  (Frontend)  │    │  (Backend)    │  │
└──────────────┘          │  └─────────────┘    └──────┬───────┘  │
                          │                            │          │
                          │              ┌─────────────┼────────┐ │
                          │              ▼             ▼        ▼ │
                          │  ┌──────────────┐ ┌────────────┐ ┌──────┐
                          │  │ PostgreSQL   │ │  ChromaDB  │ │Redis │
                          │  │  (Reviews,   │ │  (Vector   │ │      │
                          │  │   Repos)     │ │   Store)   │ │      │
                          │  └──────────────┘ └────────────┘ └──────┘
                          │                                        │
                          │  ┌─────────────────────────────────┐   │
                          │  │         Backend Modules          │   │
                          │  │  ┌───────────┐  ┌────────────┐  │   │
                          │  │  │ Gito Core │  │ CodeRubric │  │   │
                          │  │  │ (Diff,    │  │ RAG Engine │  │   │
                          │  │  │  Review,  │  │ (Embed,    │  │   │
                          │  │  │  Answer)  │  │  Retrieve, │  │   │
                          │  │  └─────┬─────┘  │  Review)   │  │   │
                          │  │        │        └────────────┘  │   │
                          │  │        ▼                        │   │
                          │  │  ┌───────────┐                  │   │
                          │  │  │ microcore │ LLM-agnostic     │   │
                          │  │  │ (Google,  │ inference layer   │   │
                          │  │  │  OpenAI,  │                  │   │
                          │  │  │  Anthropic)│                 │   │
                          │  │  └───────────┘                  │   │
                          │  └─────────────────────────────────┘   │
                          └────────────────────────────────────────┘
```

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3000 | React + Nginx (serves UI and proxies `/api/` to backend) |
| **Backend** | 8000 | FastAPI + Uvicorn |
| **PostgreSQL** | 5432 | Stores repositories, reviews, issues |
| **ChromaDB** | 8001 | Vector store for RAG embeddings |
| **Redis** | 6379 | Background task queue |

---

## Features

### Web Dashboard
- **Repository Management** — Add repos by URL, specify branch, clone and index for RAG
- **New Review** — Select repo, branches, toggle RAG on/off, set file filters, review entire codebase
- **Quick Review** — Paste a GitHub URL and run a one-step clone + review
- **Ask About Code** — Ask natural-language questions about code changes (uses Gito's `answer()`)
- **Review Details** — View issues by severity with affected code snippets and proposed fixes
- **Real-time Progress** — WebSocket-based progress tracking during reviews
- **Settings** — Change LLM provider, API key, and model at runtime (no restart needed)
- **Dashboard** — Statistics overview and quick actions

### RAG Pipeline
- **Code Chunking** — Splits source files into semantically meaningful chunks
- **Local Embeddings** — Uses `sentence-transformers` (default: `all-MiniLM-L6-v2`) — no external API key needed
- **ChromaDB** — Persistent vector storage, shared via Docker volume
- **Context Retrieval** — Retrieves relevant code patterns per reviewed file and injects them into the LLM prompt

### CLI
- `gito review` — Standard code review (current branch vs main)
- `gito review --rag` — RAG-enhanced review with indexed context
- `gito review --rag --rag-index-only` — Index repository without reviewing
- `gito review --all` — Review entire codebase (not just diff)
- `gito review --url <repo-url>` — Review a remote repository directly
- `gito answer <question>` — Ask questions about code changes

### Integrations
- **GitHub Actions** — Automated PR reviews with comment posting
- **GitLab CI** — Beta support
- **Jira / Linear** — Issue tracker integration for associating reviews with tickets

---

## Supported Platforms & Providers

### Git Platforms

| Platform    | Status               |
|-------------|----------------------|
| GitHub      | Supported            |
| GitLab      | Supported (Beta)     |
| Bitbucket   | Planned              |
| Local / CLI | Supported            |

### LLM Providers

CodeRubric uses [ai-microcore](https://github.com/Nayjest/ai-microcore) for vendor-agnostic LLM access. Switch providers by changing 3 environment variables — no code changes needed.

| Provider | `LLM_API_TYPE` | Example `MODEL` |
|----------|-----------------|------------------|
| Google Gemini | `google` | `gemini-2.0-flash` |
| OpenAI | `openai` | `gpt-4o-mini`, `gpt-4o` |
| Anthropic | `anthropic` | `claude-sonnet-4-20250514` |
| Ashna AI | `openai` + `LLM_API_BASE=https://api.ashna.ai/v1/api` | (Ashna model name) |
| OpenRouter / Mistral | `openai` | `mistralai/mistral-7b-instruct` |
| Azure OpenAI | `azure` | (your deployment name) |
| Local (Ollama, vLLM) | `openai` | (local model name) |
| Embedded Inference (PyTorch / Transformers) | — | (local model) |

RAG embeddings use a **local** `sentence-transformers` model (`all-MiniLM-L6-v2` by default) — no external API key required.

### Issue Trackers

| Tool   | Status    | Documentation |
|--------|-----------|---------------|
| Jira   | Supported | [Jira Integration](documentation/jira_integration.md) |
| Linear | Supported | [Linear Integration](documentation/linear_integration.md) |

---

## Security & Privacy

CodeRubric keeps your source code private by design — it is a **stateless, client-side tool** with a strict zero-retention policy.

- **No middleman:** Source code is transmitted directly from your environment (CI/CD runner, local machine, or Docker container) to your explicitly configured LLM provider. If you use a local model, your code never leaves your network.
- **No data collection:** Your code isn't stored, logged, or retained by CodeRubric.
- **Fully auditable:** 100% open source. Verify every line yourself.

---

## Quickstart (Docker — Web Dashboard)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An LLM API key (Google Gemini, OpenAI, or Anthropic)

### 1. Clone and configure

```bash
git clone https://github.com/i-am-sushant/CodeRubric.git
cd CodeRubric
cp .env.example .env
```

Edit `.env` with your LLM provider credentials:

```bash
# Google Gemini (free tier available)
LLM_API_KEY=your-gemini-api-key
LLM_API_TYPE=google
MODEL=gemini-2.0-flash

# — OR — OpenAI
# LLM_API_KEY=sk-your-openai-key
# LLM_API_TYPE=openai
# MODEL=gpt-4o-mini

# — OR — Ashna AI (OpenAI-compatible)
# LLM_API_KEY=your-ashna-api-key
# LLM_API_TYPE=openai
# LLM_API_BASE=https://api.ashna.ai/v1/api
# MODEL=your-ashna-model

# — OR — Anthropic
# LLM_API_KEY=sk-ant-your-key
# LLM_API_TYPE=anthropic
# MODEL=claude-sonnet-4-20250514
```

### 2. Build and start

```bash
docker compose up --build -d
```

This starts 5 services: PostgreSQL, Redis, ChromaDB, Backend (FastAPI), Frontend (React + Nginx).

### 3. Open the dashboard

Navigate to **http://localhost:3000** in your browser.

### 4. First review

1. Go to **Repositories** → Add a GitHub repo URL and branch
2. Go to **New Review** → Select the repo, configure branches, toggle RAG
3. Click **Start Review** — results appear in real-time

Or use **Quick Review** to paste a GitHub URL and review in one step.

---

## Web Dashboard Guide

### Pages

| Page | Path | Description |
|------|------|-------------|
| **Dashboard** | `/` | Overview stats, quick action links |
| **Repositories** | `/repos` | Add, list, delete repositories; trigger indexing |
| **New Review** | `/new-review` | Configure and start a code review |
| **Reviews** | `/reviews` | List all past reviews with status |
| **Review Detail** | `/reviews/:id` | Full issue list with severity, code, proposals |
| **Quick Review** | `/quick-review` | Paste URL → clone → review in one step |
| **Ask** | `/ask` | Ask natural-language questions about code changes |
| **Settings** | `/settings` | View/update LLM provider, API key, model at runtime |

### Review Modes

| Mode | RAG Toggle | Requirements | Best For |
|------|------------|--------------|----------|
| **Standard** | OFF | Repo cloned | Fast reviews, small diffs |
| **RAG-Enhanced** | ON | Repo cloned + indexed | Deep reviews with codebase context |

### Settings Page

The Settings page reads the live LLM configuration from the backend and allows runtime updates:
- **Provider** — Google Gemini, OpenAI, Anthropic
- **API Key** — Enter your own key (never displayed, only shows "Set" / "Missing")
- **Model** — Free-text input with per-provider quick-pick buttons
- **RAG Info** — Shows embedding model (local, no key needed) and vector store status

Changes apply immediately — no container restart required.

---

## Gito CLI Tool

CodeRubric includes the **Gito** CLI — a standalone command-line AI code reviewer that can be used independently of the web dashboard. It supports reviewing local repositories, remote URLs, and GitHub pull requests.

### GitHub Actions (PR Reviews)

Create `.github/workflows/gito-code-review.yml`:

```yaml
name: "CodeRubric: AI Code Review"
on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:
    inputs:
      pr_number:
        description: "Pull Request number"
        required: true
jobs:
  review:
    runs-on: ubuntu-latest
    permissions: { contents: read, pull-requests: write }
    steps:
    - uses: actions/checkout@v6
      with: { fetch-depth: 0 }
    - name: Set up Python
      uses: actions/setup-python@v6
      with: { python-version: "3.13" }
    - name: Install AI Code Review tool
      run: pip install gito.bot~=4.0
    - name: Run AI code analysis
      env:
        LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
        LLM_API_TYPE: openai
        MODEL: "gpt-4o-mini"
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        PR_NUMBER_FROM_WORKFLOW_DISPATCH: ${{ github.event.inputs.pr_number }}
      run: |
        gito --verbose review
        gito github-comment --token ${{ secrets.GITHUB_TOKEN }}
    - uses: actions/upload-artifact@v6
      with:
        name: ai-code-review-results
        path: |
          code-review-report.md
          code-review-report.json
```

> Make sure to add `LLM_API_KEY` to your repository's GitHub secrets.

PRs will now receive AI code reviews automatically. See the [GitHub Setup Guide](documentation/github_setup.md) for more details.

### Local Installation

**Prerequisites:** [Python](https://www.python.org/downloads/) 3.11 / 3.12 / 3.13, [Git](https://git-scm.com)

#### Option A: Install via pip (recommended)

```bash
pip install gito.bot
```

To install from repository source / specific branch:
```bash
pip install git+https://github.com/i-am-sushant/CodeRubric.git@<branch-or-tag>
```

#### Option B: Windows Standalone Installer

Download the latest Windows installer from [Releases](https://github.com/i-am-sushant/CodeRubric/releases).
Includes: standalone executable (no Python required), automatic PATH configuration, Start Menu shortcuts.

#### Initial Setup

Run the interactive setup wizard to configure your LLM provider:

```bash
gito setup
```

Configuration is saved to `~/.gito/.env`.

> **Tip:** On some systems, `gito` may not be available immediately after installation. Restart your terminal or run `python -m gito` instead.

### CLI Commands

#### Code Review

```bash
# Review current branch against main (default)
gito review

# RAG-enhanced review (uses indexed codebase context)
gito review --rag

# Index repository for RAG without reviewing
gito review --rag --rag-index-only

# Review entire codebase (not just diff)
gito review --all

# Review a remote repository by URL
gito review --url https://github.com/owner/repo.git

# Filter to specific files
gito review --filters "*.py"

# Verbose output
gito --verbose review
```

#### Remote Repository Review

```bash
gito remote git@github.com:owner/repo.git <FEATURE_BRANCH>..<MAIN_BRANCH>
gito remote --help  # Interactive help
```

#### Ask Questions About Code

```bash
gito answer "What does this refactoring change?"
```

#### GitHub PR Comments

```bash
# Post review results as a PR comment
gito github-comment --token $GITHUB_TOKEN
```

See `gito --help` and the [Command Line Reference](documentation/command_line_reference.md) for all options.

### CLI Configuration

Gito uses a two-layer configuration model:

| Scope | Location | Purpose |
|-------|----------|----------|
| **Environment** | `~/.gito/.env` or OS environment variables | LLM provider, model, API keys, concurrency |
| **Project** | `<repo>/.gito/config.toml` | Review behavior, prompts, templates, integrations |

> Environment configuration is machine-specific and never committed to version control. Project configuration defines review behavior and can be shared across your team.

#### Environment Configuration

Gito uses [ai-microcore](https://github.com/Nayjest/ai-microcore) for LLM access. Settings are configured via environment variables or `.env` files.

**Default location:** `~/.gito/.env` (created via `gito setup`)

```bash
# ~/.gito/.env
LLM_API_TYPE=google
LLM_API_KEY=your-api-key
MODEL=gemini-2.0-flash
MAX_CONCURRENT_TASKS=20
```

For all supported options, see the [ai-microcore configuration guide](https://github.com/Nayjest/ai-microcore?tab=readme-ov-file#%EF%B8%8F-configuring).

In CI/CD workflows, configure LLM settings via workflow environment variables and use your platform's secrets management for API keys.

#### Project Configuration

Place a `.gito/config.toml` at the repository root. Settings follow a layered override model:

**Bundled Defaults** ([config.toml](gito/config.toml)) → **Project Config** (`<your-repo>/.gito/config.toml`)

You only need to specify settings you want to change — everything else falls back to sensible defaults.

```toml
# .gito/config.toml
mention_triggers = ["gito", "/check"]
collapse_previous_code_review_comments = true

aux_files = [
    'documentation/command_line_reference.md'
]

exclude_files = [
    'poetry.lock',
]

[prompt_vars]
awards = ""  # Disable awards
requirements = """
- All public functions must have docstrings.
"""
```

Common customizations: review prompts, output templates, post-processing, bot behavior, pipeline integrations (Jira, Linear).

For detailed guidance, see the [Configuration Cookbook](documentation/config_cookbook.md).

---

## API Reference

All endpoints are prefixed with `/api/`. Interactive docs available at `http://localhost:8000/docs`.

### Repositories

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/repos/` | List all repositories |
| `POST` | `/api/repos/` | Add and clone a repository |
| `GET` | `/api/repos/{id}` | Get repository details |
| `GET` | `/api/repos/{id}/status` | Get indexing status |
| `POST` | `/api/repos/{id}/reindex` | Re-index for RAG |
| `DELETE` | `/api/repos/{id}` | Delete repository |

### Reviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reviews/` | List all reviews |
| `POST` | `/api/reviews/` | Create a new review |
| `GET` | `/api/reviews/{id}` | Get review details |
| `GET` | `/api/reviews/{id}/issues` | Get issues for a review |
| `GET` | `/api/reviews/{id}/report` | Get full JSON report |
| `POST` | `/api/reviews/{id}/rerun` | Re-run a review |
| `DELETE` | `/api/reviews/{id}` | Delete a review |
| `POST` | `/api/reviews/quick-review` | Clone + review in one call |

### Ask

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ask/` | Ask a question about code changes |

**Request body:**
```json
{
  "repo_id": "uuid",
  "question": "What does this function do?",
  "source_branch": "HEAD",
  "target_branch": "main"
}
```

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/settings/` | Get current LLM configuration |
| `PUT` | `/api/settings/` | Update LLM key/type/model at runtime |
| `GET` | `/api/settings/providers` | List supported providers |

### Other

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health/` | Health check |
| `GET` | `/api/stats/` | Review statistics |
| `WS` | `/ws/review/{id}` | WebSocket for review progress |

---

## Configuration (Web App)

The web dashboard uses environment variables from `.env` (read at startup) and supports runtime updates via the Settings page.

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Description | Default |
|----------|-------------|----------|
| `LLM_API_KEY` | API key for your LLM provider | (required) |
| `LLM_API_TYPE` | Provider type: `google`, `openai`, `anthropic` | `openai` |
| `LLM_API_BASE` | Optional OpenAI-compatible base URL, such as Ashna AI | provider default |
| `MODEL` | Model name (e.g. `gemini-2.0-flash`, `gpt-4o-mini`) | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Sentence-transformers model for RAG | `all-MiniLM-L6-v2` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/coderubric` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `VECTOR_STORE_PATH` | ChromaDB storage path | `/app/chroma_db` |
| `REPO_CLONE_PATH` | Where cloned repos are stored | `/app/data/repos` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `SECRET_KEY` | App secret key | `dev-secret-change-in-production` |

LLM settings can also be changed at runtime from the **Settings** page — no restart needed.

---

## Project Structure

```
CodeRubric/
├── backend/                    # FastAPI backend
│   ├── api/
│   │   ├── main.py            # App entry, lifespan, microcore init
│   │   ├── routes/
│   │   │   ├── repos.py       # Repository CRUD + indexing
│   │   │   ├── reviews.py     # Review CRUD + quick-review
│   │   │   ├── ask.py         # Ask questions about code
│   │   │   ├── settings.py    # Runtime LLM config
│   │   │   ├── stats.py       # Statistics
│   │   │   └── health.py      # Health check
│   │   └── ws.py              # WebSocket helpers
│   ├── services/
│   │   ├── review_service.py  # Review orchestration
│   │   └── repo_service.py    # Clone + index logic
│   ├── database.py            # SQLAlchemy models
│   ├── schemas.py             # Pydantic request/response models
│   ├── config.py              # Settings from env vars
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── dashboard.tsx
│   │   │   ├── repositories.tsx
│   │   │   ├── new-review.tsx
│   │   │   ├── reviews.tsx
│   │   │   ├── review-detail.tsx
│   │   │   ├── quick-review.tsx
│   │   │   ├── ask.tsx
│   │   │   └── settings.tsx
│   │   ├── components/layout.tsx
│   │   ├── api/client.ts
│   │   └── App.tsx
│   ├── nginx.conf              # Reverse proxy config
│   └── Dockerfile
│
├── coderubric/                 # RAG engine module
│   ├── rag/
│   │   ├── chunker.py         # Code chunking
│   │   ├── embedder.py        # Sentence-transformers embeddings
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   └── retriever.py       # Context retrieval
│   └── core/
│       ├── rag_review.py      # RAG-enhanced reviewer
│       └── standard_reviewer.py # Standard reviewer
│
├── gito/                       # Gito core engine
│   ├── core.py                # Diff, review, answer logic
│   ├── config.toml            # Default review prompts & config
│   ├── cli.py                 # CLI commands
│   └── tpl/                   # Jinja2 prompt templates
│
├── docker-compose.yml          # 5-service orchestration
├── pyproject.toml              # Python dependencies (Poetry)
├── .env.example                # Environment template
└── tests/                      # Test suite
```

---

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### Backend (local)

```bash
# Install Python dependencies
poetry install

# Set environment variables
cp .env.example .env
# Edit .env with your API key

# Start PostgreSQL + Redis + ChromaDB via Docker
docker compose up -d db redis chroma

# Run backend
uvicorn backend.api.main:app --reload --port 8000
```

### Frontend (local)

```bash
cd frontend
npm install
npm run dev    # Starts on http://localhost:5173
```

> When running the frontend locally, API requests are proxied to `http://localhost:8000` via the Vite dev server config.

### Code Style

```bash
make black     # Auto-format
make cs        # Lint check (flake8 + pylint)
```

### Tests

```bash
pytest
```

---

## Guides & Reference

- [Command Line Reference](documentation/command_line_reference.md)
- [Configuration Cookbook](documentation/config_cookbook.md)
- [GitHub Setup Guide](documentation/github_setup.md)
- Integrations
  - [Linear Integration](documentation/linear_integration.md)
  - [Atlassian Jira Integration](documentation/jira_integration.md)
- [Documentation Generation with CodeRubric](documentation/documentation_generation.md)
- [Troubleshooting](documentation/troubleshooting.md)

Browse all documentation in the [`/documentation`](documentation/) directory.

---

## Known Limitations

- CodeRubric cannot modify files inside `.github/workflows` when reacting to GitHub PR comments (e.g., "CodeRubric fix issue 2"). This is a GitHub security restriction — workflows cannot modify other workflow files using the default `GITHUB_TOKEN`. Using a PAT with the `workflow` scope would bypass this but is not recommended for security reasons.
- RAG embeddings use local sentence-transformers models. For very large repositories, initial indexing may take several minutes.
- Runtime settings changes (via the Settings page) are not persisted across container restarts. For persistence, edit `.env` and restart.

---

## Deploying on Azure (Single VM)

This guide covers deploying CodeRubric on a single Azure Virtual Machine using Docker Compose — the simplest production-ready setup.

### 1. Create the VM

```bash
# Create resource group
az group create --name coderubric-rg --location eastus

# Create VM (Ubuntu 24.04, Standard_B2s = 2 vCPU, 4 GB RAM — sufficient for small teams)
az vm create \
  --resource-group coderubric-rg \
  --name coderubric-vm \
  --image Ubuntu2404 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard

# Open ports 80 (HTTP), 443 (HTTPS), and 3000 (app)
az vm open-port --resource-group coderubric-rg --name coderubric-vm --port 80 --priority 1001
az vm open-port --resource-group coderubric-rg --name coderubric-vm --port 443 --priority 1002
az vm open-port --resource-group coderubric-rg --name coderubric-vm --port 3000 --priority 1003
```

Note the public IP from the output. You can also retrieve it:
```bash
az vm show -d --resource-group coderubric-rg --name coderubric-vm --query publicIps -o tsv
```

### 2. SSH into the VM and install Docker

```bash
ssh azureuser@<VM_PUBLIC_IP>

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt-get install -y docker-compose-plugin

# Log out and back in for group changes
exit
ssh azureuser@<VM_PUBLIC_IP>

# Verify
docker --version
docker compose version
```

### 3. Clone and configure

```bash
git clone https://github.com/i-am-sushant/CodeRubric.git
cd CodeRubric
cp .env.example .env
```

Edit `.env` with production values:
```bash
nano .env
```

```bash
# LLM Configuration
LLM_API_KEY=your-actual-api-key
LLM_API_TYPE=google
MODEL=gemini-2.0-flash

# Security — CHANGE THIS in production!
SECRET_KEY=$(openssl rand -hex 32)

# Database (uses the Docker PostgreSQL container)
DATABASE_URL=postgresql://postgres:postgres@db:5432/coderubric

# Leave the rest as defaults
```

### 4. Build and start

```bash
docker compose up --build -d
```

Wait for all services to start (~1-2 minutes for first build):
```bash
docker compose logs -f backend  # Watch for "[CodeRubric] LLM framework initialized"
```

### 5. Access the application

Open in your browser: `http://<VM_PUBLIC_IP>:3000`

### 6. (Optional) Set up a domain with SSL

If you have a domain name, set up Nginx as a reverse proxy with Let's Encrypt:

```bash
# Install Nginx and Certbot
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx config
sudo tee /etc/nginx/sites-available/coderubric << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/coderubric /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 7. (Optional) Auto-start on reboot

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Create a systemd service for CodeRubric
sudo tee /etc/systemd/system/coderubric.service << EOF
[Unit]
Description=CodeRubric
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/azureuser/CodeRubric
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=azureuser

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable coderubric
```

### Updating

```bash
cd ~/CodeRubric
git pull
docker compose up --build -d
```

### Resource Recommendations

| Team Size | VM Size | vCPU | RAM | Monthly Cost (approx) |
|-----------|---------|------|-----|----------------------|
| 1-3 users | Standard_B2s | 2 | 4 GB | ~$30 |
| 3-10 users | Standard_B2ms | 2 | 8 GB | ~$60 |
| 10+ users | Standard_B4ms | 4 | 16 GB | ~$120 |

---

## CI/CD — GitHub Actions for PR Reviews

The GitHub Actions workflow for automated PR reviews works **independently** of the web dashboard. It runs on GitHub's hosted runners, not on your Azure VM.

### How it works

1. A pull request is opened/updated on your repository
2. GitHub Actions spins up a runner, installs `gito.bot` via pip
3. `gito review` analyzes the diff using your configured LLM
4. `gito github-comment` posts the review as a PR comment
5. The runner is destroyed — nothing persists

### Setup

**Step 1:** Add your LLM API key to GitHub repository secrets:
- Go to your repo → Settings → Secrets and variables → Actions
- Add `LLM_API_KEY` with your API key value

**Step 2:** Create `.github/workflows/gito-code-review.yml` (see [Gito CLI Tool > GitHub Actions](#github-actions-pr-reviews) section above for the full YAML).

**Step 3:** Push. PRs will now be reviewed automatically.

### Does it work with the web dashboard?

- **They are independent.** The CI/CD runs on GitHub's infrastructure; the web dashboard runs on your VM/Docker.
- You can use **both simultaneously** — CI/CD for automated PR reviews, web dashboard for manual reviews with RAG.
- They share the same LLM API key but connect to the LLM provider separately.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `429 RESOURCE_EXHAUSTED` from Gemini | Free tier quota exhausted. Wait for reset (per-minute/daily) or enable billing. |
| Review shows "No code changes detected" | Ensure both source and target branches exist in the clone. Full history is fetched by default. |
| `LLMConfigError: API type 'google' not recognized` | This is a known microcore validation bug. The backend works around it with `VALIDATE_CONFIG=False`. |
| Frontend shows network errors | Verify backend is running (`docker compose logs backend`). Nginx proxies `/api/` to `backend:8000`. |
| RAG context not appearing in reviews | Ensure the repository is indexed (status = "completed" on the Repos page). |
| Settings changes not persisting across restarts | Runtime settings update `os.environ` in the running process. For persistence, edit `.env` and restart. |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Licensed under the [MIT License](LICENSE).

Built upon the [Gito](https://github.com/Sushant/CodeRubric) codebase by Vitalii Stepanenko and contributors.
