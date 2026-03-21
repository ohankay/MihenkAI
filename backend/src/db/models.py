"""SQLAlchemy ORM models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ModelConfig(Base):
    """LLM model configuration for evaluation."""
    
    __tablename__ = 'model_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)  # Human-readable profile name
    provider = Column(String(50), nullable=False)  # OpenAI, Anthropic, Ollama, vLLM
    model_name = Column(String(255), nullable=False)  # gpt-4o, llama3, etc.
    api_key = Column(Text, nullable=True)  # Will be encrypted
    base_url = Column(String(255), nullable=True)  # For local models
    temperature = Column(Float, nullable=False, default=0.0)
    generation_kwargs = Column(JSONB, nullable=True)  # Extra params: max_tokens, top_p, etc.
    system_prompt = Column(Text, nullable=True)  # Optional system prompt prepended to every LLM call
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    llm_query_logs = relationship('LLMQueryLog', back_populates='model_config', cascade='all, delete-orphan')

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)
    
    def __repr__(self):
        return f"<ModelConfig(id={self.id}, provider={self.provider}, model={self.model_name})>"


class EvaluationProfile(Base):
    """Test profile template with metrics and weights."""
    
    __tablename__ = 'evaluation_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    single_weights = Column(JSONB, nullable=False, default={})  # {"faithfulness": 0.6, "answer_relevancy": 0.4}
    # Penalty metrics — threshold values (0–100). If a metric score >= threshold the composite is zeroed.
    single_negative_thresholds = Column(JSONB, nullable=True, server_default='{}')  # {"hallucination": 50.0, "bias": 30.0}
    conversational_weights = Column(JSONB, nullable=False, default={})  # {"knowledge_retention": 0.5, ...}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evaluation_jobs = relationship('EvaluationJob', back_populates='evaluation_profile')
    
    def __repr__(self):
        return f"<EvaluationProfile(id={self.id}, name={self.name})>"


class EvaluationJob(Base):
    """Evaluation job records and results."""
    
    __tablename__ = 'evaluation_jobs'
    
    job_id = Column(String(50), primary_key=True)  # eval-{uuid4}
    profile_id = Column(Integer, ForeignKey('evaluation_profiles.id'), nullable=False)
    evaluation_type = Column(String(50), nullable=False)  # SINGLE, CONVERSATIONAL
    status = Column(String(50), nullable=False, default='QUEUED')  # QUEUED, PROCESSING, COMPLETED, FAILED
    composite_score = Column(Float, nullable=True)  # 0-100
    metrics_breakdown = Column(JSONB, nullable=True)  # {metric: {score, weight}}
    request_payload = Column(JSONB, nullable=True)  # Original evaluation request body
    result_payload = Column(JSONB, nullable=True)  # Final evaluation output payload
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    evaluation_profile = relationship('EvaluationProfile', back_populates='evaluation_jobs')
    
    __table_args__ = (
        Index('ix_evaluation_jobs_profile_id', 'profile_id'),
        Index('ix_evaluation_jobs_status', 'status'),
        Index('ix_evaluation_jobs_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<EvaluationJob(job_id={self.job_id}, status={self.status})>"


class LLMQueryLog(Base):
    """Stores prompt/response logs for model-level chat tests."""

    __tablename__ = 'llm_query_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_config_id = Column(Integer, ForeignKey('model_configs.id', ondelete='CASCADE'), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    model_config = relationship('ModelConfig', back_populates='llm_query_logs')

    __table_args__ = (
        Index('ix_llm_query_logs_model_config_id', 'model_config_id'),
        Index('ix_llm_query_logs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<LLMQueryLog(id={self.id}, model_config_id={self.model_config_id})>"
