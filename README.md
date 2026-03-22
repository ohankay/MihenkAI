# MihenkAI - LLM Quality Evaluation Platform

MihenkAI is built for **test engineers** working on LLM-based applications. It automates quality evaluation of LLM outputs — define judge models and metric profiles, submit test prompts and responses, and receive detailed per-metric and composite scores via a web UI or REST API. Supports RAG pipeline validation, chatbot quality testing, and any LLM workflow where you need measurable output quality.

> **Target Audience:** QA teams and test engineers who need repeatable, metric-driven evaluation of LLM-based product behaviour.
>
> **Project Positioning:** MihenkAI does not claim to solve a fundamentally new problem that no existing framework or tool can address. Similar capabilities already exist in established ecosystems. The motivation here is twofold: (1) provide a practical, simpler option for closed/corporate environments with focused needs, and (2) serve as a personal learning and growth project by a test engineer operating outside a formal AI engineering role.

## Features

- **Automated LLM Evaluation**: LLM-as-Judge methodology via DeepEval — real quality scoring, not heuristics
- **Two Evaluation Types**:
  - **Single**: Evaluate standalone prompt/response/context triples (RAG, Q&A)
  - **Conversational**: Evaluate multi-turn conversation quality
- **11 Configurable Metrics**: 5 weighted single-eval metrics + 3 penalty metrics (Hallucination/Bias/Toxicity) + 3 conversational metrics — each profile configures its own weights and penalty thresholds
- **Multi-Provider Support**: OpenAI, Anthropic, Gemini, Grok, DeepSeek, vLLM — configure any as judge model
- **Evaluation Profiles**: Named, reusable metric sets with custom weights — run the same test campaign with different scoring criteria
- **Asynchronous Processing**: Evaluations run in background workers; API stays responsive
- **Container-First**: Deploy with a single `docker-compose up` command
- **Web UI**: React-based interface for managing models, defining profiles, submitting evaluations, and reviewing results
- **REST API + Swagger**: Full OpenAPI documentation at `/docs` for CI/CD integration

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

3. **Customize environment (optional)**
   Edit `.env` to set fallback API keys for LLM providers:
   ```
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   DEEPEVAL_API_KEY=your_key_here
   ```
   > **Note:** These are optional fallback keys used by the evaluator.
   > System starts with a seeded default judge profile: **Grok / llama-3.1-8b-instant** (API key empty).

4. **Start the system**
   ```bash
   docker-compose up -d
   ```

   > **Default judge profile:** first setup seeds **provider=Grok**, **base_url=https://api.groq.com/openai/v1**, **model=llama-3.1-8b-instant**.
   > Add your Groq API key from the web UI before running evaluations.

5. **Access the application**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Docs (Swagger)**: http://localhost:8000/docs

6. **Define your LLM models**
   Navigate to **Models** in the web UI and add the LLM(s) you want to use as judge models for evaluation.

### Initial Setup

PostgreSQL and Redis are configured automatically via Docker environment variables — no manual setup required. The frontend connects to the backend as soon as all containers are healthy.

### Reset PostgreSQL Only

If you want a clean database, do **not** use `down -v`.

Use this flow instead:

```bash
docker compose stop db backend worker
docker volume rm mihenkai_pgdata
docker compose up -d db backend worker
```

This resets PostgreSQL only.

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
│   │   └── job_queue/         # Redis/RQ job management
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
- `GET /api/config` - Retrieve configuration status
- `GET /api/status` - Get system health status

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

All metrics are powered by **DeepEval with LLM-as-Judge** and scored 0–1 (displayed as 0–100).

### Single Evaluation — Weighted Metrics (5)

These metrics contribute to the composite score according to their configured weights. All weights in a profile must sum to 1.0.

| Metric | Description |
|---|---|
| **Faithfulness** | Does the response stay faithful to the retrieved contexts? |
| **Answer Relevancy** | Is the response relevant to the input prompt? |
| **Contextual Precision** | Are the retrieved contexts precisely relevant to the prompt? |
| **Contextual Recall** | Do the retrieved contexts cover the expected answer? |
| **Contextual Relevancy** | Are the retrieved contexts relevant to the input? |

### Single Evaluation — Penalty Metrics (3)

These metrics are evaluated against a **threshold** (0–100), not a weight. If a metric's score meets or exceeds its configured threshold the **entire composite score is zeroed**, regardless of the weighted metrics. Enable only the penalty metrics that are relevant to your test campaign.

| Metric | Description | Threshold behaviour |
|---|---|---|
| **Hallucination** | Does the response contain fabricated information not grounded in context? | Score ≥ threshold → composite = 0 |
| **Bias** | Does the response exhibit demographic or ideological bias? | Score ≥ threshold → composite = 0 |
| **Toxicity** | Does the response contain harmful or toxic content? | Score ≥ threshold → composite = 0 |

> **Required inputs for single eval:** `prompt`, `actual_response`, `expected_response`, `retrieved_contexts`

### Conversational Evaluation (3 metrics)

| Metric | Description | Optional inputs |
|---|---|---|
| **Knowledge Retention** | Does the model retain facts from earlier turns? | — |
| **Conversation Completeness** | Does the conversation fully address the user's goals? | `scenario`, `expected_outcome` |
| **Conversation Relevancy** | Are responses relevant to the current conversational context? | `window_size` (default 3) |

> **Required inputs for conversational eval:** `chat_history`, `prompt`, `actual_response`  
> **Optional:** `scenario` and `expected_outcome` improve Conversation Completeness scoring; `retrieved_contexts` is passed through per turn if the chatbot uses RAG.

### Composite Score

Each profile defines weights for its weighted metrics and optional thresholds for its penalty metrics.

```
# Step 1 — Penalty check (runs first)
If any penalty metric's score >= its configured threshold:
    CompositeScore = 0   ← immediately zeroed, no further calculation

# Step 2 — Weighted average (only if no penalty was triggered)
CompositeScore = Σ(MetricScore × MetricWeight)   (weights sum to 1.0)
```

Only enabled weighted metrics contribute to the score — disabled metrics do not dilute the result.

## Testing

### Unit Tests

Run backend unit tests:

```bash
cd backend
pip install -r requirements.txt
pytest tests/
```

Test files:
- `tests/test_schemas.py` - Pydantic schema validation (weights, fields)
- `tests/test_evaluator.py` - Metric calculation accuracy
- `tests/test_endpoints.py` - FastAPI endpoint functionality

```bash
# Run specific test module
pytest tests/test_schemas.py -v

# Run with coverage
pytest --cov=src tests/

# Run asyncio tests only
pytest -m asyncio
```

### Integration Tests (E2E)

**Quick Test** (Services already running):

```bash
# Start services first
docker-compose up -d

# Wait 10 seconds for services to initialize
# Then run the test
python test_workflow.py
```

This tests:
1. Backend connectivity
2. Model creation
3. Evaluation profile creation
4. Single evaluation execution
5. Job polling and results retrieval
6. Composite score validation

**Full E2E Test** (Start and stop services):

```bash
python e2e_test.py
```

This also:
- Builds and starts all docker-compose services
- Waits for health checks
- Runs the complete workflow
- Automatically stops services

Add `--keep-running` flag to leave services running:

```bash
python e2e_test.py --keep-running
```

### Debugging Tests

View test execution details:

```bash
# Verbose output with print statements
pytest tests/ -v -s

# Show local variables and full tracebacks
pytest tests/ -vv --tb=long

# Stop on first failure
pytest tests/ -x

# Run only tests matching a pattern
pytest tests/ -k "test_weights"
```

## Configuration

### Environment Variables

```env
# PostgreSQL (auto-configured by Docker, do not change unless you know what you're doing)
POSTGRES_USER=mihenkai_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=mihenkai_db

# Optional fallback API keys — used when a model config has no API key stored
# Models themselves are defined through the web UI, not here
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPEVAL_API_KEY=

# Internal (set automatically by docker-compose)
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

Built for QA teams and test engineers building and validating LLM-based applications.
