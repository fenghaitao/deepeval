# DeepEval Scorer Module - Complete Guide

## Table of Contents

1. [Overview](#overview)
2. [Purpose and Use Cases](#purpose-and-use-cases)
3. [Traditional NLP Metrics](#traditional-nlp-metrics)
4. [Neural Model-Based Metrics](#neural-model-based-metrics)
5. [Specialized Metrics](#specialized-metrics)
6. [Usage in Custom Metrics](#usage-in-custom-metrics)
7. [Usage in Benchmarks](#usage-in-benchmarks)
8. [Complete API Reference](#complete-api-reference)
9. [Installation Requirements](#installation-requirements)
10. [Best Practices](#best-practices)

---

## Overview

The `Scorer` module provides a collection of **traditional NLP evaluation metrics** and **neural model-based scoring methods** that can be used for evaluating LLM outputs without requiring LLM-as-judge approaches.

Unlike DeepEval's main metrics system (which uses LLMs to evaluate LLM outputs), the Scorer module provides:

- **Deterministic scoring** - Same inputs always produce same scores
- **Fast evaluation** - No LLM API calls required
- **Traditional metrics** - ROUGE, BLEU, exact match, etc.
- **Neural metrics** - BERTScore, toxicity detection, bias detection
- **Lower cost** - No API costs for evaluation

---

## Purpose and Use Cases

### When to Use Scorer

**Use Scorer when you need**:
- Fast, deterministic evaluation without LLM calls
- Traditional NLP metrics (ROUGE, BLEU)
- Neural model-based evaluation (BERTScore, toxicity)
- Benchmark evaluation (SQuAD, MMLU, etc.)
- Custom metrics with non-LLM scoring

**Use LLM-based metrics when you need**:
- Semantic understanding and reasoning
- Complex evaluation criteria
- Contextual relevance assessment
- Nuanced quality judgments

### Common Use Cases

1. **Building custom metrics** - Combine traditional scores with custom logic
2. **Benchmark evaluation** - Score benchmark tasks (SQuAD, MMLU, etc.)
3. **Quick validation** - Fast checks without API costs
4. **Baseline metrics** - Compare against traditional NLP metrics
5. **Safety checks** - Toxicity and bias detection

---

## Traditional NLP Metrics

### 1. ROUGE Score

**Purpose**: Evaluate text summarization quality by comparing n-gram overlap.

**Method**: `rouge_score(target, prediction, score_type)`

**Parameters**:
- `target` (str): Reference/ground truth text
- `prediction` (str): Generated text to evaluate
- `score_type` (str): Type of ROUGE score
  - `"rouge1"`: Unigram overlap
  - `"rouge2"`: Bigram overlap
  - `"rougeL"`: Longest common subsequence

**Returns**: `float` - F-measure score (0.0 to 1.0)

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

target = "The cat sat on the mat."
prediction = "A cat was sitting on a mat."

# ROUGE-1 (unigram overlap)
score = scorer.rouge_score(target, prediction, "rouge1")
print(f"ROUGE-1: {score}")  # ~0.67

# ROUGE-2 (bigram overlap)
score = scorer.rouge_score(target, prediction, "rouge2")
print(f"ROUGE-2: {score}")  # ~0.40

# ROUGE-L (longest common subsequence)
score = scorer.rouge_score(target, prediction, "rougeL")
print(f"ROUGE-L: {score}")  # ~0.67
```

**Installation**: `pip install rouge-score`

---

### 2. BLEU Score

**Purpose**: Evaluate machine translation quality using n-gram precision.

**Method**: `sentence_bleu_score(references, prediction, bleu_type)`

**Parameters**:
- `references` (str or List[str]): One or more reference translations
- `prediction` (str): Generated translation to evaluate
- `bleu_type` (str): Type of BLEU score
  - `"bleu1"`: Unigram precision
  - `"bleu2"`: Bigram precision
  - `"bleu3"`: Trigram precision
  - `"bleu4"`: 4-gram precision

**Returns**: `float` - BLEU score (0.0 to 1.0)

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Single reference
reference = "The cat is on the mat"
prediction = "The cat sits on the mat"

score = scorer.sentence_bleu_score(reference, prediction, "bleu1")
print(f"BLEU-1: {score}")  # ~0.83

# Multiple references
references = [
    "The cat is on the mat",
    "A cat sits on a mat",
    "There is a cat on the mat"
]
prediction = "The cat sits on the mat"

score = scorer.sentence_bleu_score(references, prediction, "bleu2")
print(f"BLEU-2: {score}")  # Higher score with multiple references
```

**Installation**: `pip install nltk`

---

### 3. Exact Match Score

**Purpose**: Check if prediction exactly matches target (strict comparison).

**Method**: `exact_match_score(target, prediction)`

**Parameters**:
- `target` (str): Expected output
- `prediction` (str): Generated output

**Returns**: `int` - 1 if exact match, 0 otherwise

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Exact match
score = scorer.exact_match_score("Paris", "Paris")
print(score)  # 1

# Not exact match (case sensitive)
score = scorer.exact_match_score("Paris", "paris")
print(score)  # 0

# Not exact match (whitespace matters)
score = scorer.exact_match_score("Paris", " Paris ")
print(score)  # 0 (strips whitespace, so this would be 1)
```

---

### 4. Quasi Exact Match Score

**Purpose**: Check if prediction matches target after normalization (case-insensitive, punctuation removed).

**Method**: `quasi_exact_match_score(target, prediction)`

**Parameters**:
- `target` (str): Expected output
- `prediction` (str): Generated output

**Returns**: `int` - 1 if normalized match, 0 otherwise

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Matches after normalization
score = scorer.quasi_exact_match_score("Paris", "paris")
print(score)  # 1

score = scorer.quasi_exact_match_score("Hello, World!", "hello world")
print(score)  # 1

# Still doesn't match
score = scorer.quasi_exact_match_score("Paris", "London")
print(score)  # 0
```

---

### 5. Quasi Contains Score

**Purpose**: Check if normalized prediction is in list of normalized targets.

**Method**: `quasi_contains_score(targets, prediction)`

**Parameters**:
- `targets` (List[str]): List of acceptable answers
- `prediction` (str): Generated output

**Returns**: `int` - 1 if prediction in targets (after normalization), 0 otherwise

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

targets = ["Paris", "paris", "PARIS"]
prediction = "paris"

score = scorer.quasi_contains_score(targets, prediction)
print(score)  # 1

targets = ["London", "Berlin", "Madrid"]
prediction = "Paris"

score = scorer.quasi_contains_score(targets, prediction)
print(score)  # 0
```

---

## Neural Model-Based Metrics

### 1. BERTScore

**Purpose**: Evaluate semantic similarity using BERT embeddings.

**Method**: `bert_score(references, predictions, model, lang)`

**Parameters**:
- `references` (str or List[str]): Reference text(s)
- `predictions` (str or List[str]): Generated text(s)
- `model` (str, optional): BERT model name (default: "microsoft/deberta-large-mnli")
- `lang` (str, optional): Language code (default: "en")

**Returns**: `dict` with keys:
- `"bert-precision"`: List of precision scores
- `"bert-recall"`: List of recall scores
- `"bert-f1"`: List of F1 scores

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

reference = "The cat sat on the mat"
prediction = "A feline was resting on a rug"

scores = scorer.bert_score(reference, prediction)
print(f"Precision: {scores['bert-precision']}")
print(f"Recall: {scores['bert-recall']}")
print(f"F1: {scores['bert-f1']}")

# Batch scoring
references = ["The cat sat on the mat", "The dog ran in the park"]
predictions = ["A cat was on a mat", "A dog played in a park"]

scores = scorer.bert_score(references, predictions)
# Returns lists of scores for each pair
```

**Installation**: `pip install bert-score torch`

**Notes**:
- BERTScore captures semantic similarity better than n-gram metrics
- Slower than traditional metrics but faster than LLM-based evaluation
- Requires GPU for best performance

---

### 2. Toxicity Score

**Purpose**: Detect toxic, offensive, or harmful content using Detoxify model.

**Method**: `neural_toxic_score(prediction, model)`

**Parameters**:
- `prediction` (str): Text to evaluate for toxicity
- `model` (str, optional): Detoxify model variant
  - `"original"`: Original model (default)
  - `"unbiased"`: Unbiased variant
  - `"multilingual"`: Multilingual support

**Returns**: `dict` with toxicity scores:
- **Original model**: `toxicity`, `severe_toxicity`, `obscene`, `threat`, `insult`, `identity_attack`
- **Unbiased model**: Same as original + `sexual_explicit`
- **Multilingual model**: Same as unbiased

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Clean text
text = "This is a nice day!"
scores = scorer.neural_toxic_score(text)
print(scores)
# {'toxicity': 0.001, 'severe_toxicity': 0.0001, ...}

# Toxic text
text = "You are stupid and worthless!"
scores = scorer.neural_toxic_score(text, model="unbiased")
print(scores)
# {'toxicity': 0.95, 'insult': 0.98, ...}

# Get mean toxicity
mean_toxicity = sum(scores.values()) / len(scores)
```

**Installation**: `pip install detoxify`

---

### 3. Bias Score

**Purpose**: Detect biased language using UnBiased model.

**Method**: `neural_bias_score(text, model)`

**Parameters**:
- `text` (str): Text to evaluate for bias
- `model` (str, optional): Model name (default: None uses default model)

**Returns**: `float` - Bias score (0.0 to 1.0, higher = more biased)

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Neutral text
text = "The engineer completed the project on time."
score = scorer.neural_bias_score(text)
print(f"Bias score: {score}")  # Low score

# Potentially biased text
text = "The female engineer surprisingly completed the project."
score = scorer.neural_bias_score(text)
print(f"Bias score: {score}")  # Higher score
```

**Installation**: Requires specific bias detection model

---

### 4. Answer Relevancy Score

**Purpose**: Measure semantic similarity between prediction and target using sentence transformers.

**Method**: `answer_relevancy_score(predictions, target, model_type, model_name)`

**Parameters**:
- `predictions` (str or List[str]): Generated answer(s)
- `target` (str): Reference answer or query
- `model_type` (str, optional): Encoder type
  - `"cross_encoder"`: Cross-encoder model (default)
  - `"self_encoder"`: Bi-encoder model
- `model_name` (str, optional): Specific model name

**Returns**: `float` - Relevancy score (0.0 to 1.0)

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Cross-encoder (single prediction)
target = "What is the capital of France?"
prediction = "The capital of France is Paris."

score = scorer.answer_relevancy_score(
    prediction, 
    target, 
    model_type="cross_encoder"
)
print(f"Relevancy: {score}")

# Self-encoder (multiple predictions)
predictions = [
    "Paris is the capital of France.",
    "The capital is Paris.",
    "London is the capital of England."
]

score = scorer.answer_relevancy_score(
    predictions, 
    target, 
    model_type="self_encoder"
)
print(f"Relevancy: {score}")
```

**Installation**: `pip install sentence-transformers`

---

## Specialized Metrics

### 1. Faithfulness Score

**Purpose**: Measure if generated text is faithful to source using SummaCZS model.

**Method**: `faithfulness_score(target, prediction, model, granularity, device)`

**Parameters**:
- `target` (str): Source/reference text
- `prediction` (str): Generated text to verify
- `model` (str, optional): SummaCZS model variant
- `granularity` (str, optional): Scoring granularity
- `device` (str, optional): Device for computation ("cpu", "cuda")

**Returns**: `float` - Faithfulness score (0.0 to 1.0)

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

source = "The company reported revenue of $100M in Q1 2024."
prediction = "The company made $100M in the first quarter of 2024."

score = scorer.faithfulness_score(source, prediction)
print(f"Faithfulness: {score}")  # High score (faithful)

prediction = "The company made $200M in Q1 2024."
score = scorer.faithfulness_score(source, prediction)
print(f"Faithfulness: {score}")  # Low score (unfaithful)
```

---

### 2. Hallucination Score

**Purpose**: Detect hallucinations using Vectara Hallucination Evaluation Model.

**Method**: `hallucination_score(source, prediction, model)`

**Parameters**:
- `source` (str): Source document
- `prediction` (str): Generated summary/text
- `model` (str, optional): Model name

**Returns**: `float` - Hallucination score (lower = more hallucination)

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

source = "The meeting is scheduled for 3 PM on Monday."
prediction = "The meeting is at 3 PM on Monday."

score = scorer.hallucination_score(source, prediction)
print(f"Hallucination: {score}")  # High score (no hallucination)

prediction = "The meeting is at 5 PM on Tuesday."
score = scorer.hallucination_score(source, prediction)
print(f"Hallucination: {score}")  # Low score (hallucination detected)
```

---

### 3. Truth Identification Score

**Purpose**: Calculate percentage of correct answers identified from a list.

**Method**: `truth_identification_score(target, prediction)`

**Parameters**:
- `target` (str): String representing list of correct answers (e.g., "1,2,3")
- `prediction` (str): String representing predicted answers (e.g., "1,3,5")

**Returns**: `int` - Percentage of correct answers (0 to 100)

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Target: correct answers are 1, 2, 3
target = "1,2,3"

# Prediction: guessed 1, 2, 4
prediction = "1,2,4"

score = scorer.truth_identification_score(target, prediction)
print(f"Accuracy: {score}%")  # 67% (2 out of 3 correct)

# Perfect score
prediction = "1,2,3"
score = scorer.truth_identification_score(target, prediction)
print(f"Accuracy: {score}%")  # 100%
```

---

### 4. SQuAD Score

**Purpose**: Evaluate question-answering using LLM to judge correctness.

**Method**: `squad_score(input, prediction, expected_output, evaluation_model, using_native_evaluation_model)`

**Parameters**:
- `input` (str): Question and context
- `prediction` (str): Model's answer
- `expected_output` (str): Correct answer
- `evaluation_model` (DeepEvalBaseLLM): LLM for evaluation
- `using_native_evaluation_model` (bool): Whether using native model

**Returns**: `int` - 1 if correct, 0 if incorrect

**Example**:
```python
from deepeval.scorer import Scorer
from deepeval.models import GPTModel

scorer = Scorer()
eval_model = GPTModel(model="gpt-4")

input = "Context: Paris is the capital of France.\nQuestion: What is the capital of France?"
prediction = "Paris"
expected = "Paris"

score = scorer.squad_score(
    input, 
    prediction, 
    expected, 
    eval_model, 
    using_native_evaluation_model=True
)
print(f"Correct: {score}")  # 1

# Handles variations
prediction = "The capital is Paris"
score = scorer.squad_score(input, prediction, expected, eval_model, True)
print(f"Correct: {score}")  # 1 (LLM judges as correct)
```

---

### 5. Pass@K Score

**Purpose**: Calculate pass@k metric for code generation (used in HumanEval).

**Method**: `pass_at_k(n, c, k)`

**Parameters**:
- `n` (int): Total number of samples
- `c` (int): Number of correct samples
- `k` (int): k in pass@k

**Returns**: `float` - Pass@k probability

**Example**:
```python
from deepeval.scorer import Scorer

scorer = Scorer()

# Generated 10 code samples, 7 passed tests
# What's the probability at least 1 of 3 random samples passes?
score = scorer.pass_at_k(n=10, c=7, k=3)
print(f"Pass@3: {score}")  # ~0.97

# Pass@1 (probability any single sample passes)
score = scorer.pass_at_k(n=10, c=7, k=1)
print(f"Pass@1: {score}")  # 0.7
```

---

## Usage in Custom Metrics

The Scorer module is commonly used to build custom metrics that don't require LLM evaluation.

### Example: ROUGE Metric

```python
from deepeval.scorer import Scorer
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class RougeMetric(BaseMetric):
    def __init__(self, threshold: float = 0.5, score_type: str = "rouge1"):
        self.threshold = threshold
        self.score_type = score_type
        self.scorer = Scorer()

    def measure(self, test_case: LLMTestCase):
        self.score = self.scorer.rouge_score(
            target=test_case.expected_output,
            prediction=test_case.actual_output,
            score_type=self.score_type
        )
        self.success = self.score >= self.threshold
        self.reason = f"ROUGE-{self.score_type[-1]} score: {self.score:.3f}"
        return self.score

    async def a_measure(self, test_case: LLMTestCase):
        return self.measure(test_case)

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return f"ROUGE-{self.score_type[-1]}"

# Usage
metric = RougeMetric(threshold=0.6, score_type="rougeL")
test_case = LLMTestCase(
    input="Summarize this article...",
    actual_output="The article discusses...",
    expected_output="This article is about..."
)
score = metric.measure(test_case)
print(f"Score: {score}, Success: {metric.success}")
```

### Example: Toxicity Metric

```python
from deepeval.scorer import Scorer
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class ToxicityMetric(BaseMetric):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.scorer = Scorer()

    def measure(self, test_case: LLMTestCase):
        scores = self.scorer.neural_toxic_score(test_case.actual_output)
        
        # Calculate mean toxicity
        self.score = sum(scores.values()) / len(scores)
        self.success = self.score <= self.threshold
        
        # Find highest toxicity type
        max_type = max(scores, key=scores.get)
        self.reason = f"Mean toxicity: {self.score:.3f}, Highest: {max_type} ({scores[max_type]:.3f})"
        
        return self.score

    async def a_measure(self, test_case: LLMTestCase):
        return self.measure(test_case)

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "Toxicity"

# Usage
metric = ToxicityMetric(threshold=0.3)
test_case = LLMTestCase(
    input="Tell me about your day",
    actual_output="I had a wonderful day, thank you for asking!"
)
score = metric.measure(test_case)
print(f"Toxicity: {score}, Safe: {metric.success}")
```

---

## Usage in Benchmarks

The Scorer module is extensively used in DeepEval's benchmark implementations.

### Example: SQuAD Benchmark

```python
from deepeval.scorer import Scorer
from deepeval.benchmarks import SQuAD

# SQuAD benchmark uses scorer.squad_score() internally
benchmark = SQuAD(n_shots=5)

# The scorer evaluates if predictions match expected outputs
# accounting for variations like "2" vs "two"
```

### Example: Custom Benchmark

```python
from deepeval.scorer import Scorer
from deepeval.benchmarks.base_benchmark import DeepEvalBaseBenchmark

class MyBenchmark(DeepEvalBaseBenchmark):
    def __init__(self):
        self.scorer = Scorer()
    
    def evaluate(self, model):
        for task in self.tasks:
            prediction = model.generate(task.input)
            
            # Use scorer for evaluation
            score = self.scorer.exact_match_score(
                target=task.expected_output,
                prediction=prediction
            )
            
            # Or use BLEU for more lenient matching
            score = self.scorer.sentence_bleu_score(
                references=task.expected_output,
                prediction=prediction,
                bleu_type="bleu1"
            )
```

---

## Complete API Reference

### Traditional NLP Metrics

| Method | Purpose | Returns |
|--------|---------|---------|
| `rouge_score(target, prediction, score_type)` | ROUGE score for summarization | float (0-1) |
| `sentence_bleu_score(references, prediction, bleu_type)` | BLEU score for translation | float (0-1) |
| `exact_match_score(target, prediction)` | Exact string match | int (0 or 1) |
| `quasi_exact_match_score(target, prediction)` | Normalized string match | int (0 or 1) |
| `quasi_contains_score(targets, prediction)` | Normalized contains check | int (0 or 1) |

### Neural Model-Based Metrics

| Method | Purpose | Returns |
|--------|---------|---------|
| `bert_score(references, predictions, model, lang)` | Semantic similarity via BERT | dict with precision/recall/f1 |
| `neural_toxic_score(prediction, model)` | Toxicity detection | dict with toxicity scores |
| `neural_bias_score(text, model)` | Bias detection | float (0-1) |
| `answer_relevancy_score(predictions, target, model_type, model_name)` | Answer relevancy | float (0-1) |

### Specialized Metrics

| Method | Purpose | Returns |
|--------|---------|---------|
| `faithfulness_score(target, prediction, model, granularity, device)` | Faithfulness to source | float (0-1) |
| `hallucination_score(source, prediction, model)` | Hallucination detection | float (lower = more hallucination) |
| `truth_identification_score(target, prediction)` | Correct answer percentage | int (0-100) |
| `squad_score(input, prediction, expected_output, evaluation_model, using_native_evaluation_model)` | QA correctness | int (0 or 1) |
| `pass_at_k(n, c, k)` | Pass@k for code generation | float (0-1) |

---

## Installation Requirements

Different scorer methods require different dependencies:

```bash
# ROUGE score
pip install rouge-score

# BLEU score
pip install nltk

# BERTScore
pip install bert-score torch

# Toxicity detection
pip install detoxify

# Answer relevancy
pip install sentence-transformers

# Faithfulness (SummaCZS)
# Requires specific model installation

# Hallucination (Vectara)
# Requires specific model installation

# Bias detection
# Requires specific model installation
```

**Install all at once**:
```bash
pip install rouge-score nltk bert-score torch detoxify sentence-transformers
```

---

## Best Practices

### 1. Choose the Right Metric

```python
# For summarization: Use ROUGE
scorer.rouge_score(target, prediction, "rougeL")

# For translation: Use BLEU
scorer.sentence_bleu_score(references, prediction, "bleu4")

# For semantic similarity: Use BERTScore
scorer.bert_score(reference, prediction)

# For exact answers: Use exact match
scorer.exact_match_score(target, prediction)

# For safety: Use toxicity/bias scores
scorer.neural_toxic_score(prediction)
scorer.neural_bias_score(prediction)
```

### 2. Combine Multiple Metrics

```python
from deepeval.scorer import Scorer

scorer = Scorer()

def comprehensive_evaluation(target, prediction):
    # Traditional metrics
    rouge = scorer.rouge_score(target, prediction, "rougeL")
    bleu = scorer.sentence_bleu_score(target, prediction, "bleu1")
    
    # Neural metrics
    bert = scorer.bert_score(target, prediction)
    bert_f1 = bert["bert-f1"][0]
    
    # Safety checks
    toxicity = scorer.neural_toxic_score(prediction)
    mean_toxicity = sum(toxicity.values()) / len(toxicity)
    
    return {
        "rouge_l": rouge,
        "bleu_1": bleu,
        "bert_f1": bert_f1,
        "toxicity": mean_toxicity,
        "overall": (rouge + bleu + bert_f1) / 3
    }
```

### 3. Handle Edge Cases

```python
from deepeval.scorer import Scorer

scorer = Scorer()

def safe_scoring(target, prediction):
    # Handle empty predictions
    if not prediction or not prediction.strip():
        return 0.0
    
    # Handle missing target
    if not target:
        return None
    
    try:
        score = scorer.rouge_score(target, prediction, "rouge1")
        return score
    except Exception as e:
        print(f"Scoring failed: {e}")
        return 0.0
```

### 4. Optimize for Performance

```python
from deepeval.scorer import Scorer

# Initialize once, reuse many times
scorer = Scorer()

# For batch evaluation, use BERTScore's batch mode
references = ["ref1", "ref2", "ref3"]
predictions = ["pred1", "pred2", "pred3"]

# Single call for all pairs (faster)
scores = scorer.bert_score(references, predictions)

# vs multiple calls (slower)
# for ref, pred in zip(references, predictions):
#     score = scorer.bert_score(ref, pred)
```

### 5. Set Appropriate Thresholds

```python
# ROUGE/BLEU: 0.3-0.5 for acceptable, 0.6+ for good
rouge_threshold = 0.5

# BERTScore: 0.7-0.8 for acceptable, 0.85+ for good
bert_threshold = 0.8

# Toxicity: 0.3-0.5 for acceptable, <0.3 for safe
toxicity_threshold = 0.3

# Exact match: Binary (0 or 1)
exact_match_threshold = 1
```

---

## Summary

The DeepEval Scorer module provides:

- **Traditional NLP metrics**: ROUGE, BLEU, exact match for fast, deterministic evaluation
- **Neural metrics**: BERTScore, toxicity, bias detection using pre-trained models
- **Specialized metrics**: Faithfulness, hallucination, truth identification
- **Benchmark support**: Used extensively in DeepEval's benchmark implementations
- **Custom metric building**: Foundation for creating non-LLM evaluation metrics
- **Cost-effective**: No API costs, faster than LLM-based evaluation
- **Deterministic**: Same inputs always produce same outputs

Use Scorer for fast, traditional evaluation and combine with LLM-based metrics for comprehensive evaluation.
