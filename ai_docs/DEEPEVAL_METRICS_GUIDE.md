# DeepEval Metrics System - Complete Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Base Metric Classes](#base-metric-classes)
3. [Test Case Structure](#test-case-structure)
4. [How Metrics Work](#how-metrics-work)
5. [Template System](#template-system)
6. [Schema System](#schema-system)
7. [Metric Examples](#metric-examples)
8. [Metric Configuration Options](#metric-configuration-options)
9. [Cost Tracking](#cost-tracking)
10. [Progress Indicators](#progress-indicators)
11. [Metric Categories](#metric-categories)
12. [Creating Custom Metrics](#creating-custom-metrics)

---

## Architecture Overview

DeepEval's metrics system is built on a three-tier architecture:

1. **Base Classes** - Define the metric interface and behavior
2. **Metric Implementations** - Specific metrics that inherit from base classes
3. **Supporting Infrastructure** - Templates, schemas, utilities, and progress indicators

---

## Base Metric Classes

DeepEval provides three base classes for different evaluation scenarios:

### BaseMetric

For single-turn LLM test cases.

- Used for most metrics (RAG, safety, quality)
- Evaluates one input → output interaction
- Required methods: `measure()`, `a_measure()`, `is_successful()`

### BaseConversationalMetric

For multi-turn conversations.

- Evaluates entire conversation flows
- Tracks context across multiple turns
- Used for conversation_completeness, knowledge_retention, role_adherence

### BaseArenaMetric

For comparing multiple LLM outputs.

- Side-by-side comparison of different models/prompts
- Returns rankings or preference scores
- Used for A/B testing and model selection

---

## Test Case Structure

All metrics evaluate `LLMTestCase` objects with these fields:

```python
from deepeval.test_case import LLMTestCase, ToolCall

test_case = LLMTestCase(
    input="User query",                    # Required
    actual_output="LLM response",          # Most metrics need this
    expected_output="Ground truth",        # For comparison metrics
    context=["doc1", "doc2"],             # For context-aware metrics
    retrieval_context=["chunk1", "chunk2"], # For RAG metrics
    tools_called=[ToolCall(...)],         # For agentic metrics
    expected_tools=[ToolCall(...)],       # For tool correctness
    mcp_servers=[MCPServer(...)],         # For MCP evaluation
    multimodal=False,                     # Auto-detected for images
    additional_metadata={...}             # Custom fields
)
```

### Key Fields

- **input**: The user's query or prompt
- **actual_output**: The LLM's actual response
- **expected_output**: The ground truth or expected response
- **context**: General context documents
- **retrieval_context**: Retrieved documents for RAG evaluation
- **tools_called**: List of tools the agent actually called
- **expected_tools**: List of tools the agent should have called
- **multimodal**: Whether the test case includes images (auto-detected)

---

## How Metrics Work

Every metric follows this evaluation pipeline:

### 1. Initialization

```python
from deepeval.metrics import AnswerRelevancyMetric

metric = AnswerRelevancyMetric(
    threshold=0.7,              # Pass/fail threshold (0-1)
    model="gpt-4",              # Evaluation LLM
    strict_mode=False,          # If True, threshold becomes 1.0
    async_mode=True,            # Use async evaluation
    verbose_mode=False,         # Show detailed logs
    include_reason=True         # Generate explanation
)
```

### 2. Measurement

The `measure()` or `a_measure()` method:

1. Validates test case has required parameters
2. Generates intermediate artifacts (statements, claims, verdicts)
3. Calculates final score (0-1 range)
4. Generates human-readable reason
5. Determines success (score >= threshold)
6. Logs to Confident AI (if enabled)

### 3. LLM-Based Evaluation Pattern

Most metrics use a multi-step LLM evaluation:

```python
# Step 1: Extract structured information
statements = _generate_statements(actual_output)
# Uses template to create prompt
# Uses schema to parse LLM response into Pydantic model

# Step 2: Generate verdicts
verdicts = _generate_verdicts(input, statements)
# LLM judges each statement

# Step 3: Calculate score
score = _calculate_score()
# Aggregate verdicts into 0-1 score

# Step 4: Generate reason
reason = _generate_reason(score, verdicts)
# LLM explains the score
```

---

## Template System

Each metric has a `Template` class that generates prompts for the evaluation LLM.

### Example: AnswerRelevancyTemplate

```python
class AnswerRelevancyTemplate:
    @staticmethod
    def generate_statements(actual_output: str, multimodal: bool):
        return f"""Given the text, breakdown and generate a list of statements...
        
        Text: {actual_output}
        JSON:
        """
```

### Template Features

- **Few-shot examples** to guide LLM behavior
- **Multimodal rules** when images are present
- **JSON output format** enforcement
- **Clear instructions** for structured extraction

---

## Schema System

Each metric has Pydantic schemas for parsing LLM responses.

### Example: Answer Relevancy Schemas

```python
from pydantic import BaseModel
from typing import List, Optional, Literal

class AnswerRelevancyVerdict(BaseModel):
    verdict: Literal["yes", "no", "idk"]
    reason: Optional[str] = None

class Verdicts(BaseModel):
    verdicts: List[AnswerRelevancyVerdict]
```

### Schema Utilities

The `generate_with_schema_and_extract()` utility:

1. Sends prompt to LLM
2. Parses JSON response
3. Validates against Pydantic schema
4. Extracts specific fields
5. Handles errors gracefully

---

## Metric Examples

### 1. Answer Relevancy Metric

**Purpose**: Measures if the LLM's answer is relevant to the user's question

**Required params**: `input`, `actual_output`

**How it works**:

1. Break down `actual_output` into individual statements
2. For each statement, judge if it's relevant to `input` (yes/no/idk)
3. Score = (relevant statements) / (total statements)
4. Generate reason explaining irrelevant statements

**Usage**:

```python
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

metric = AnswerRelevancyMetric(threshold=0.7)
test_case = LLMTestCase(
    input="What is the capital of France?",
    actual_output="Paris is the capital of France. It's also known for the Eiffel Tower."
)
score = metric.measure(test_case)
# score ≈ 1.0 (both statements relevant)
# metric.reason: "The score is 1.0 because all statements directly address the question."
```

---

### 2. Hallucination Metric

**Purpose**: Detects when LLM makes claims not supported by provided context

**Required params**: `input`, `actual_output`, `context`

**How it works**:

1. Extract claims from `actual_output`
2. For each claim, check if it's supported by `context` (yes/no)
3. Score = (unsupported claims) / (total claims)
4. Lower score is better (0 = no hallucinations)

**Usage**:

```python
from deepeval.metrics import HallucinationMetric

metric = HallucinationMetric(threshold=0.3)  # Allow up to 30% hallucination
test_case = LLMTestCase(
    input="Tell me about the company",
    actual_output="The company was founded in 2020 and has 500 employees.",
    context=["The company was founded in 2020."]  # No mention of employee count
)
score = metric.measure(test_case)
# score ≈ 0.5 (50% hallucination - employee count not in context)
# metric.success = False (exceeds threshold)
```

---

### 3. Faithfulness Metric

**Purpose**: Ensures LLM output is faithful to retrieval context (for RAG systems)

**Required params**: `input`, `actual_output`, `retrieval_context`

**How it works**:

1. Extract "truths" from `retrieval_context` (factual statements)
2. Extract "claims" from `actual_output`
3. For each claim, verify if supported by truths (yes/no/idk)
4. Score = (supported claims) / (total claims)

**Special features**:

- `truths_extraction_limit`: Limit number of truths extracted (performance optimization)
- `penalize_ambiguous_claims`: Penalize "idk" verdicts

**Usage**:

```python
from deepeval.metrics import FaithfulnessMetric

metric = FaithfulnessMetric(
    threshold=0.8,
    truths_extraction_limit=10  # Only extract top 10 truths
)
test_case = LLMTestCase(
    input="What are the product features?",
    actual_output="The product has 256GB storage and wireless charging.",
    retrieval_context=[
        "Product specs: 256GB SSD, USB-C charging",
        "Available in black and silver colors"
    ]
)
score = metric.measure(test_case)
# score ≈ 0.5 (storage correct, wireless charging contradicts context)
```

---

### 4. G-Eval (Custom Metric Framework)

**Purpose**: Create custom metrics with your own evaluation criteria

**Required params**: Configurable via `evaluation_params`

**How it works**:

1. Define custom criteria (what to evaluate)
2. Optionally provide evaluation steps (how to evaluate)
3. Optionally provide rubric (scoring guide)
4. LLM evaluates based on your criteria
5. Uses log probabilities for more reliable scoring (when available)

**Basic Usage**:

```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

# Define custom "Helpfulness" metric
helpfulness_metric = GEval(
    name="Helpfulness",
    criteria="Determine if the response is helpful and actionable",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT
    ],
    evaluation_steps=[
        "Check if the response directly addresses the user's question",
        "Verify the response provides actionable information",
        "Assess if the tone is friendly and supportive"
    ],
    threshold=0.7
)

test_case = LLMTestCase(
    input="How do I reset my password?",
    actual_output="Click 'Forgot Password' on the login page and follow the email instructions."
)
score = helpfulness_metric.measure(test_case)
```

**With Rubric** (for more precise scoring):

```python
from deepeval.metrics.g_eval.utils import Rubric

coherence_metric = GEval(
    name="Coherence",
    criteria="Evaluate the logical flow and coherence of the response",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
    rubric=[
        Rubric(score=1, description="Incoherent, contradictory statements"),
        Rubric(score=2, description="Some logical flow but disjointed"),
        Rubric(score=3, description="Mostly coherent with minor issues"),
        Rubric(score=4, description="Clear logical flow throughout"),
        Rubric(score=5, description="Perfectly coherent and well-structured")
    ],
    threshold=0.6
)
```

---

## Metric Configuration Options

All metrics support these common parameters:

### threshold (float, default=0.5)

- Pass/fail threshold for the metric
- Score >= threshold → success = True
- Range: 0.0 to 1.0

### model (str or DeepEvalBaseLLM, default=None)

- LLM used for evaluation
- Accepts: "gpt-4", "gpt-3.5-turbo", "claude-3-opus", custom models
- If None, uses default from config

### strict_mode (bool, default=False)

- When True, threshold becomes 1.0 (perfect score required)
- For hallucination: threshold becomes 0.0 (zero tolerance)

### async_mode (bool, default=True)

- Use async evaluation for better performance
- Automatically manages event loop

### verbose_mode (bool, default=False)

- Show detailed evaluation steps
- Access via `metric.verbose_logs` after measurement

### include_reason (bool, default=True)

- Generate human-readable explanation
- Access via `metric.reason` after measurement

---

## Cost Tracking

Metrics automatically track evaluation costs:

```python
metric = AnswerRelevancyMetric(model="gpt-4")
score = metric.measure(test_case)

print(f"Evaluation cost: ${metric.evaluation_cost}")
print(f"Evaluation model: {metric.evaluation_model}")
```

**Cost tracking notes**:

- Only works with native DeepEval models (OpenAI, Anthropic, etc.)
- Returns None for custom models
- Accumulates across multiple LLM calls within one evaluation

---

## Progress Indicators

Metrics show progress during evaluation:

```python
from deepeval.metrics.indicator import metric_progress_indicator

with metric_progress_indicator(metric, _show_indicator=True):
    # Shows: "Evaluating Answer Relevancy... ✓"
    score = metric.measure(test_case)
```

Controlled by `_show_indicator` parameter (internal use).

---

## Metric Categories

### RAG Metrics (for retrieval-augmented generation)

- **AnswerRelevancyMetric** - Is answer relevant to question?
- **FaithfulnessMetric** - Is answer faithful to retrieved context?
- **ContextualPrecisionMetric** - Are relevant contexts ranked higher?
- **ContextualRecallMetric** - Are all relevant contexts retrieved?
- **ContextualRelevancyMetric** - Are retrieved contexts relevant?

### Safety Metrics

- **HallucinationMetric** - Does LLM make unsupported claims?
- **BiasMetric** - Does output contain biased language?
- **ToxicityMetric** - Does output contain toxic content?
- **PIILeakageMetric** - Does output leak personal information?

### Agentic Metrics (for AI agents)

- **ToolCorrectnessMetric** - Did agent use correct tools?
- **TaskCompletionMetric** - Did agent complete the task?
- **PlanAdherenceMetric** - Did agent follow the plan?
- **StepEfficiencyMetric** - Was agent efficient in steps?

### Conversational Metrics

- **KnowledgeRetentionMetric** - Does agent remember context?
- **ConversationCompletenessMetric** - Is conversation complete?
- **RoleAdherenceMetric** - Does agent stay in character?

### Custom Metrics

- **GEval** - Define your own evaluation criteria
- **DAGMetric** - Directed acyclic graph evaluation

---

## Creating Custom Metrics

You can create custom metrics by inheriting from `BaseMetric`:

```python
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class MyCustomMetric(BaseMetric):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
    
    def measure(self, test_case: LLMTestCase) -> float:
        # Your evaluation logic
        self.score = self._calculate_my_score(test_case)
        self.success = self.score >= self.threshold
        self.reason = "Custom evaluation reason"
        return self.score
    
    async def a_measure(self, test_case: LLMTestCase) -> float:
        # Async version
        return self.measure(test_case)
    
    def is_successful(self) -> bool:
        return self.success
    
    @property
    def __name__(self):
        return "My Custom Metric"
    
    def _calculate_my_score(self, test_case: LLMTestCase) -> float:
        # Implement your scoring logic here
        # Return a float between 0.0 and 1.0
        pass
```

### Custom Metric Best Practices

1. **Always set `self.score`** - The final score (0.0 to 1.0)
2. **Always set `self.success`** - Boolean pass/fail result
3. **Optionally set `self.reason`** - Human-readable explanation
4. **Implement both sync and async** - `measure()` and `a_measure()`
5. **Validate test case params** - Use `check_llm_test_case_params()`
6. **Track evaluation cost** - Set `self.evaluation_cost` if using LLMs

---

## Summary

DeepEval's metrics system provides:

- **Flexibility**: Custom metrics via GEval or BaseMetric inheritance
- **Comprehensiveness**: 40+ built-in metrics covering RAG, safety, agentic, and conversational use cases
- **Production-ready**: Async evaluation, cost tracking, progress indicators
- **LLM-as-judge**: Uses LLMs to evaluate LLM outputs with structured prompts and schemas
- **Multimodal support**: Automatic detection and handling of images in test cases
- **Integration**: Works seamlessly with pytest and Confident AI platform

The system is designed to make LLM evaluation rigorous, scalable, and maintainable.
