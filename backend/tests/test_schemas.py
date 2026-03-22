"""Tests for Pydantic schemas validation."""
import pytest
from pydantic import ValidationError

from src.schemas.base import (
    ModelConfigCreate,
    EvaluationProfileCreate,
    SingleEvalRequest,
    ConversationalEvalRequest,
    ProviderEnum,
    ChatMessage,
)


class TestModelConfigCreate:
    """Test ModelConfigCreate schema validation."""
    
    def test_valid_model_config(self):
        """Test creating valid model config."""
        config = ModelConfigCreate(
            name="OpenAI Default",
            provider="OpenAI",
            model_name="gpt-4",
            api_key="sk-12345",
            temperature=0.7
        )
        assert config.name == 'OpenAI Default'
        assert config.model_name == 'gpt-4'
        assert config.provider == ProviderEnum.OPENAI
        assert config.api_key == 'sk-12345'
    
    def test_model_name_required(self):
        """Test validation fails with missing model_name."""
        with pytest.raises(ValidationError):
            ModelConfigCreate(
                name="OpenAI Default",
                provider="OpenAI",
                api_key="sk-12345"
            )

    def test_name_required(self):
        """Test validation fails with missing name."""
        with pytest.raises(ValidationError):
            ModelConfigCreate(
                provider="OpenAI",
                model_name="gpt-4",
                api_key="sk-12345"
            )
    
    def test_provider_required(self):
        """Test validation fails with missing provider."""
        with pytest.raises(ValidationError):
            ModelConfigCreate(
                name="OpenAI Default",
                model_name="gpt-4",
                api_key="sk-12345"
            )
    
    def test_valid_providers(self):
        """Test all valid providers."""
        for provider in ["OpenAI", "Anthropic", "Gemini", "Grok", "DeepSeek", "vLLM"]:
            config = ModelConfigCreate(
                name=f"{provider} Default",
                provider=provider,
                model_name="test-model",
                api_key="test-key"
            )
            assert config.provider is not None
    
    def test_temperature_bounds(self):
        """Test temperature validation."""
        # Valid temperature
        config = ModelConfigCreate(
            name="OpenAI Default",
            provider="OpenAI",
            model_name="gpt-4",
            temperature=1.0
        )
        assert config.temperature == 1.0
        
        # Invalid temperature > 2.0
        with pytest.raises(ValidationError):
            ModelConfigCreate(
                name="OpenAI Default",
                provider="OpenAI",
                model_name="gpt-4",
                temperature=2.5
            )
        
        # Invalid temperature < 0.0
        with pytest.raises(ValidationError):
            ModelConfigCreate(
                name="OpenAI Default",
                provider="OpenAI",
                model_name="gpt-4",
                temperature=-0.5
            )


class TestEvaluationProfileCreate:
    """Test EvaluationProfileCreate schema validation."""
    
    def test_valid_profile_empty_weights(self):
        """Test creating profile with empty weights."""
        profile = EvaluationProfileCreate(
            name='Test Profile',
            single_weights={},
            conversational_weights={}
        )
        assert profile.name == 'Test Profile'
    
    def test_valid_single_weights(self):
        """Test valid single evaluation weights."""
        profile = EvaluationProfileCreate(
            name='Test Profile',
            single_weights={
                'faithfulness': 0.3,
                'relevancy': 0.4,
                'completeness': 0.3,
            }
        )
        assert sum(profile.single_weights.values()) == 1.0
    
    def test_single_weights_sum_invalid(self):
        """Test single weights validation fails when sum != 1.0."""
        with pytest.raises(ValidationError):
            EvaluationProfileCreate(
                name='Test Profile',
                single_weights={
                    'faithfulness': 0.3,
                    'relevancy': 0.4,
                    'completeness': 0.4,  # Sum = 1.1
                }
            )
    
    def test_conversational_weights_sum_valid(self):
        """Test valid conversational weights."""
        profile = EvaluationProfileCreate(
            name='Test Profile',
            conversational_weights={
                'faithfulness': 0.25,
                'relevancy': 0.25,
                'completeness': 0.25,
                'knowledge_retention': 0.25,
            }
        )
        assert sum(profile.conversational_weights.values()) == 1.0
    
    def test_conversational_weights_sum_invalid(self):
        """Test conversational weights validation fails when sum < 1.0."""
        with pytest.raises(ValidationError):
            EvaluationProfileCreate(
                name='Test Profile',
                conversational_weights={
                    'faithfulness': 0.2,
                    'relevancy': 0.2,
                    'completeness': 0.2,
                    'knowledge_retention': 0.2,  # Sum = 0.8
                }
            )
    
    def test_name_required(self):
        """Test validation fails without name."""
        with pytest.raises(ValidationError):
            EvaluationProfileCreate(
                single_weights={}
            )
    
    def test_negative_threshold_validation(self):
        """Test allowed threshold keys and value range."""
        profile = EvaluationProfileCreate(
            name='Threshold Profile',
            single_negative_thresholds={'toxicity': 70.0, 'bias': 80.0},
        )
        assert profile.single_negative_thresholds['toxicity'] == 70.0

        with pytest.raises(ValidationError):
            EvaluationProfileCreate(
                name='Invalid Threshold Profile',
                single_negative_thresholds={'foo': 10.0},
            )


class TestSingleEvalRequest:
    """Test SingleEvalRequest schema validation."""
    
    def test_valid_single_eval_request(self):
        """Test creating valid single evaluation request."""
        request = SingleEvalRequest(
            evaluation_profile_id=1,
            judge_llm_profile_id=2,
            prompt="What is the capital of France?",
            actual_response="Paris is the capital of France.",
            retrieved_contexts=[],
            expected_response="Paris is the capital of France.",
        )
        assert request.evaluation_profile_id == 1
        assert request.judge_llm_profile_id == 2
        assert request.prompt is not None
        assert request.actual_response is not None
    
    def test_with_contexts(self):
        """Test single eval request with retrieved contexts."""
        request = SingleEvalRequest(
            evaluation_profile_id=1,
            judge_llm_profile_id=2,
            prompt="What is the capital of France?",
            actual_response="Paris",
            retrieved_contexts=[
                "France's capital is Paris",
                "Paris is located in France"
            ],
            expected_response="Paris"
        )
        assert len(request.retrieved_contexts) == 2
    
    def test_with_expected_response(self):
        """Test single eval request with expected response."""
        request = SingleEvalRequest(
            evaluation_profile_id=1,
            judge_llm_profile_id=2,
            prompt="What is the capital of France?",
            actual_response="Paris",
            retrieved_contexts=[],
            expected_response="Paris, France"
        )
        assert request.expected_response is not None
    
    def test_prompt_required(self):
        """Test validation fails without prompt."""
        with pytest.raises(ValidationError):
            SingleEvalRequest(
                evaluation_profile_id=1,
                judge_llm_profile_id=2,
                actual_response="Some response"
            )
    
    def test_actual_response_required(self):
        """Test validation fails without actual_response."""
        with pytest.raises(ValidationError):
            SingleEvalRequest(
                evaluation_profile_id=1,
                judge_llm_profile_id=2,
                prompt="Some prompt"
            )


class TestConversationalEvalRequest:
    """Test ConversationalEvalRequest schema validation."""
    
    def test_valid_conversational_request(self):
        """Test creating valid conversational evaluation request."""
        request = ConversationalEvalRequest(
            evaluation_profile_id=1,
            judge_llm_profile_id=2,
            chat_history=[
                ChatMessage(role="user", content="What is the capital of France?"),
                ChatMessage(role="assistant", content="Paris"),
            ],
            prompt="What is the capital?",
            actual_response="Paris is the capital of France."
        )
        assert request.evaluation_profile_id == 1
        assert request.judge_llm_profile_id == 2
        assert len(request.chat_history) == 2
    
    def test_empty_chat_history_valid(self):
        """Test conversational request with empty chat history."""
        request = ConversationalEvalRequest(
            evaluation_profile_id=1,
            judge_llm_profile_id=2,
            chat_history=[],
            prompt="Question",
            actual_response="Answer"
        )
        assert request.evaluation_profile_id == 1
    
    def test_with_contexts(self):
        """Test conversational request with retrieved contexts."""
        request = ConversationalEvalRequest(
            evaluation_profile_id=1,
            judge_llm_profile_id=2,
            chat_history=[
                ChatMessage(role="user", content="Hello"),
            ],
            prompt="Hello",
            actual_response="Hi there",
            retrieved_contexts=["Context 1", "Context 2"]
        )
        assert len(request.retrieved_contexts) == 2
    
    def test_prompt_required(self):
        """Test validation fails without prompt."""
        with pytest.raises(ValidationError):
            ConversationalEvalRequest(
                evaluation_profile_id=1,
                judge_llm_profile_id=2,
                chat_history=[],
                actual_response="Response"
            )
    
    def test_actual_response_required(self):
        """Test validation fails without actual_response."""
        with pytest.raises(ValidationError):
            ConversationalEvalRequest(
                evaluation_profile_id=1,
                judge_llm_profile_id=2,
                chat_history=[],
                prompt="Prompt"
            )


class TestChatMessage:
    """Test ChatMessage schema validation."""
    
    def test_valid_user_message(self):
        """Test valid user chat message."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_valid_assistant_message(self):
        """Test valid assistant chat message."""
        msg = ChatMessage(role="assistant", content="Hi there")
        assert msg.role == "assistant"
    
    def test_invalid_role(self):
        """Test validation fails with invalid role."""
        with pytest.raises(ValidationError):
            ChatMessage(role="system", content="Hello")
    
    def test_content_required(self):
        """Test validation fails without content."""
        with pytest.raises(ValidationError):
            ChatMessage(role="user")
