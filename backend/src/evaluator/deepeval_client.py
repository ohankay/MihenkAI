"""DeepEval integration — real LLM judge metrics."""
import logging
import asyncio
import os
from typing import Dict, List, Optional

# Metrics where deepeval returns higher = more problematic (worse).
# Their effective contribution to the composite is (100 - score):
# a clean output (score ≈ 0) contributes ~100 (max positive),
# a toxic/hallucinated output (score ≈ 100) contributes ~0 (max penalty).
NEGATIVE_METRICS: frozenset = frozenset({"hallucination", "bias", "toxicity"})
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
    from deepeval.metrics import KnowledgeRetentionMetric
    _HAS_KNOWLEDGE_RETENTION = True
except ImportError:
    KnowledgeRetentionMetric = None
    _HAS_KNOWLEDGE_RETENTION = False

# ConversationCompletenessMetric / ConversationRelevancyMetric were added in
# deepeval >=1.x — not available in 0.21.x.
# We emulate them with GEval (available in 0.21.x).
try:
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCaseParams
    _HAS_GEVAL = True
except ImportError:
    GEval = None
    LLMTestCaseParams = None
    _HAS_GEVAL = False

try:
    from deepeval.metrics import ConversationCompletenessMetric
    _HAS_CONV_COMPLETENESS = True
except ImportError:
    ConversationCompletenessMetric = None
    _HAS_CONV_COMPLETENESS = False

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

    # Known provider base URLs — used when user does not supply a base_url explicitly
    _PROVIDER_BASE_URLS: Dict[str, str] = {
        "grok": "https://api.x.ai/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    }

    def _call_openai_compat(self, prompt: str) -> str:
        """
        OpenAI and OpenAI-compatible providers (Ollama, vLLM, Grok, DeepSeek, Gemini).
        For Ollama:  base_url="http://host.docker.internal:11434/v1", api_key="ollama"
        For vLLM:   base_url="http://host.docker.internal:8080/v1"
        For Grok:   base_url auto-set to https://api.x.ai/v1
        For DeepSeek: base_url auto-set to https://api.deepseek.com/v1
        """
        from openai import OpenAI

        # OpenAI SDK requires a non-None api_key; use env var or a placeholder
        # so that providers which don't validate keys (Ollama, local) still work.
        api_key = self._api_key or os.environ.get("OPENAI_API_KEY") or "not-required"
        # Use explicit base_url if set; otherwise fall back to known provider defaults
        base_url = self._base_url or self._PROVIDER_BASE_URLS.get(self._provider)
        client = OpenAI(api_key=api_key, base_url=base_url)
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
        expected_response: str,  # always required — enforced at API schema level
        weights: Optional[Dict[str, float]] = None,
        negative_thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a single LLM response using real DeepEval LLM-judge metrics.

        Positive metric keys (contribute to composite via weights):
          faithfulness, answer_relevancy,
          contextual_precision, contextual_recall, contextual_relevancy

        Negative/penalty metric keys (tracked via threshold, NOT weight):
          hallucination, bias, toxicity
          — if any score >= its threshold the composite is zeroed.
        """
        logger.info("Starting single evaluation via DeepEval LLM judge")

        if not weights:
            weights = {"faithfulness": 0.5, "answer_relevancy": 0.5}
        if negative_thresholds is None:
            negative_thresholds = {}

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
            """Run a positive metric and store score + weight."""
            score = await self._run(metric, test_case)
            result[key] = {"score": score, "weight": weights[key]}
            logger.info(f"{key}: {score:.1f}")

        async def _run_negative(key: str, metric) -> None:
            """Run a penalty metric and store score + threshold (no weight)."""
            threshold = negative_thresholds[key]
            score = await self._run(metric, test_case)
            result[key] = {"score": score, "threshold": threshold, "negative": True}
            logger.info(f"{key}: {score:.1f} (threshold: {threshold:.1f})")

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
            else:
                logger.info("Running ContextualPrecisionMetric…")
                await _run_metric("contextual_precision", ContextualPrecisionMetric(model=self.judge, threshold=0.0))

        # ── contextual_recall ─────────────────────────────────────────────
        if weights.get("contextual_recall", 0) > 0:
            if not _HAS_CONTEXTUAL:
                logger.warning("contextual_recall: ContextualRecallMetric unavailable — skipping")
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

        # ── hallucination (penalty metric) ───────────────────────────────
        if negative_thresholds.get("hallucination", 0) > 0:
            if not _HAS_HALLUCINATION:
                logger.warning("hallucination: HallucinationMetric unavailable — skipping")
            else:
                logger.info("Running HallucinationMetric (penalty)…")
                await _run_negative("hallucination", HallucinationMetric(model=self.judge, threshold=0.0))

        # ── bias (penalty metric) ─────────────────────────────────────────
        if negative_thresholds.get("bias", 0) > 0:
            if not _HAS_BIAS:
                logger.warning("bias: BiasMetric unavailable — skipping")
            else:
                logger.info("Running BiasMetric (penalty)…")
                await _run_negative("bias", BiasMetric(model=self.judge, threshold=0.0))

        # ── toxicity (penalty metric) ─────────────────────────────────────
        if negative_thresholds.get("toxicity", 0) > 0:
            if not _HAS_TOXICITY:
                logger.warning("toxicity: ToxicityMetric unavailable — skipping")
            else:
                logger.info("Running ToxicityMetric (penalty)…")
                await _run_negative("toxicity", ToxicityMetric(model=self.judge, threshold=0.0))

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
        scenario: Optional[str] = None,
        expected_outcome: Optional[str] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate a conversational LLM response using DeepEval conversational metrics.

        Supported weight keys:
          knowledge_retention, conversation_completeness, conversation_relevancy

        scenario: optional description of the chatbot's role/purpose.
        expected_outcome: optional description of what the conversation should accomplish.
        Both are used to enrich the ConversationCompleteness evaluation criteria.
        chat_history: list of {"role": "user"|"assistant", "content": "..."} dicts.
        """
        logger.info("Starting conversational evaluation via DeepEval LLM judge")

        # Use provided weights; only fall back if truly nothing passed
        if not weights:
            logger.warning("No conversational weights provided — falling back to knowledge_retention only")
            weights = {"knowledge_retention": 1.0}

        if not _HAS_KNOWLEDGE_RETENTION:
            raise RuntimeError(
                "KnowledgeRetentionMetric could not be imported from deepeval. "
                "Check your deepeval version."
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

        # Dynamic window_size: 2× the number of user-assistant turn pairs.
        # This mirrors deepeval's ConversationRelevancyMetric expectation:
        # each evaluation window spans 2× the conversation depth, ensuring
        # the full context is considered regardless of conversation length.
        window_size = max(2, 2 * len(turns))
        logger.info(f"Conversational eval: {len(turns)} turn(s), window_size={window_size}")

        # Build ConversationalTestCase using messages= (deepeval 0.21.x API)
        convo = ConversationalTestCase(messages=turns)

        # Build a flat conversation transcript for GEval-based metrics
        all_turns = list(chat_history) + [{"role": "user", "content": prompt}, {"role": "assistant", "content": actual_response}]
        conversation_transcript = "\n".join(
            f"{t['role'].upper()}: {t['content']}" for t in all_turns
        )

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
            if _HAS_CONV_COMPLETENESS:
                logger.info("Running ConversationCompletenessMetric…")
                metric = ConversationCompletenessMetric(model=self.judge, threshold=0.0)
                score = await self._run(metric, convo)
            elif _HAS_GEVAL:
                logger.info("Running conversation_completeness via GEval…")
                tc = LLMTestCase(
                    input=conversation_transcript,
                    actual_output=actual_response,
                )
                # Build rich criteria incorporating scenario + expected_outcome when provided
                criteria_parts = [
                    "Evaluate whether the AI assistant has fully addressed all of the user's "
                    "goals, questions, and requests throughout the entire conversation.",
                ]
                if scenario:
                    criteria_parts.append(f"Chatbot scenario / role: {scenario}")
                if expected_outcome:
                    criteria_parts.append(
                        f"Expected outcome of the conversation: {expected_outcome}. "
                        "Judge whether this expected outcome was achieved."
                    )
                criteria_parts.append(
                    "Score 1.0 if every user intent and the expected outcome are fully satisfied, "
                    "0.0 if none are addressed."
                )
                metric = GEval(
                    name="ConversationCompleteness",
                    criteria=" ".join(criteria_parts),
                    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
                    model=self.judge,
                    threshold=0.0,
                )
                score = await self._run(metric, tc)
            else:
                logger.warning("conversation_completeness: neither native metric nor GEval available — skipping")
                score = None
            if score is not None:
                result["conversation_completeness"] = {"score": score, "weight": weights["conversation_completeness"]}
                logger.info(f"conversation_completeness: {score:.1f}")

        # ── conversation_relevancy ────────────────────────────────────────
        if weights.get("conversation_relevancy", 0) > 0:
            if _HAS_CONV_RELEVANCY:
                # Pass dynamic window_size so the metric evaluates windows of
                # 2× the actual turn count — equivalent to the full conversation.
                logger.info(f"Running ConversationRelevancyMetric (window_size={window_size})…")
                metric = ConversationRelevancyMetric(
                    model=self.judge,
                    threshold=0.0,
                    window_size=window_size,
                )
                score = await self._run(metric, convo)
            elif _HAS_GEVAL:
                # GEval fallback: replicate deepeval's sliding-window evaluation.
                # Build windows of `window_size` individual messages, score each,
                # then average — consistent with how ConversationRelevancyMetric works.
                flat_messages = all_turns  # each dict: {role, content}
                # Convert each raw message to a labelled line
                msg_lines = [f"{m['role'].upper()}: {m['content']}" for m in flat_messages]
                n_msgs = len(msg_lines)
                # Each window covers `window_size` consecutive messages
                window_scores: List[float] = []
                for start in range(0, n_msgs, window_size):
                    window_lines = msg_lines[start: start + window_size]
                    window_text = "\n".join(window_lines)
                    # Last assistant message in this window is the "actual output"
                    last_assistant = next(
                        (flat_messages[start + j]["content"]
                         for j in range(min(window_size, n_msgs - start) - 1, -1, -1)
                         if flat_messages[start + j]["role"] == "assistant"),
                        actual_response,
                    )
                    tc_window = LLMTestCase(
                        input=window_text,
                        actual_output=last_assistant,
                    )
                    geval_window = GEval(
                        name="ConversationRelevancy",
                        criteria=(
                            "Evaluate whether each AI assistant response in the given conversation "
                            "window is directly relevant and on-topic to the user's preceding message. "
                            "Score 1.0 if all responses are fully relevant, 0.0 if responses are off-topic."
                        ),
                        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
                        model=self.judge,
                        threshold=0.0,
                    )
                    window_score = await self._run(geval_window, tc_window)
                    if window_score is not None:
                        window_scores.append(window_score)
                        logger.info(
                            f"conversation_relevancy window [{start}:{start+window_size}]: {window_score:.3f}"
                        )
                score = float(sum(window_scores) / len(window_scores)) if window_scores else None
                logger.info(f"Running conversation_relevancy via GEval (window_size={window_size}, windows={len(window_scores)})…")
            else:
                logger.warning("conversation_relevancy: neither native metric nor GEval available — skipping")
                score = None
            if score is not None:
                result["conversation_relevancy"] = {"score": score, "weight": weights["conversation_relevancy"]}
                logger.info(f"conversation_relevancy: {score:.3f}")

        return result

    # ------------------------------------------------------------------ #
    #  Composite score
    # ------------------------------------------------------------------ #

    async def calculate_composite_score(self, metrics: Dict[str, Dict[str, float]]) -> float:
        """
        Composite score calculation with penalty (threshold) logic.

        Positive metrics:  contribute via weighted average (higher = better).
        Negative/penalty metrics (marked with ``negative: True``):
          — if any score >= its configured threshold the composite is zeroed.
          — if threshold is 0 or the metric was not executed, it is ignored.

        Returns 0.0–100.0.
        """
        if not metrics:
            return 0.0

        pos_metrics = {k: v for k, v in metrics.items() if not v.get("negative")}
        neg_metrics = {k: v for k, v in metrics.items() if v.get("negative")}

        # ── Penalty check ──────────────────────────────────────────
        penalty_triggered = False
        for key, m in neg_metrics.items():
            threshold = m.get("threshold", 0.0)
            score = m.get("score", 0.0)
            if threshold > 0 and score >= threshold:
                m["exceeded"] = True  # mark for frontend display
                penalty_triggered = True
                logger.warning(
                    f"Penalty triggered: {key} score={score:.1f} >= threshold={threshold:.1f}"
                )
            else:
                m["exceeded"] = False

        if penalty_triggered:
            logger.warning("Composite score zeroed due to penalty threshold breach.")
            return 0.0

        # ── Weighted avg of positive metrics ────────────────────────
        total_weight = sum(m["weight"] for m in pos_metrics.values())
        if total_weight == 0:
            return 0.0
        composite = sum(m["score"] * m["weight"] for m in pos_metrics.values()) / total_weight
        return round(min(100.0, max(0.0, composite)), 2)
