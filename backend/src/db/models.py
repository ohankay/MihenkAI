"""SQLAlchemy ORM models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ModelConfig(Base):
    """LLM model configuration for evaluation."""
    
    __tablename__ = 'model_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False)  # OpenAI, Anthropic, Ollama, vLLM
    model_name = Column(String(255), nullable=False)  # gpt-4o, llama3, etc.
    api_key = Column(Text, nullable=True)  # Will be encrypted
    base_url = Column(String(255), nullable=True)  # For local models
    temperature = Column(Float, nullable=False, default=0.0)
    generation_kwargs = Column(JSONB, nullable=True)  # Extra params: max_tokens, top_p, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evaluation_profiles = relationship('EvaluationProfile', back_populates='model_config')
    
    def __repr__(self):
        return f"<ModelConfig(id={self.id}, provider={self.provider}, model={self.model_name})>"


class EvaluationProfile(Base):
    """Test profile template with metrics and weights."""
    
    __tablename__ = 'evaluation_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_config_id = Column(Integer, ForeignKey('model_configs.id'), nullable=False)
    single_weights = Column(JSONB, nullable=False, default={})  # {"faithfulness": 0.6, "answer_relevancy": 0.4}
    conversational_weights = Column(JSONB, nullable=False, default={})  # {"knowledge_retention": 0.5, ...}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model_config = relationship('ModelConfig', back_populates='evaluation_profiles')
    evaluation_jobs = relationship('EvaluationJob', back_populates='evaluation_profile')
    
    __table_args__ = (
        Index('ix_evaluation_profiles_model_config_id', 'model_config_id'),
    )
    
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
