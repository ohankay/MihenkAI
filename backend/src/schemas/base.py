"""Pydantic request/response schemas."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class ProviderEnum(str, Enum):
    """Available LLM providers."""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GEMINI = "Gemini"
    GROK = "Grok"
    DEEPSEEK = "DeepSeek"
    OLLAMA = "Ollama"
    VLLM = "vLLM"


class EvaluationTypeEnum(str, Enum):
    """Evaluation types."""
    SINGLE = "SINGLE"
    CONVERSATIONAL = "CONVERSATIONAL"


class JobStatusEnum(str, Enum):
    """Job status states."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Model Config Schemas
class ModelConfigCreate(BaseModel):
    """Create model config request."""
    name: str = Field(..., min_length=1, max_length=255)
    provider: ProviderEnum
    model_name: str = Field(..., min_length=1, max_length=255)
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    generation_kwargs: Optional[Dict[str, Any]] = None


class ModelConfigUpdate(BaseModel):
    """Update model config request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    provider: Optional[ProviderEnum] = None
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    generation_kwargs: Optional[Dict[str, Any]] = None


class ModelConfigResponse(BaseModel):
    """Model config response."""
    id: int
    name: Optional[str] = None
    provider: str
    model_name: str
    base_url: Optional[str] = None
    temperature: float
    generation_kwargs: Optional[Dict[str, Any]] = None
    has_api_key: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


# Evaluation Profile Schemas
class EvaluationProfileCreate(BaseModel):
    """Create evaluation profile request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model_config_id: int
    single_weights: Dict[str, float] = Field(default_factory=dict)
    conversational_weights: Dict[str, float] = Field(default_factory=dict)
    
    @field_validator('single_weights')
    @classmethod
    def validate_single_weights(cls, v):
        """Validate that weights sum to 1.0 (or 0 if empty)."""
        if v:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):  # Allow small float rounding
                raise ValueError(f"Single weights must sum to 1.0, got {total}")
        return v
    
    @field_validator('conversational_weights')
    @classmethod
    def validate_conversational_weights(cls, v):
        """Validate that weights sum to 1.0 (or 0 if empty)."""
        if v:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):  # Allow small float rounding
                raise ValueError(f"Conversational weights must sum to 1.0, got {total}")
        return v


class EvaluationProfileUpdate(BaseModel):
    """Update evaluation profile request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    model_config_id: Optional[int] = None
    single_weights: Optional[Dict[str, float]] = None
    conversational_weights: Optional[Dict[str, float]] = None
    
    @field_validator('single_weights')
    @classmethod
    def validate_single_weights(cls, v):
        """Validate that weights sum to 1.0 (or 0 if empty)."""
        if v:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):
                raise ValueError(f"Single weights must sum to 1.0, got {total}")
        return v
    
    @field_validator('conversational_weights')
    @classmethod
    def validate_conversational_weights(cls, v):
        """Validate that weights sum to 1.0 (or 0 if empty)."""
        if v:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):
                raise ValueError(f"Conversational weights must sum to 1.0, got {total}")
        return v


class EvaluationProfileResponse(BaseModel):
    """Evaluation profile response."""
    id: int
    name: str
    description: Optional[str]
    model_config_id: int
    single_weights: Dict[str, float]
    conversational_weights: Dict[str, float]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Evaluation Request Schemas
class ChatMessage(BaseModel):
    """Chat message for conversational evaluation."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class SingleEvalRequest(BaseModel):
    """Request for single evaluation."""
    profile_id: int
    model_config_id: Optional[int] = None  # Override the judge LLM from profile
    prompt: str
    actual_response: str
    retrieved_contexts: List[str] = Field(..., description="Alınan bağlamlar (RAG). Boş liste gönderilebilir ama alan zorunludur.")
    expected_response: str = Field(..., description="Beklenen/referans yanıt. Tüm single metrikler için zorunludur.")


class ConversationalEvalRequest(BaseModel):
    """Request for conversational evaluation."""
    profile_id: int
    model_config_id: Optional[int] = None  # Override the judge LLM from profile
    chat_history: List[ChatMessage] = Field(default_factory=list)
    prompt: str
    actual_response: str
    retrieved_contexts: List[str] = Field(default_factory=list)


# Job Response Schemas
class JobQueuedResponse(BaseModel):
    """Response when job is queued."""
    status: str = "QUEUED"
    job_id: str


class MetricScore(BaseModel):
    """Single metric score with weight."""
    score: float
    weight: float


class EvaluationResult(BaseModel):
    """Complete evaluation result."""
    job_id: str
    status: str
    composite_score: Optional[float] = None
    metrics_breakdown: Optional[Dict[str, MetricScore]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    composite_score: Optional[float] = None
    metrics_breakdown: Optional[Dict[str, Dict[str, float]]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Configuration Schemas
class ConfigData(BaseModel):
    """Bootstrap configuration data."""
    db_host: str
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str
    redis_host: str
    redis_port: int = 6379


class ConfigResponse(BaseModel):
    """Configuration response."""
    status: str
    message: str
