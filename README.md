# MihenkAI - LLM Evaluation System

A comprehensive, asynchronous microservices-based platform for automated evaluation of Large Language Model (LLM) responses in RAG, Chatbot, and other AI applications.

## Features

- **Automated Evaluation**: Evaluate LLM response quality, consistency, and contextual accuracy
- **Microservices Architecture**: Isolated, scalable components (FastAPI, DeepEval, PostgreSQL, Redis, RQ)
- **Asynchronous Processing**: Long-running evaluations don't block the API
- **Container-First**: Deploy with a single `docker-compose up` command
- **Two Evaluation Types**:
  - **Single**: Evaluate standalone responses
  - **Conversational**: Evaluate responses in multi-turn conversations
- **Flexible Metrics**: Customizable metric weights for different use cases
- **Web UI**: Intuitive React-based interface for configuration and testing

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MihenkAI
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Customize configuration (optional)**
   Edit `.env` with your API keys:
   ```
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   OLLAMA_BASE_URL=http://localhost:11434  # For local models
   ```

4. **Start the system**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Docs (Swagger)**: http://localhost:8000/docs

### Initial Setup Wizard

When you first access the frontend, you'll see a setup wizard to configure:
- PostgreSQL connection
- Redis connection

Default values are pre-filled for docker-compose environment. Click "Save Configuration" to proceed.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Browser (React)                  │
│                    localhost:3000                       │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            FastAPI Backend (Async)                      │
│              localhost:8000                             │
│  ├─ Config Endpoints                                    │
│  ├─ Model Management                                    │
│  ├─ Profile Management                                  │
│  └─ Evaluation Endpoints (POST, GET)                    │
└──────────────────────┬──────────────────────────────────┘
           │           │           │
    eval_network       │           │
           │           │           │
┌──────────▼─┐  ┌──────▼─┐  ┌────▼───────┐
│ PostgreSQL │  │ Redis  │  │ RQ Worker  │
│   Port:    │  │ Port:  │  │  Process   │
│   5432     │  │ 6379   │  │  (async)   │
│(internal)  │  │(intern)│  │            │
└────────────┘  └────────┘  └────────────┘
```

## Project Structure

```
MihenkAI/
├── backend/                    # FastAPI application
│   ├── src/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── worker.py          # RQ Worker
│   │   ├── routers/           # API endpoints
│   │   ├── db/                # Database models & session
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── evaluator/         # DeepEval integration
│   │   └── queue/             # Redis/RQ job management
│   ├── alembic/               # Database migrations
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # React application
│   ├── src/
│   │   ├── pages/             # Main pages (Setup, Dashboard, etc.)
│   │   ├── components/        # Reusable components
│   │   ├── context/           # Context API state
│   │   ├── services/          # API client
│   │   ├── hooks/             # Custom hooks
│   │   └── styles/            # Tailwind CSS
│   ├── package.json           # Node dependencies
│   └── vite.config.ts         # Vite configuration
│
├── docker/                     # Docker configurations
│   ├── Dockerfile.backend     # Multi-stage Python image
│   └── Dockerfile.frontend    # Multi-stage Node image
│
├── docker-compose.yml          # Orchestration
└── .env.example               # Environment variables template
```

## API Endpoints

### Configuration
- `POST /api/config` - Save system configuration
- `GET /api/config` - Retrieve configuration

### Model Management
- `POST /api/model-configs` - Create model config
- `GET /api/model-configs` - List all models
- `GET /api/model-configs/{id}` - Get specific model
- `PUT /api/model-configs/{id}` - Update model
- `DELETE /api/model-configs/{id}` - Delete model

### Profile Management
- `POST /api/profiles` - Create evaluation profile
- `GET /api/profiles` - List all profiles
- `GET /api/profiles/{id}` - Get specific profile
- `PUT /api/profiles/{id}` - Update profile
- `DELETE /api/profiles/{id}` - Delete profile

### Evaluation
- `POST /api/evaluate/single` - Start single evaluation
- `POST /api/evaluate/conversational` - Start conversational evaluation
- `GET /api/evaluate/status/{job_id}` - Get job status & results
- `GET /api/evaluate/jobs` - List all jobs

## Evaluation Metrics

### Single Evaluation
- **Faithfulness**: How well the response adheres to retrieved contexts
- **Answer Relevancy**: How relevant the response is to the question

### Conversational Evaluation
- **Knowledge Retention**: How well the model maintains context from previous turns
- **Conversation Completeness**: Whether the response fully addresses the current prompt

## Configuration

### Environment Variables

```env
# PostgreSQL
POSTGRES_USER=mihenkai_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=mihenkai_db

# API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
DEEPEVAL_API_KEY=

# Internal (auto-generated)
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://redis:6379/0

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

## Development

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend
```

### Run Backend Tests
```bash
docker exec mihenkai_backend pytest tests/
```

### Access Database
```bash
docker exec -it mihenkai_db psql -U mihenkai_user -d mihenkai_db
```

## Deployment

For production deployment:

1. **Create production environment file**
   ```bash
   cp .env.example .env.production
   # Edit with production values
   ```

2. **Use production docker-compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Key settings for production**
   - Set secure PostgreSQL passwords
   - Configure API keys for all external services
   - Use strong session tokens
   - Enable HTTPS/SSL on frontend
   - Set up monitoring and logging

## Troubleshooting

### "Connection refused" on first run
- Wait 30 seconds for database to be ready
- Check: `docker-compose logs db`

### Setup wizard not appearing
- Clear browser cache or use incognito mode
- Check: `docker-compose logs frontend`

### Evaluations stuck in QUEUED
- Check if worker is running: `docker-compose logs worker`
- Verify Redis connection: `docker-compose logs redis`

### Database migration errors
- Check migrations: `docker exec mihenkai_backend alembic current`
- View migration history: `docker exec mihenkai_backend alembic history`

## Performance Tuning

### For High Load
- Increase worker count: Add more `worker` services in docker-compose.yml
- Tune database: Add indexes on frequently queried columns
- Redis persistence: Enable AOF for durability
- Frontend: Implement result caching with React Query

## Future Enhancements

- [ ] Real-time WebSocket updates for evaluation progress
- [ ] Batch evaluation processing
- [ ] Custom metric plugins
- [ ] Advanced analytics dashboard
- [ ] Integration with popular LLM frameworks
- [ ] Cloud deployment templates (AWS, Azure, GCP)

## License

[Your License Here]

## Support

For issues and questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs`
3. Open an issue on GitHub

## Contributors

Built with ❤️ for the AI community
