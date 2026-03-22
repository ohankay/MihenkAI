"""Tests for FastAPI endpoints."""
from fastapi.testclient import TestClient

from src.main import app
from tests.conftest import TEST_ENTITY_PREFIX


client = TestClient(app)


class TestConfigEndpoints:
    """Test /api/config endpoints."""

    def test_get_config(self):
        response = client.get('/api/config')
        assert response.status_code == 200
        assert response.json().get('status') == 'configured'

    def test_get_status(self):
        response = client.get('/api/status')
        assert response.status_code in [200, 500]


class TestModelConfigEndpoints:
    """Test /api/model-configs endpoints."""

    def test_create_model_config_missing_name(self):
        response = client.post('/api/model-configs', json={
            'provider': 'OpenAI',
            'model_name': 'gpt-4o',
        })
        assert response.status_code == 422

    def test_create_model_config_invalid_provider(self):
        response = client.post('/api/model-configs', json={
            'name': 'Bad provider',
            'provider': 'FakeProvider',
            'model_name': 'x',
        })
        assert response.status_code == 422

    def test_create_model_config_all_providers(self):
        for provider in ['OpenAI', 'Anthropic', 'Gemini', 'Grok', 'DeepSeek', 'vLLM']:
            response = client.post('/api/model-configs', json={
                'name': f'{TEST_ENTITY_PREFIX}{provider} Test',
                'provider': provider,
                'model_name': 'test-model',
            })
            assert response.status_code != 422

    def test_model_config_crud_endpoints_exist(self):
        assert client.get('/api/model-configs').status_code in [200, 500]
        assert client.get('/api/model-configs/1').status_code in [200, 404, 500]
        assert client.put('/api/model-configs/1', json={'name': 'Updated'}).status_code in [200, 404, 422, 500]
        assert client.delete('/api/model-configs/1').status_code in [200, 204, 404, 500]


class TestProfileEndpoints:
    """Test /api/profiles endpoints."""

    def test_profile_endpoints_exist(self):
        assert client.get('/api/profiles').status_code in [200, 500]
        assert client.get('/api/profiles/1').status_code in [200, 404, 500]
        assert client.delete('/api/profiles/1').status_code in [200, 204, 400, 404, 500]


class TestEvaluationEndpoints:
    """Test /api/evaluate endpoints."""

    def test_evaluate_single_validation(self):
        response = client.post('/api/evaluate/single', json={
            'evaluation_profile_id': 1,
            'judge_llm_profile_id': 1,
        })
        assert response.status_code == 422

    def test_evaluate_conversational_validation(self):
        response = client.post('/api/evaluate/conversational', json={
            'evaluation_profile_id': 1,
            'judge_llm_profile_id': 1,
            'chat_history': [{'role': 'system', 'content': 'bad role'}],
            'prompt': 'x',
            'actual_response': 'y',
            'retrieved_contexts': [],
        })
        assert response.status_code == 422

    def test_get_job_status(self):
        response = client.get('/api/evaluate/status/nonexistent-job')
        assert response.status_code in [200, 404, 500]

    def test_list_jobs_with_filters(self):
        response = client.get('/api/evaluate/jobs', params={
            'limit': 20,
            'offset': 0,
            'profile_id': 1,
            'status': 'COMPLETED',
            'start_time': '2026-03-21T00:00:00Z',
            'end_time': '2026-03-22T23:59:59Z',
        })
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            body = response.json()
            assert 'items' in body
            assert 'total' in body
            assert 'has_next' in body


class TestOpenAPIDocumentation:
    """Test OpenAPI + schema contracts."""

    def test_openapi_schema(self):
        response = client.get('/openapi.json')
        assert response.status_code == 200
        data = response.json()
        assert 'openapi' in data
        assert 'paths' in data

    def test_provider_enum_contract(self):
        response = client.get('/openapi.json')
        enum_values = response.json()['components']['schemas']['ProviderEnum']['enum']
        for expected in ['OpenAI', 'Anthropic', 'Gemini', 'Grok', 'DeepSeek', 'vLLM']:
            assert expected in enum_values

    def test_evaluation_list_contract(self):
        response = client.get('/openapi.json')
        schema = response.json()['components']['schemas']['EvaluationJobListResponse']['properties']
        for key in ['items', 'limit', 'offset', 'count', 'total', 'has_next']:
            assert key in schema

    def test_docs_endpoints(self):
        assert client.get('/docs').status_code == 200
        assert client.get('/redoc').status_code == 200


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_health_endpoint(self):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'

    def test_root_endpoint(self):
        response = client.get('/')
        assert response.status_code == 200
        data = response.json()
        assert 'docs' in data
