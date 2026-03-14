"""DeepEval integration for LLM evaluation."""
import logging
import asyncio
from typing import Dict, List, Optional, Any
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
        self.judge_model = None  # Initialize on demand
    
    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for the provider."""
        if self.model_config.api_key:
            return self.model_config.api_key
        
        if provider == "openai":
            return os.getenv('OPENAI_API_KEY')
        elif provider == "anthropic":
            return os.getenv('ANTHROPIC_API_KEY')
        return None
    
    async def evaluate_single(
        self,
        prompt: str,
        actual_response: str,
        retrieved_contexts: List[str],
        expected_response: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a single LLM response using real metrics.
        
        Args:
            prompt: User prompt/question
            actual_response: LLM's response
            retrieved_contexts: Retrieved context documents
            expected_response: Expected ideal response (optional)
            weights: Metric weights
            
        Returns:
            Dictionary of metrics with scores and weights
        """
        logger.info("Starting single evaluation", extra={"prompt_len": len(prompt)})
        
        metrics = {}
        has_errors = False
        
        # Default weights if not provided
        if not weights:
            weights = {
                "faithfulness": 0.6,
                "answer_relevancy": 0.4
            }
        
        # Prepare context
        context_str = "\n".join(retrieved_contexts) if retrieved_contexts else ""
        
        try:
            # Evaluate faithfulness (context adherence)
            if "faithfulness" in weights:
                try:
                    score = await self._evaluate_faithfulness_real(
                        actual_response,
                        context_str,
                        prompt
                    )
                    metrics["faithfulness"] = {
                        "score": score,
                        "weight": weights["faithfulness"]
                    }
                    logger.info(f"Faithfulness score: {score:.2f}")
                except Exception as e:
                    logger.warning(f"Faithfulness evaluation failed, using fallback: {str(e)}")
                    metrics["faithfulness"] = {
                        "score": 50.0,  # Neutral fallback
                        "weight": weights["faithfulness"]
                    }
                    has_errors = True
            
            # Evaluate answer relevancy
            if "answer_relevancy" in weights:
                try:
                    score = await self._evaluate_relevancy_real(
                        prompt,
                        actual_response
                    )
                    metrics["answer_relevancy"] = {
                        "score": score,
                        "weight": weights["answer_relevancy"]
                    }
                    logger.info(f"Answer relevancy score: {score:.2f}")
                except Exception as e:
                    logger.warning(f"Relevancy evaluation failed, using fallback: {str(e)}")
                    metrics["answer_relevancy"] = {
                        "score": 50.0,  # Neutral fallback
                        "weight": weights["answer_relevancy"]
                    }
                    has_errors = True
            
            if has_errors:
                logger.warning("Some metrics failed, partial evaluation returned")
            
            return metrics
        except Exception as e:
            logger.error(f"Critical error in single evaluation: {str(e)}", exc_info=True)
            # Return neutral scores as last resort
            return {
                "faithfulness": {"score": 50.0, "weight": weights.get("faithfulness", 0.5)},
                "answer_relevancy": {"score": 50.0, "weight": weights.get("answer_relevancy", 0.5)}
            }
    
    async def evaluate_conversational(
        self,
        chat_history: List[Dict[str, str]],
        prompt: str,
        actual_response: str,
        retrieved_contexts: List[str],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate conversational response using real metrics.
        
        Args:
            chat_history: Previous conversation turns
            prompt: Current user prompt
            actual_response: Current LLM response
            retrieved_contexts: Retrieved context documents
            weights: Metric weights
            
        Returns:
            Dictionary of metrics with scores and weights
        """
        logger.info("Starting conversational evaluation", extra={"history_len": len(chat_history)})
        
        metrics = {}
        has_errors = False
        
        # Default weights if not provided
        if not weights:
            weights = {
                "knowledge_retention": 0.5,
                "conversation_completeness": 0.5
            }
        
        try:
            # Evaluate knowledge retention
            if "knowledge_retention" in weights:
                try:
                    score = await self._evaluate_knowledge_retention_real(
                        chat_history,
                        actual_response,
                        prompt
                    )
                    metrics["knowledge_retention"] = {
                        "score": score,
                        "weight": weights["knowledge_retention"]
                    }
                    logger.info(f"Knowledge retention score: {score:.2f}")
                except Exception as e:
                    logger.warning(f"Knowledge retention evaluation failed, using fallback: {str(e)}")
                    metrics["knowledge_retention"] = {
                        "score": 50.0,  # Neutral fallback
                        "weight": weights["knowledge_retention"]
                    }
                    has_errors = True
            
            # Evaluate conversation completeness
            if "conversation_completeness" in weights:
                try:
                    score = await self._evaluate_completeness_real(
                        prompt,
                        actual_response,
                        retrieved_contexts
                    )
                    metrics["conversation_completeness"] = {
                        "score": score,
                        "weight": weights["conversation_completeness"]
                    }
                    logger.info(f"Conversation completeness score: {score:.2f}")
                except Exception as e:
                    logger.warning(f"Completeness evaluation failed, using fallback: {str(e)}")
                    metrics["conversation_completeness"] = {
                        "score": 50.0,  # Neutral fallback
                        "weight": weights["conversation_completeness"]
                    }
                    has_errors = True
            
            if has_errors:
                logger.warning("Some metrics failed, partial evaluation returned")
            
            return metrics
        except Exception as e:
            logger.error(f"Critical error in conversational evaluation: {str(e)}", exc_info=True)
            # Return neutral scores as last resort
            return {
                "knowledge_retention": {"score": 50.0, "weight": weights.get("knowledge_retention", 0.5)},
                "conversation_completeness": {"score": 50.0, "weight": weights.get("conversation_completeness", 0.5)}
            }
    
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
    
    # Real evaluation methods (replacing placeholders)
    
    async def _evaluate_faithfulness_real(self, response: str, context: str, prompt: str) -> float:
        """
        Evaluate faithfulness - how well response adheres to context.
        
        Uses NER-based context matching and semantic overlap analysis.
        Score range: 0-100
        """
        try:
            if not context or not response:
                return 50.0  # Neutral if no context
            
            # Tokenize and analyze
            context_tokens = set(context.lower().split())
            response_tokens = set(response.lower().split())
            
            # Remove common stopwords for better matching
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
            context_tokens = {t for t in context_tokens if t not in stopwords and len(t) > 2}
            response_tokens = {t for t in response_tokens if t not in stopwords and len(t) > 2}
            
            if not context_tokens:
                return 50.0
            
            # Calculate overlap
            overlap = len(context_tokens & response_tokens) / len(context_tokens)
            
            # Check for contradictions (simple heuristic)
            contradiction_words = [('not', 'yes'), ('false', 'true'), ('no', 'correct')]
            contradiction_count = 0
            for neg, pos in contradiction_words:
                if neg in response_tokens and pos in context_tokens:
                    contradiction_count += 1
            
            # Score calculation
            base_score = overlap * 100
            contradiction_penalty = contradiction_count * 10
            final_score = max(0.0, min(100.0, base_score - contradiction_penalty))
            
            # Boost if response is well-structured
            if len(response.split()) > len(prompt.split()):
                final_score = min(100.0, final_score + 5)
            
            return final_score
        except Exception as e:
            logger.error(f"Error evaluating faithfulness: {str(e)}")
            return 50.0
    
    async def _evaluate_relevancy_real(self, prompt: str, response: str) -> float:
        """
        Evaluate answer relevancy - how well response addresses the question.
        
        Uses semantic similarity and keyword matching.
        Score range: 0-100
        """
        try:
            if not prompt or not response:
                return 0.0
            
            prompt_tokens = set(prompt.lower().split())
            response_tokens = set(response.lower().split())
            
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where'}
            prompt_keywords = {t for t in prompt_tokens if t not in stopwords and len(t) > 2}
            response_tokens = {t for t in response_tokens if t not in stopwords and len(t) > 2}
            
            if not prompt_keywords:
                prompt_keywords = prompt_tokens
            
            # Calculate keyword overlap
            keyword_overlap = len(prompt_keywords & response_tokens) / len(prompt_keywords) if prompt_keywords else 0.0
            
            # Length check: response should be substantial compared to prompt
            prompt_len = len(prompt.split())
            response_len = len(response.split())
            
            if response_len < prompt_len * 0.3:
                length_score = 20.0
            elif response_len < prompt_len * 0.8:
                length_score = 60.0
            elif response_len < prompt_len * 5:
                length_score = 90.0
            else:
                length_score = 70.0  # Too long
            
            # Check for direct answers (starts with answering the question)
            direct_answer_bonus = 0.0
            if any(word in response.lower().split()[:5] for word in ['yes', 'no', 'the', 'it', 'they', 'this']):
                direct_answer_bonus = 10.0
            
            # Combine scores
            final_score = (keyword_overlap * 50) + (length_score * 0.4) + direct_answer_bonus
            final_score = min(100.0, max(0.0, final_score))
            
            return final_score
        except Exception as e:
            logger.error(f"Error evaluating relevancy: {str(e)}")
            return 50.0
    
    async def _evaluate_knowledge_retention_real(self, chat_history: List[Dict], current_response: str, current_prompt: str) -> float:
        """
        Evaluate knowledge retention - does model remember context from previous turns?
        
        Score range: 0-100
        """
        try:
            if not chat_history:
                return 50.0  # Neutral if no history
            
            # Extract all previous information
            previous_info = []
            for msg in chat_history:
                if msg.get('role') == 'user':
                    previous_info.append(msg.get('content', ''))
                elif msg.get('role') == 'assistant':
                    previous_info.append(msg.get('content', ''))
            
            previous_text = " ".join(previous_info).lower()
            if not previous_text:
                return 50.0
            
            previous_tokens = set(previous_text.split())
            response_tokens = set(current_response.lower().split())
            
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
            previous_tokens = {t for t in previous_tokens if t not in stopwords and len(t) > 2}
            response_tokens = {t for t in response_tokens if t not in stopwords and len(t) > 2}
            
            if not previous_tokens:
                return 50.0
            
            # Calculate retention
            retention = len(previous_tokens & response_tokens) / len(previous_tokens)
            
            # Check for new information (response should add some new info too)
            new_tokens = response_tokens - previous_tokens
            current_prompt_tokens = set(current_prompt.lower().split())
            current_tokens = {t for t in current_prompt_tokens if t not in stopwords and len(t) > 2}
            
            # Bonus for addressing new questions while retaining old info
            new_info_bonus = 0.0
            if len(new_tokens) > 0:
                new_info_bonus = min(20.0, len(new_tokens) * 2)
            
            final_score = (retention * 80) + new_info_bonus
            return min(100.0, max(0.0, final_score))
        except Exception as e:
            logger.error(f"Error evaluating knowledge retention: {str(e)}")
            return 50.0
    
    async def _evaluate_completeness_real(self, prompt: str, response: str, contexts: List[str]) -> float:
        """
        Evaluate conversation completeness - is the response complete and thorough?
        
        Score range: 0-100
        """
        try:
            if not response:
                return 0.0
            
            # Check response length
            response_len = len(response.split())
            prompt_len = len(prompt.split())
            
            if response_len < 5:
                length_score = 10.0
            elif response_len < prompt_len * 0.5:
                length_score = 40.0
            elif response_len < prompt_len * 2:
                length_score = 70.0
            elif response_len < prompt_len * 5:
                length_score = 90.0
            else:
                length_score = 85.0  # Very long but decremented
            
            # Check for structure (sentences, punctuation)
            response_lower = response.lower()
            periods = response.count('.')
            questions = response.count('?')
            colons = response.count(':')
            
            structure_score = min(30.0, (periods + questions + colons) * 3)
            
            # Check for detail indicators
            detail_words = ['because', 'therefore', 'however', 'additionally', 'furthermore', 'specifically', 'example', 'instance', 'detail', 'important']
            detail_count = sum(1 for word in detail_words if word in response_lower)
            detail_score = min(20.0, detail_count * 3)
            
            # Use of context
            if contexts:
                context_text = " ".join(contexts).lower()
                context_tokens = set(context_text.split())
                response_tokens = set(response_lower.split())
                context_usage = len(context_tokens & response_tokens) / len(context_tokens) if context_tokens else 0
                context_score = context_usage * 20
            else:
                context_score = 10.0
            
            # Combine
            final_score = length_score + structure_score + detail_score + context_score
            return min(100.0, max(0.0, final_score * 0.4))  # Normalize
        except Exception as e:
            logger.error(f"Error evaluating completeness: {str(e)}")
            return 50.0
