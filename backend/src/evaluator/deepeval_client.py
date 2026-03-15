"""DeepEval integration — real LLM judge metrics."""
import logging
import asyncio
import os
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, ConversationalTestCase

# ── Core single metrics (always available) ──────────────────────────────────
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

# ── Extended single metrics ──────────────────────────────────────────────────
try:
    from deepeval.metrics import (
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        ContextualRelevancyMetric,
    )
    _HAS_CONTEXTUAL = True
except ImportError:
    ContextualPrecisionMetric = ContextualRecallMetric = ContextualRelevancyMetric = None
    _HAS_CONTEXTUAL = False

try:
    from deepeval.metrics import HallucinationMetric
    _HAS_HALLUCINATION = True
except ImportError:
    HallucinationMetric = None
    _HAS_HALLUCINATION = False

try:
    from deepeval.metrics import BiasMetric
    _HAS_BIAS = True
except ImportError:
    BiasMetric = None
    _HAS_BIAS = False

try:
    from deepeval.metrics import ToxicityMetric
    _HAS_TOXICITY = True
except ImportError:
    ToxicityMetric = None
    _HAS_TOXICITY = False

# ── Conversational metrics ───────────────────────────────────────────────────
try:
    from deepeval.metrics import KnowledgeRetentionMetric, ConversationCompletenessMetric
    _HAS_CONVERSATIONAL_BASE = True
except ImportError:
    KnowledgeRetentionMetric = ConversationCompletenessMetric = None
    _HAS_CONVERSATIONAL_BASE = False

try:
    from deepeval.metrics import ConversationRelevancyMetric
    _HAS_CONV_RELEVANCY = True
except ImportError:
    ConversationRelevancyMetric = None
    _HAS_CONV_RELEVANCY = False

logger = logging.getLogger(__name__)

# Thread pool — DeepEval metrics are synchronous (they make HTTP calls internally)
_executor = ThreadPoolExecutor(max_workers=4)


class _LLMJudge(DeepEvalBaseLLM):
    """
    Custom DeepEval judge model supporting OpenAI, Anthropic,
    and any OpenAI-compatible provider (Ollama, vLLM).
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: Optional[str],
        base_url: Optional[str],
        temperature: float = 0.0,
        generation_kwargs: Optional[dict] = None,
    ):
        self._provider = provider.lower()
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url
        self._temperature = temperature
        self._generation_kwargs = generation_kwargs or {}

    # ---- DeepEvalBaseLLM abstract interface ----

    def load_model(self):
        return self  # no external state; clients are created per-call

    def generate(self, prompt: str, schema=None) -> str:
        """Synchronous LLM call — invoked inside thread pool by _run()."""
        if self._provider == "anthropic":
            return self._call_anthropic(prompt)
        return self._call_openai_compat(prompt)

    async def a_generate(self, prompt: str, schema=None) -> str:
        """Async LLM call — delegates to synchronous generate via executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.generate(prompt, schema))

    def get_model_name(self) -> str:
        return self._model_name

    # ---- Provider implementations ----

    def _call_openai_compat(self, prompt: str) -> str:
        """
        OpenAI and OpenAI-compatible providers (Ollama, vLLM).
        For Ollama:  base_url="http://host.docker.internal:11434/v1", api_key="ollama"
        For vLLM:   base_url="http://host.docker.internal:8080/v1"
        """
        from openai import OpenAI

        # OpenAI SDK requires a non-None api_key; use env var or a placeholder
        # so that providers which don't validate keys (Ollama, local) still work.
        api_key = self._api_key or os.environ.get("OPENAI_API_KEY") or "not-required"
        client = OpenAI(api_key=api_key, base_url=self._base_url or None)
        kwargs = dict(self._generation_kwargs) if self._generation_kwargs else {}
        kwargs.setdefault("temperature", self._temperature)
        resp = client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return resp.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required for the Anthropic provider. "
                "Add anthropic to requirements.txt and rebuild."
            )
        api_key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")
        client = anthropic.Anthropic(api_key=api_key)
        kwargs = dict(self._generation_kwargs) if self._generation_kwargs else {}
        kwargs.setdefault("max_tokens", 4096)
        kwargs.setdefault("temperature", self._temperature)
        resp = client.messages.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return resp.content[0].text


class DeepEvalClient:
    """
    Evaluator using real DeepEval LLM-judge metrics.

    Single evaluation metrics:
      - FaithfulnessMetric      (does the response stay faithful to retrieved context?)
      - AnswerRelevancyMetric   (does the response address the question?)

    Conversational evaluation metrics:
      - KnowledgeRetentionMetric       (does the model remember earlier conversation?)
      - ConversationCompletenessMetric (does the conversation resolve the user's goals?)

    All metrics call a judge LLM (configured via model_config) and return scores 0-100.
    """

    def __init__(self, model_config):
        self.model_config = model_config
        self._judge: Optional[_LLMJudge] = None

    @property
    def judge(self) -> _LLMJudge:
        if self._judge is None:
            if not self.model_config.provider or not self.model_config.model_name:
                raise ValueError(
                    "Model configuration is missing provider or model_name. "
                    "Please define a model via the web interface before running evaluations."
                )
            self._judge = _LLMJudge(
                provider=self.model_config.provider,
                model_name=self.model_config.model_name,
                api_key=self.model_config.api_key,
                base_url=self.model_config.base_url,
                temperature=self.model_config.temperature,
                generation_kwargs=self.model_config.generation_kwargs,
            )
        return self._judge

    async def _run(self, metric, test_case) -> float:
        """Run a synchronous DeepEval metric in thread pool, return score 0-100."""
        loop = asyncio.get_event_loop()

        def _measure():
            metric.measure(test_case)
            return metric.score  # deepeval scores are 0.0–1.0

        raw = await loop.run_in_executor(_executor, _measure)
        return round(float(raw) * 100, 2)
    
    # ------------------------------------------------------------------ #
    #  Single evaluation
    # ------------------------------------------------------------------ #

    async def evaluate_single(
        self,
        prompt: str,
        actual_response: str,
        retrieved_contexts: List[str],
        expected_response: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a single LLM response using real DeepEval LLM-judge metrics.

        Supported weight keys:
          faithfulness, answer_relevancy,
          contextual_precision (*), contextual_recall (*),
          contextual_relevancy, hallucination, bias, toxicity

        (*) requires expected_response to be provided.
        """
        logger.info("Starting single evaluation via DeepEval LLM judge")

        if not weights:
            weights = {"faithfulness": 0.5, "answer_relevancy": 0.5}

        ctx = list(retrieved_contexts) if retrieved_contexts else []

        # Pass retrieved_contexts to BOTH retrieval_context (RAG metrics)
        # and context (HallucinationMetric) — each uses whichever it needs.
        test_case = LLMTestCase(
            input=prompt,
            actual_output=actual_response,
            retrieval_context=ctx,
            context=ctx,
            expected_output=expected_response,
        )

        result: Dict[str, Dict[str, float]] = {}

        async def _run_metric(key: str, metric) -> None:
            score = await self._run(metric, test_case)
            result[key] = {"score": score, "weight": weights[key]}
            logger.info(f"{key}: {score:.1f}")

        # ── faithfulness ──────────────────────────────────────────────────
        if weights.get("faithfulness", 0) > 0:
            logger.info("Running FaithfulnessMetric…")
            await _run_metric("faithfulness", FaithfulnessMetric(model=self.judge, threshold=0.0))

        # ── answer_relevancy ──────────────────────────────────────────────
        if weights.get("answer_relevancy", 0) > 0:
            logger.info("Running AnswerRelevancyMetric…")
            await _run_metric("answer_relevancy", AnswerRelevancyMetric(model=self.judge, threshold=0.0))

        # ── contextual_precision ──────────────────────────────────────────
        if weights.get("contextual_precision", 0) > 0:
            if not _HAS_CONTEXTUAL:
                logger.warning("contextual_precision: ContextualPrecisionMetric unavailable in this deepeval version — skipping")
            elif not expected_response:
                logger.warning("contextual_precision: skipped (expected_response not provided)")
            else:
                logger.info("Running ContextualPrecisionMetric…")
                await _run_metric("contextual_precision", ContextualPrecisionMetric(model=self.judge, threshold=0.0))

        # ── contextual_recall ─────────────────────────────────────────────
        if weights.get("contextual_recall", 0) > 0:
            if not _HAS_CONTEXTUAL:
                logger.warning("contextual_recall: ContextualRecallMetric unavailable — skipping")
            elif not expected_response:
                logger.warning("contextual_recall: skipped (expected_response not provided)")
            else:
                logger.info("Running ContextualRecallMetric…")
                await _run_metric("contextual_recall", ContextualRecallMetric(model=self.judge, threshold=0.0))

        # ── contextual_relevancy ──────────────────────────────────────────
        if weights.get("contextual_relevancy", 0) > 0:
            if not _HAS_CONTEXTUAL:
                logger.warning("contextual_relevancy: ContextualRelevancyMetric unavailable — skipping")
            else:
                logger.info("Running ContextualRelevancyMetric…")
                await _run_metric("contextual_relevancy", ContextualRelevancyMetric(model=self.judge, threshold=0.0))

        # ── hallucination ─────────────────────────────────────────────────
        if weights.get("hallucination", 0) > 0:
            if not _HAS_HALLUCINATION:
                logger.warning("hallucination: HallucinationMetric unavailable — skipping")
            else:
                logger.info("Running HallucinationMetric…")
                await _run_metric("hallucination", HallucinationMetric(model=self.judge, threshold=0.0))

        # ── bias ──────────────────────────────────────────────────────────
        if weights.get("bias", 0) > 0:
            if not _HAS_BIAS:
                logger.warning("bias: BiasMetric unavailable — skipping")
            else:
                logger.info("Running BiasMetric…")
                await _run_metric("bias", BiasMetric(model=self.judge, threshold=0.0))

        # ── toxicity ──────────────────────────────────────────────────────
        if weights.get("toxicity", 0) > 0:
            if not _HAS_TOXICITY:
                logger.warning("toxicity: ToxicityMetric unavailable — skipping")
            else:
                logger.info("Running ToxicityMetric…")
                await _run_metric("toxicity", ToxicityMetric(model=self.judge, threshold=0.0))

        return result

    # ------------------------------------------------------------------ #
    #  Conversational evaluation
    # ------------------------------------------------------------------ #

    async def evaluate_conversational(
        self,
        chat_history: List[Dict[str, str]],
        prompt: str,
        actual_response: str,
        retrieved_contexts: List[str],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a conversational LLM response using DeepEval conversational metrics.

        Supported weight keys:
          knowledge_retention, conversation_completeness, conversation_relevancy

        chat_history: list of {"role": "user"|"assistant", "content": "..."} dicts.
        """
        logger.info("Starting conversational evaluation via DeepEval LLM judge")

        if not weights:
            weights = {"knowledge_retention": 0.5, "conversation_completeness": 0.5}

        if not _HAS_CONVERSATIONAL_BASE:
            raise RuntimeError(
                "KnowledgeRetentionMetric / ConversationCompletenessMetric could not be "
                "imported from deepeval. Check your deepeval version."
            )

        # Pair up user/assistant messages from history into LLMTestCase turns
        turns: List[LLMTestCase] = []
        history = list(chat_history)
        i = 0
        while i < len(history):
            if history[i]["role"] == "user":
                q = history[i]["content"]
                a = ""
                if i + 1 < len(history) and history[i + 1]["role"] == "assistant":
                    a = history[i + 1]["content"]
                    i += 2
                else:
                    i += 1
                turns.append(LLMTestCase(input=q, actual_output=a))
            else:
                i += 1

        # Append the current (latest) turn
        turns.append(LLMTestCase(input=prompt, actual_output=actual_response))
        convo = ConversationalTestCase(turns=turns)

        result: Dict[str, Dict[str, float]] = {}

        # ── knowledge_retention ───────────────────────────────────────────
        if weights.get("knowledge_retention", 0) > 0:
            logger.info("Running KnowledgeRetentionMetric…")
            metric = KnowledgeRetentionMetric(model=self.judge, threshold=0.0)
            score = await self._run(metric, convo)
            result["knowledge_retention"] = {"score": score, "weight": weights["knowledge_retention"]}
            logger.info(f"knowledge_retention: {score:.1f}")

        # ── conversation_completeness ─────────────────────────────────────
        if weights.get("conversation_completeness", 0) > 0:
            logger.info("Running ConversationCompletenessMetric…")
            metric = ConversationCompletenessMetric(model=self.judge, threshold=0.0)
            score = await self._run(metric, convo)
            result["conversation_completeness"] = {"score": score, "weight": weights["conversation_completeness"]}
            logger.info(f"conversation_completeness: {score:.1f}")

        # ── conversation_relevancy ────────────────────────────────────────
        if weights.get("conversation_relevancy", 0) > 0:
            if not _HAS_CONV_RELEVANCY:
                logger.warning("conversation_relevancy: ConversationRelevancyMetric unavailable — skipping")
            else:
                logger.info("Running ConversationRelevancyMetric…")
                metric = ConversationRelevancyMetric(model=self.judge, threshold=0.0)
                score = await self._run(metric, convo)
                result["conversation_relevancy"] = {"score": score, "weight": weights["conversation_relevancy"]}
                logger.info(f"conversation_relevancy: {score:.1f}")

        return result

    # ------------------------------------------------------------------ #
    #  Composite score
    # ------------------------------------------------------------------ #

    async def calculate_composite_score(self, metrics: Dict[str, Dict[str, float]]) -> float:
        """
        Weighted average: Σ(score_i × weight_i) / Σ(weight_i)

        Renormalises automatically so that metrics skipped at runtime
        (e.g. contextual_precision without expected_response) don't
        deflate the final score.
        """
        if not metrics:
            return 0.0
        total_weight = sum(m["weight"] for m in metrics.values())
        if total_weight == 0:
            return 0.0
        composite = sum(m["score"] * m["weight"] for m in metrics.values()) / total_weight
        return round(min(100.0, max(0.0, composite)), 2)
