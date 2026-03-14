"""DeepEval integration for LLM evaluation."""
import logging
from typing import Dict, List, Optional, Any
from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics import (
    Faithfulness,
    AnswerRelevancy,
)
import os

logger = logging.getLogger(__name__)


class DeepEvalClient:
    """Client for DeepEval metric calculations."""
    
    def __init__(self, model_config):
        """
        Initialize DeepEval client with model configuration.
        
        Args:
            model_config: ModelConfig database object with provider, model_name, api_key, etc.
        """
        self.model_config = model_config
        self.judge_model = self._create_judge_model()
    
    def _create_judge_model(self) -> DeepEvalBaseLLM:
        """
        Create judge model based on provider.
        
        Returns:
            DeepEvalBaseLLM instance
        """
        from deepeval.models import GPTModel, ClaudeModel, OllamaModel
        
        provider = self.model_config.provider.lower()
        model_name = self.model_config.model_name
        
        try:
            if provider == "openai":
                api_key = self.model_config.api_key or os.getenv('OPENAI_API_KEY')
                model = GPTModel(
                    name=model_name,
                    api_key=api_key
                )
                logger.info(f"Initialized OpenAI model: {model_name}")
                
            elif provider == "anthropic":
                api_key = self.model_config.api_key or os.getenv('ANTHROPIC_API_KEY')
                model = ClaudeModel(
                    name=model_name,
                    api_key=api_key
                )
                logger.info(f"Initialized Anthropic model: {model_name}")
                
            elif provider == "ollama":
                base_url = self.model_config.base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
                model = OllamaModel(
                    name=model_name,
                    base_url=base_url
                )
                logger.info(f"Initialized Ollama model: {model_name}")
                
            elif provider == "vllm":
                base_url = self.model_config.base_url or os.getenv('VLLM_BASE_URL', 'http://localhost:8000')
                # vLLM uses OpenAI-compatible API
                model = GPTModel(
                    name=model_name,
                    api_key="not-needed",  # vLLM doesn't require API key
                    base_url=base_url
                )
                logger.info(f"Initialized vLLM model: {model_name}")
                
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            return model
        except Exception as e:
            logger.error(f"Error initializing judge model: {str(e)}")
            raise
    
    async def evaluate_single(
        self,
        prompt: str,
        actual_response: str,
        retrieved_contexts: List[str],
        expected_response: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a single LLM response.
        
        Args:
            prompt: User prompt/question
            actual_response: LLM's response
            retrieved_contexts: Retrieved context documents
            expected_response: Expected ideal response (optional)
            weights: Metric weights ({"faithfulness": 0.6, "answer_relevancy": 0.4})
            
        Returns:
            Dictionary of metrics with scores and weights
        """
        try:
            logger.info("Starting single evaluation")
            
            metrics = {}
            
            # Default weights if not provided
            if not weights:
                weights = {
                    "faithfulness": 0.6,
                    "answer_relevancy": 0.4
                }
            
            # Evaluate faithfulness
            if "faithfulness" in weights:
                context_str = "\n".join(retrieved_contexts) if retrieved_contexts else ""
                metric = Faithfulness(
                    model=self.judge_model,
                    threshold=0.5,
                )
                # Note: In real implementation, you would call metric.measure()
                # For now, we'll use placeholder scoring logic
                score = self._evaluate_faithfulness_placeholder(
                    actual_response,
                    context_str
                )
                metrics["faithfulness"] = {
                    "score": score,
                    "weight": weights["faithfulness"]
                }
                logger.info(f"Faithfulness score: {score}")
            
            # Evaluate answer relevancy
            if "answer_relevancy" in weights:
                metric = AnswerRelevancy(
                    model=self.judge_model,
                    threshold=0.5,
                )
                # Note: In real implementation, you would call metric.measure()
                score = self._evaluate_relevancy_placeholder(
                    prompt,
                    actual_response
                )
                metrics["answer_relevancy"] = {
                    "score": score,
                    "weight": weights["answer_relevancy"]
                }
                logger.info(f"Answer relevancy score: {score}")
            
            return metrics
        except Exception as e:
            logger.error(f"Error in single evaluation: {str(e)}")
            raise
    
    async def evaluate_conversational(
        self,
        chat_history: List[Dict[str, str]],
        prompt: str,
        actual_response: str,
        retrieved_contexts: List[str],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate conversational response.
        
        Args:
            chat_history: Previous conversation turns
            prompt: Current user prompt
            actual_response: Current LLM response
            retrieved_contexts: Retrieved context documents
            weights: Metric weights
            
        Returns:
            Dictionary of metrics with scores and weights
        """
        try:
            logger.info("Starting conversational evaluation")
            
            metrics = {}
            
            # Default weights if not provided
            if not weights:
                weights = {
                    "knowledge_retention": 0.5,
                    "conversation_completeness": 0.5
                }
            
            # Evaluate knowledge retention
            if "knowledge_retention" in weights:
                score = self._evaluate_knowledge_retention_placeholder(
                    chat_history,
                    actual_response
                )
                metrics["knowledge_retention"] = {
                    "score": score,
                    "weight": weights["knowledge_retention"]
                }
                logger.info(f"Knowledge retention score: {score}")
            
            # Evaluate conversation completeness
            if "conversation_completeness" in weights:
                score = self._evaluate_completeness_placeholder(
                    prompt,
                    actual_response
                )
                metrics["conversation_completeness"] = {
                    "score": score,
                    "weight": weights["conversation_completeness"]
                }
                logger.info(f"Conversation completeness score: {score}")
            
            return metrics
        except Exception as e:
            logger.error(f"Error in conversational evaluation: {str(e)}")
            raise
    
    async def calculate_composite_score(self, metrics: Dict[str, Dict[str, float]]) -> float:
        """
        Calculate composite score from individual metrics.
        
        Formula: composite_score = Σ(metric_score × weight)
        
        Args:
            metrics: Dictionary of metrics with scores and weights
            
        Returns:
            Composite score (0-100)
        """
        try:
            if not metrics:
                return 0.0
            
            composite = 0.0
            total_weight = 0.0
            
            for metric_name, metric_data in metrics.items():
                score = metric_data.get("score", 0)
                weight = metric_data.get("weight", 0)
                
                composite += score * weight
                total_weight += weight
            
            # Normalize if necessary
            if total_weight > 0:
                composite = composite  # Already weighted
            
            return min(100.0, max(0.0, composite))  # Clamp to 0-100
        except Exception as e:
            logger.error(f"Error calculating composite score: {str(e)}")
            raise
    
    # Placeholder evaluation methods (to be replaced with actual DeepEval calls)
    
    def _evaluate_faithfulness_placeholder(self, response: str, context: str) -> float:
        """Placeholder faithfulness evaluation."""
        # In production, this would use DeepEval's Faithfulness metric
        # For now, we use simple heuristics
        if not context:
            return 50.0
        
        # Check if response mentions key terms from context
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        
        if not context_words:
            return 50.0
        
        overlap = len(context_words & response_words) / len(context_words)
        return min(100.0, overlap * 100.0 + 50.0)  # Range 50-100
    
    def _evaluate_relevancy_placeholder(self, prompt: str, response: str) -> float:
        """Placeholder relevancy evaluation."""
        if not response:
            return 0.0
        
        # Check if response contains meaningful content
        response_length = len(response.split())
        prompt_length = len(prompt.split())
        
        if response_length < prompt_length * 0.5:
            return 40.0
        elif response_length > prompt_length * 10:
            return 70.0
        else:
            return 80.0
    
    def _evaluate_knowledge_retention_placeholder(self, chat_history: List[Dict], response: str) -> float:
        """Placeholder knowledge retention evaluation."""
        if not chat_history:
            return 50.0
        
        # Check if response references previous conversations
        all_previous = " ".join([msg.get("content", "") for msg in chat_history])
        previous_words = set(all_previous.lower().split())
        response_words = set(response.lower().split())
        
        if not previous_words:
            return 50.0
        
        overlap = len(previous_words & response_words) / len(previous_words)
        return min(100.0, overlap * 100.0)
    
    def _evaluate_completeness_placeholder(self, prompt: str, response: str) -> float:
        """Placeholder completeness evaluation."""
        if not response:
            return 0.0
        
        # Simple heuristic: longer, more detailed responses are more complete
        response_length = len(response.split())
        
        if response_length < 10:
            return 30.0
        elif response_length < 30:
            return 60.0
        else:
            return 85.0
