"""Pydantic request/response schemas."""
from pydantic import BaseModel, Field, field_validator, ConfigDict
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
    ABORTED = "ABORTED"


# Penalty metrics — not allowed in positive weights, managed via thresholds instead.
_NEGATIVE_METRIC_KEYS = frozenset({"hallucination", "bias", "toxicity"})


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
    system_prompt: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())


class ModelConfigUpdate(BaseModel):
    """Update model config request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    provider: Optional[ProviderEnum] = None
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    generation_kwargs: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())


class ModelConfigResponse(BaseModel):
    """Model config response."""
    id: int
    name: Optional[str] = None
    provider: str
    model_name: str
    base_url: Optional[str] = None
    temperature: float
    generation_kwargs: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    has_api_key: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelChatTestRequest(BaseModel):
    """Request payload for quick model QA test."""
    prompt: str = Field(..., min_length=1, max_length=8000)


class ModelChatTestResponse(BaseModel):
    """Response payload for quick model QA test."""
    model_config_id: int
    provider: str
    model_name: str
    prompt: str
    response: str
    latency_ms: int

    model_config = ConfigDict(protected_namespaces=())


class LLMQueryLogSummaryResponse(BaseModel):
    """Summary row for LLM query log list."""
    id: int
    model_config_id: int
    created_at: datetime
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class LLMQueryLogDetailResponse(BaseModel):
    """Detailed LLM query log row with prompt/response payload."""
    id: int
    model_config_id: int
    prompt: str
    response: Optional[str] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class LLMQueryLogListResponse(BaseModel):
    """Paginated response for LLM query log list."""
    items: List[LLMQueryLogSummaryResponse]
    limit: int
    offset: int = 0
    count: int
    total: int
    has_next: bool
    start_time: datetime
    end_time: datetime


# Evaluation Profile Schemas
class EvaluationProfileCreate(BaseModel):
    """Create evaluation profile request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    single_weights: Dict[str, float] = Field(default_factory=dict)
    # Penalty metrics with threshold values (0–100). If score >= threshold the composite is zeroed.
    single_negative_thresholds: Dict[str, float] = Field(default_factory=dict)
    conversational_weights: Dict[str, float] = Field(default_factory=dict)

    @field_validator('single_weights')
    @classmethod
    def validate_single_weights(cls, v):
        """Validate that weights sum to 1.0. Penalty metric keys are silently stripped
        so legacy profiles that stored HAB in positive weights can still be saved."""
        v = {k: val for k, val in v.items() if k not in _NEGATIVE_METRIC_KEYS}
        if v:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):
                raise ValueError(f"Single weights must sum to 1.0, got {total}")
        return v

    @field_validator('single_negative_thresholds')
    @classmethod
    def validate_single_negative_thresholds(cls, v):
        """Validate keys and value range (0–100)."""
        bad = set(v.keys()) - _NEGATIVE_METRIC_KEYS
        if bad:
            raise ValueError(
                f"single_negative_thresholds only accepts {sorted(_NEGATIVE_METRIC_KEYS)}, got {sorted(bad)}"
            )
        for key, val in v.items():
            if not (0.0 <= val <= 100.0):
                raise ValueError(f"{key} threshold must be between 0 and 100, got {val}")
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
    single_weights: Optional[Dict[str, float]] = None
    single_negative_thresholds: Optional[Dict[str, float]] = None
    conversational_weights: Optional[Dict[str, float]] = None

    @field_validator('single_weights')
    @classmethod
    def validate_single_weights(cls, v):
        """Validate that weights sum to 1.0. Penalty metric keys are silently stripped
        so legacy profiles that stored HAB in positive weights can still be saved."""
        if v is None:
            return v
        v = {k: val for k, val in v.items() if k not in _NEGATIVE_METRIC_KEYS}
        if v:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):
                raise ValueError(f"Single weights must sum to 1.0, got {total}")
        return v

    @field_validator('single_negative_thresholds')
    @classmethod
    def validate_single_negative_thresholds(cls, v):
        if v is None:
            return v
        bad = set(v.keys()) - _NEGATIVE_METRIC_KEYS
        if bad:
            raise ValueError(
                f"single_negative_thresholds only accepts {_NEGATIVE_METRIC_KEYS}, got {bad}"
            )
        for key, val in v.items():
            if not (0.0 <= val <= 100.0):
                raise ValueError(f"{key} threshold must be between 0 and 100, got {val}")
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
    single_weights: Dict[str, float]
    single_negative_thresholds: Dict[str, float] = Field(default_factory=dict)
    conversational_weights: Dict[str, float]
    created_at: datetime

    @field_validator('single_negative_thresholds', mode='before')
    @classmethod
    def coerce_none_thresholds(cls, v):
        """Coerce NULL DB values to empty dict."""
        return v if v is not None else {}

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# Evaluation Request Schemas
class ChatMessage(BaseModel):
    """Chat message for conversational evaluation."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class SingleEvalRequest(BaseModel):
    """Request for single evaluation."""
    evaluation_profile_id: int
    judge_llm_profile_id: int  # Judge LLM (ModelConfig) — required at test time
    prompt: str
    actual_response: str
    retrieved_contexts: List[str] = Field(..., description="Alınan bağlamlar (RAG). Boş liste gönderilebilir ama alan zorunludur.")
    expected_response: str = Field(..., description="Beklenen/referans yanıt. Tüm single metrikler için zorunludur.")


class ConversationalEvalRequest(BaseModel):
    """Request for conversational evaluation."""
    evaluation_profile_id: int
    judge_llm_profile_id: int  # Judge LLM (ModelConfig) — required at test time
    chat_history: List[ChatMessage] = Field(default_factory=list)
    prompt: str
    actual_response: str
    retrieved_contexts: List[str] = Field(default_factory=list)
    scenario: Optional[str] = Field(None, description="Chatbot'un amacı/rolunu tanımlayan senaryo. ConversationCompleteness metriği için kullanılır.")
    expected_outcome: Optional[str] = Field(None, description="Konuşmanın ulaşması gereken sonuç. ConversationCompleteness metriği için kullanılır.")


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
    metrics_breakdown: Optional[Dict[str, Dict[str, Any]]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationJobSummaryResponse(BaseModel):
    """Compact job data for monitoring list."""
    job_id: str
    profile_id: int
    evaluation_type: str
    status: str
    composite_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationJobListResponse(BaseModel):
    """Paginated evaluation jobs response."""
    items: List[EvaluationJobSummaryResponse]
    jobs: List[EvaluationJobSummaryResponse] = Field(default_factory=list)  # legacy compatibility
    limit: int
    offset: int
    count: int
    total: int
    has_next: bool


class EvaluationJobDetailResponse(BaseModel):
    """Detailed job payload for monitoring detail panel."""
    job_id: str
    profile_id: int
    evaluation_type: str
    status: str
    composite_score: Optional[float] = None
    metrics_breakdown: Optional[Dict[str, Dict[str, Any]]] = None
    request_payload: Optional[Dict[str, Any]] = None
    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class AbortJobsRequest(BaseModel):
    """Abort request for one or more job IDs."""
    job_ids: List[str] = Field(default_factory=list)


class AbortJobsResponse(BaseModel):
    """Abort operation summary."""
    aborted_job_ids: List[str]
    skipped_job_ids: List[str]
    not_found_job_ids: List[str]


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
