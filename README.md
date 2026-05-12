# ModAI - Smart Sales Chatbot

ModAI is a SaaS platform designed to automate sales through a chatbot, initially focused on clothing stores. The system acts as a human-like virtual salesperson, welcoming potential customers, providing store information, sending PDF catalogs, answering questions, and helping with order assembly and checkout.

The system features intelligent routing that dynamically switches between AI providers (like OpenAI GPT and Google Gemini) depending on the interaction's complexity.

## 🚀 Architecture & Tech Stack

The project uses a modern architecture with decoupled Frontend and Backend, orchestrated via Docker.

### Backend
- **Python 3.12+**
- **FastAPI**: High-performance asynchronous web framework.
- **SQLAlchemy (AsyncIO) + PostgreSQL**: ORM and relational database for data persistence (customers, messages, stock, etc.).
- **Redis Stack**: Cache, sessions, and rate-limiting management.
- **AI Integrations**: OpenAI (GPT-4o-mini, GPT-4o) and Google GenAI (Gemini 2.5 Flash, Gemini 1.5 Pro).
- **FPDF2**: Dynamic generation of PDF catalogs.

### Frontend
- **Next.js 14+ (App Router)**: React framework for optimized user interfaces.
- **React & Tailwind CSS**: Utility-first styled visual components.
- **Lucide React**: Interface icons.

## 🧠 AI Architecture & Optimizations

ModAI implements a sophisticated **LangGraph** pipeline with heavy emphasis on token economy and reliability:

- **Semantic Routing**: Distinguishes between simple greetings and product queries, completely bypassing database retrievals and saving hundreds of tokens on casual interactions.
- **RAG Condensation**: Vector searches (RediSearch) retrieve only the Top-3 items, and long descriptions are truncated on the fly before prompt injection.
- **Rolling Window Summarization**: Hard limits the raw conversation history (e.g., last 4 messages) to prevent exponential token growth. Older context is asynchronously compressed into tiny summaries by cheap/fast models (GPT-4o-mini/Gemini Flash) and kept in memory.
- **Dual-Provider Fallbacks**: If the primary AI provider (OpenAI) rate-limits or fails, requests transparently cascade to the secondary provider (Google Gemini).

## 📦 Prototype Features

1. **Chatbot (Customer Simulator)**
   - Web interface simulating a WhatsApp conversation flow.
   - Smart, contextual responses utilizing conversation history and real stock/product data.
   - Automatic dispatch of **PDF Catalog** links when requested by the customer.
2. **CRM and Store Management**
   - **Sales Kanban**: Customer cards are automatically moved (e.g., Greeting → Browsing → Checkout) by the AI's intelligence.
   - **Catalog & Product Management**: Allows creation of categories and uploading/replacing PDF catalogs.
   - **Stock Management**: Control of sizes, colors, and quantities (the AI notifies the customer when items are out of stock).
3. **SuperAdmin Dashboard**
   - "Tenants" (Stores) management.
   - Tracking of token usage and limits by the AI to control costs (SaaS).

## 🛠️ How to Run Locally

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your machine.
- API Keys (OpenAI and/or Google Gemini).

### 1. Configure Environment Variables

At the project root, there is a `.env.example` file. Copy it to `.env`:

```bash
cp .env.example .env
```

Open the `.env` file and fill in your API keys:
```env
OPENAI_API_KEY="sk-your-openai-key"
GOOGLE_API_KEY="AIza-your-google-key"
```

> **Note**: You do not need to change the database/redis credentials in the `.env.example` file if you are going to run everything via Docker.

### 2. Start the Containers

Run the following command at the project root to build and start all services:

```bash
docker compose up -d --build
```

Docker will start 4 containers:
- `db`: PostgreSQL Database (on local port `5433`).
- `redis`: Redis Database.
- `backend`: FastAPI API.
- `frontend`: Next.js Application.

### 3. Data Seeding (Automatic)

When running the backend for the first time, the database will automatically be created and populated with a fictional store ("Moda Estrela"), sample products, PDF catalogs, stock items, and administrative users.

### 4. Access the Platform

- **Frontend (Chat and Dashboards)**: [http://localhost:3000](http://localhost:3000)
- **Backend (API Documentation)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Access Credentials (Generated in Seed)

| Dashboard | Email | Password |
| :--- | :--- | :--- |
| **Store CRM** | `admin@modaestrela.com` | `admin123` |
| **Super Admin** | `superadmin@modai.com` | `super123` |

## 🔄 Applying Code Changes

The environment is configured for **Hot-Reloading**. This means the vast majority of changes you make to local files (both in the Next.js frontend and FastAPI backend) will be detected immediately, updating the server automatically without needing to restart the containers.

### When do I need to restart or rebuild?
You only need to rebuild the containers (`rebuild`) if you:
1. Install new dependencies (e.g., altering `package.json` in the frontend or `pyproject.toml` in the backend).
2. Change environment variables in the `.env` file or modify service ports in `docker-compose.yml`.
3. Feel that the container has "frozen" or lost volume synchronization.

### Command to update and run the latest version
If you made changes that require a rebuild (such as new libraries), run:

```bash
# Tear down current containers
docker compose down

# Rebuild images and start them in the background again
docker compose up -d --build
```

## 📁 Directory Structure

```
.
├── backend/                  # Python FastAPI API Source Code
│   ├── app/
│   │   ├── ai/               # Prompts and LLM logic
│   │   ├── api/              # HTTP Routes (Controllers)
│   │   ├── models/           # SQLAlchemy Entities
│   │   ├── services/         # Business logic and Chat Engine
│   │   ├── main.py           # FastAPI entry point
│   │   └── seed.py           # Initial database population script
│   ├── uploads/              # Locally generated files (like Catalog PDFs)
│   └── Dockerfile
├── frontend/                 # Next.js app Source Code
│   ├── src/
│   │   ├── app/              # Pages (Chat, Login, CRM, Admin)
│   │   └── lib/              # Utilities (e.g., api.ts)
│   └── Dockerfile
├── docker-compose.yml        # Local orchestrator
└── .env                      # Secret environment variables
```

## 🧹 Cleaning the Environment

If you wish to wipe the database and start from scratch:

```bash
docker compose down -v
```
*(The `-v` flag removes the persistent Postgres and Redis volumes. Upon restarting, the initial seed will run again).*
