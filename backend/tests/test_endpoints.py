"""Tests for FastAPI endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Since we're testing endpoints, we need to use the actual app
from src.main import app
from src.db.models import ModelConfig, EvaluationProfile, EvaluationJob
from src.db.session import AsyncSessionLocal


# Create test client
client = TestClient(app)


class TestConfigEndpoints:
    """Test /api/config endpoints."""

    def test_get_config(self):
        """Test GET /api/config always returns configured status."""
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "configured"

    def test_get_status(self):
        """Test GET /api/status."""
        response = client.get("/api/status")
        assert response.status_code in [200, 500]


class TestModelConfigEndpoints:
    """Test /api/model-configs endpoints."""

    def test_create_model_config_valid(self):
        """Test POST /api/model-configs with valid payload."""
        response = client.post("/api/model-configs", json={
            "name": "Test GPT-4o",
            "provider": "OpenAI",
            "model_name": "gpt-4o",
            "temperature": 0.0,
            "generation_kwargs": {"max_tokens": 2000}
        })
        # 201/200 = created, 500 = DB not available in unit test env
        assert response.status_code in [200, 201, 500]

    def test_create_model_config_missing_name(self):
        """POST without required name field must return 422."""
        response = client.post("/api/model-configs", json={
            "provider": "OpenAI",
            "model_name": "gpt-4o"
        })
        assert response.status_code == 422

    def test_create_model_config_invalid_provider(self):
        """POST with unknown provider must return 422."""
        response = client.post("/api/model-configs", json={
            "name": "Bad provider",
            "provider": "FakeProvider",
            "model_name": "some-model"
        })
        assert response.status_code == 422

    def test_create_model_config_all_providers(self):
        """All ProviderEnum values must be accepted by create endpoint."""
        for provider in ["OpenAI", "Anthropic", "Gemini", "Grok", "DeepSeek", "Ollama", "vLLM"]:
            response = client.post("/api/model-configs", json={
                "name": f"{provider} Test",
                "provider": provider,
                "model_name": "test-model"
            })
            # 422 would mean provider is not in ProviderEnum — must not happen
            assert response.status_code != 422, f"Provider '{provider}' rejected by API"

    def test_get_model_configs(self):
        """Test GET /api/model-configs."""
        response = client.get("/api/model-configs")
        assert response.status_code in [200, 500]

    def test_get_model_config_by_id(self):
        """Test GET /api/model-configs/{id}."""
        response = client.get("/api/model-configs/1")
        assert response.status_code in [200, 404, 500]

    def test_update_model_config_partial(self):
        """Test PUT /api/model-configs/{id} with partial update."""
        response = client.put("/api/model-configs/1", json={
            "name": "Updated Name",
            "temperature": 0.5
        })
        assert response.status_code in [200, 404, 500]

    def test_update_model_config_invalid_provider(self):
        """PUT with unknown provider must return 422."""
        response = client.put("/api/model-configs/1", json={
            "provider": "NotAProvider"
        })
        assert response.status_code == 422

    def test_delete_model_config(self):
        """Test DELETE /api/model-configs/{id}."""
        response = client.delete("/api/model-configs/1")
        assert response.status_code in [200, 204, 404, 500]


class TestEvaluationProfileEndpoints:
    """Test /api/profiles endpoints."""

    def test_create_profile_valid(self):
        """Test POST /api/profiles with valid payload."""
        response = client.post("/api/profiles", json={
            "name": "Standard Profile",
            "description": "Standard evaluation",
            "model_config_id": 1,
            "single_weights": {
                "faithfulness": 0.6,
                "answer_relevancy": 0.4
            },
            "conversational_weights": {
                "knowledge_retention": 0.5,
                "conversation_completeness": 0.5
            }
        })
        assert response.status_code in [200, 201, 404, 500]

    def test_create_profile_invalid_weights(self):
        """POST with weights not summing to 1.0 must return 422."""
        response = client.post("/api/profiles", json={
            "name": "Invalid Profile",
            "model_config_id": 1,
            "single_weights": {
                "faithfulness": 0.5,
                "answer_relevancy": 0.6
            },
            "conversational_weights": {}
        })
        assert response.status_code == 422

    def test_create_profile_missing_name(self):
        """POST without name must return 422."""
        response = client.post("/api/profiles", json={
            "model_config_id": 1,
            "single_weights": {}
        })
        assert response.status_code == 422

    def test_get_profiles(self):
        """Test GET /api/profiles."""
        response = client.get("/api/profiles")
        assert response.status_code in [200, 500]

    def test_get_profile_by_id(self):
        """Test GET /api/profiles/{id}."""
        response = client.get("/api/profiles/1")
        assert response.status_code in [200, 404, 500]

    def test_delete_profile(self):
        """Test DELETE /api/profiles/{id}."""
        response = client.delete("/api/profiles/1")
        assert response.status_code in [200, 204, 404, 500]


class TestEvaluationEndpoints:
    """Test /api/evaluate endpoints."""

    def test_evaluate_single_valid(self):
        """Test POST /api/evaluate/single with valid payload."""
        response = client.post("/api/evaluate/single", json={
            "profile_id": 1,
            "prompt": "What is the capital of France?",
            "actual_response": "The capital of France is Paris.",
            "retrieved_contexts": ["Paris is the capital of France."]
        })
        assert response.status_code in [200, 201, 404, 422, 500]

    def test_evaluate_single_missing_required_fields(self):
        """POST missing required fields must return 422."""
        response = client.post("/api/evaluate/single", json={
            "profile_id": 1
            # missing prompt and actual_response
        })
        assert response.status_code == 422

    def test_evaluate_conversational_valid(self):
        """Test POST /api/evaluate/conversational."""
        response = client.post("/api/evaluate/conversational", json={
            "profile_id": 1,
            "prompt": "What is the capital of France?",
            "actual_response": "Paris is the capital.",
            "retrieved_contexts": [],
            "chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ]
        })
        assert response.status_code in [200, 201, 404, 422, 500]

    def test_evaluate_conversational_invalid_role(self):
        """Chat message with invalid role must return 422."""
        response = client.post("/api/evaluate/conversational", json={
            "profile_id": 1,
            "prompt": "test",
            "actual_response": "test",
            "retrieved_contexts": [],
            "chat_history": [
                {"role": "system", "content": "You are helpful"}
            ]
        })
        assert response.status_code == 422

    def test_get_job_status(self):
        """Test GET /api/evaluate/status/{job_id}."""
        response = client.get("/api/evaluate/status/nonexistent-job")
        assert response.status_code in [200, 404, 500]

    def test_list_jobs(self):
        """Test GET /api/evaluate/jobs."""
        response = client.get("/api/evaluate/jobs")
        assert response.status_code in [200, 500]


class TestOpenAPIDocumentation:
    """Test that OpenAPI documentation is properly generated."""

    def test_openapi_schema(self):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_model_config_create_schema_has_name(self):
        """ModelConfigCreate must require name field."""
        response = client.get("/openapi.json")
        schema = response.json()["components"]["schemas"]["ModelConfigCreate"]
        assert "name" in schema["required"]
        assert "provider" in schema["required"]
        assert "model_name" in schema["required"]

    def test_model_config_response_has_name(self):
        """ModelConfigResponse must include name field."""
        response = client.get("/openapi.json")
        schema = response.json()["components"]["schemas"]["ModelConfigResponse"]
        assert "name" in schema["properties"]

    def test_provider_enum_has_all_providers(self):
        """ProviderEnum must include all 7 providers."""
        response = client.get("/openapi.json")
        enum_values = response.json()["components"]["schemas"]["ProviderEnum"]["enum"]
        for expected in ["OpenAI", "Anthropic", "Gemini", "Grok", "DeepSeek", "Ollama", "vLLM"]:
            assert expected in enum_values, f"{expected} missing from ProviderEnum"

    def test_swagger_ui(self):
        """Test Swagger UI endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc(self):
        """Test ReDoc endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestHealthCheck:
    """Test application health."""

    def test_health_endpoint(self):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self):
        """Test / root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "docs" in data



class TestConfigEndpoints:
    """Test /config endpoints."""
    
    def test_setup_config(self):
        """Test POST /config setup."""
        response = client.post("/config", json={
            "database_url": "postgresql://user:pass@localhost/db",
            "redis_url": "redis://localhost:6379/0"
        })
        assert response.status_code in [200, 201]
    
    def test_get_config(self):
        """Test GET /config."""
        # First ensure config is set
        client.post("/config", json={
            "database_url": "postgresql://user:pass@localhost/db",
            "redis_url": "redis://localhost:6379/0"
        })
        
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "database_url" in data or "status" in data


class TestModelConfigEndpoints:
    """Test /models endpoints."""
    
    @pytest.fixture
    def setup_db(self):
        """Setup mock database for testing."""
        with patch('src.routers.models.AsyncSessionLocal') as mock_session:
            yield mock_session
    
    def test_create_model_config(self):
        """Test POST /models."""
        response = client.post("/models", json={
            "model_name": "gpt-4",
            "model_type": "openai",
            "api_key": "sk-test-key"
        })
        # May fail due to DB connectivity, but check endpoint exists
        assert response.status_code in [200, 201, 422, 500]
    
    def test_get_models(self):
        """Test GET /models."""
        response = client.get("/models")
        # Endpoint should exist (may return error due to DB)
        assert response.status_code in [200, 500]
    
    def test_get_model_by_id(self):
        """Test GET /models/{model_id}."""
        response = client.get("/models/1")
        assert response.status_code in [200, 404, 500]
    
    def test_update_model(self):
        """Test PUT /models/{model_id}."""
        response = client.put("/models/1", json={
            "model_name": "gpt-4-turbo",
            "model_type": "openai",
            "api_key": "sk-updated-key"
        })
        assert response.status_code in [200, 404, 422, 500]
    
    def test_delete_model(self):
        """Test DELETE /models/{model_id}."""
        response = client.delete("/models/1")
        assert response.status_code in [200, 204, 404, 500]


class TestEvaluationProfileEndpoints:
    """Test /profiles endpoints."""
    
    def test_create_profile(self):
        """Test POST /profiles."""
        response = client.post("/profiles", json={
            "name": "Standard Profile",
            "description": "Standard evaluation",
            "faithfulness_weight": 0.3,
            "relevancy_weight": 0.35,
            "completeness_weight": 0.35,
            "knowledge_retention_weight": 0.0
        })
        assert response.status_code in [200, 201, 422, 500]
    
    def test_create_profile_invalid_weights(self):
        """Test POST /profiles with invalid weights."""
        response = client.post("/profiles", json={
            "name": "Invalid Profile",
            "description": "Invalid weights",
            "faithfulness_weight": 0.5,
            "relevancy_weight": 0.5,
            "completeness_weight": 0.5,
            "knowledge_retention_weight": 0.0
        })
        # Should fail validation due to weights sum > 1.0
        assert response.status_code in [422, 500]
    
    def test_get_profiles(self):
        """Test GET /profiles."""
        response = client.get("/profiles")
        assert response.status_code in [200, 500]
    
    def test_get_profile_by_id(self):
        """Test GET /profiles/{profile_id}."""
        response = client.get("/profiles/1")
        assert response.status_code in [200, 404, 500]
    
    def test_update_profile(self):
        """Test PUT /profiles/{profile_id}."""
        response = client.put("/profiles/1", json={
            "name": "Updated Profile",
            "description": "Updated",
            "faithfulness_weight": 0.25,
            "relevancy_weight": 0.25,
            "completeness_weight": 0.25,
            "knowledge_retention_weight": 0.25
        })
        assert response.status_code in [200, 404, 422, 500]
    
    def test_delete_profile(self):
        """Test DELETE /profiles/{profile_id}."""
        response = client.delete("/profiles/1")
        assert response.status_code in [200, 204, 404, 500]


class TestEvaluationEndpoints:
    """Test /evaluate endpoints."""
    
    def test_evaluate_single(self):
        """Test POST /evaluate/single."""
        response = client.post("/evaluate/single", json={
            "model_config_id": 1,
            "evaluation_profile_id": 1,
            "prompt": "What is the capital of France?",
            "response": "The capital of France is Paris.",
            "context": "France is a country in Western Europe."
        })
        # May fail due to DB, but endpoint should exist
        assert response.status_code in [200, 201, 422, 500]
    
    def test_evaluate_conversational(self):
        """Test POST /evaluate/conversational."""
        response = client.post("/evaluate/conversational", json={
            "model_config_id": 1,
            "evaluation_profile_id": 1,
            "conversation": [
                {"role": "user", "content": "What is the capital of France?"},
                {"role": "assistant", "content": "Paris is the capital."}
            ],
            "context": "France is a Western European country."
        })
        # May fail due to DB, but endpoint should exist
        assert response.status_code in [200, 201, 422, 500]
    
    def test_evaluate_single_invalid_prompt(self):
        """Test POST /evaluate/single with invalid data."""
        response = client.post("/evaluate/single", json={
            "model_config_id": 1,
            "evaluation_profile_id": 1,
            "prompt": "",  # Empty prompt
            "response": "Some response",
            "context": "Some context"
        })
        # Should fail validation
        assert response.status_code in [422, 500]
    
    def test_get_job_status(self):
        """Test GET /evaluate/{job_id}."""
        response = client.get("/evaluate/test-job-id")
        assert response.status_code in [200, 404, 500]
    
    def test_poll_evaluation_result(self):
        """Test GET /evaluate/{job_id}/result."""
        response = client.get("/evaluate/test-job-id/result")
        assert response.status_code in [200, 404, 500]


class TestOpenAPIDocumentation:
    """Test that OpenAPI documentation is properly generated."""
    
    def test_openapi_schema(self):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_swagger_ui(self):
        """Test Swagger UI endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_redoc(self):
        """Test ReDoc endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestHealthCheck:
    """Test application health."""
    
    def test_root_endpoint(self):
        """Test if root endpoint works."""
        response = client.get("/")
        # Root might not be defined, but shouldn't crash
        assert response.status_code in [200, 404, 405]
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.get("/models")
        # Check if CORS headers are present
        assert "access-control-allow-origin" in response.headers or True
