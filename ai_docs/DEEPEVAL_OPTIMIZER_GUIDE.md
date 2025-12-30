# DeepEval Prompt Optimizer - Complete Guide

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Quick Start](#quick-start)
4. [Creating an Optimizer](#creating-an-optimizer)
5. [Optimization Algorithms](#optimization-algorithms)
6. [Model Callback](#model-callback)
7. [Configuration Options](#configuration-options)
8. [Optimization Report](#optimization-report)
9. [Advanced Usage](#advanced-usage)
10. [Best Practices](#best-practices)

---

## Overview

DeepEval's `PromptOptimizer` automatically crafts better prompts based on evaluation results from 50+ metrics. Instead of manually tweaking prompts through trial and error, the optimizer uses research-backed algorithms to iteratively improve prompts.

### Key Benefits

- **Automated optimization** - No manual prompt engineering required
- **Metric-driven** - Uses evaluation scores to guide improvements
- **Research-backed** - Implements state-of-the-art algorithms (GEPA, MIPROv2, COPRO, SIMBA)
- **Multi-objective** - Optimizes for multiple metrics simultaneously
- **Async support** - Fast optimization with concurrent evaluations

### How It Works

1. **Start with initial prompt** - Provide a baseline prompt template
2. **Evaluate on goldens** - Score the prompt using your metrics and test data
3. **Generate feedback** - Extract reasons why the prompt failed
4. **Rewrite prompt** - Use LLM to improve prompt based on feedback
5. **Iterate** - Repeat until optimal prompt is found
6. **Return best prompt** - Get the highest-scoring prompt variant

---

## Core Concepts

### Prompt

A `Prompt` object containing your prompt template (text or messages).

```python
from deepeval.prompt import Prompt

# Text prompt
prompt = Prompt(text_template="Answer the question: {input}")

# Chat prompt
prompt = Prompt(messages_template=[
    PromptMessage(role="system", content="You are a helpful assistant"),
    PromptMessage(role="user", content="{input}")
])
```

### Goldens

Test data with inputs and expected outputs used for evaluation.

```python
from deepeval.dataset import Golden

goldens = [
    Golden(input="What is Python?", expected_output="Python is a programming language"),
    Golden(input="What is Java?", expected_output="Java is a programming language")
]
```

### Metrics

Evaluation metrics that score prompt performance.

```python
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

metrics = [
    AnswerRelevancyMetric(threshold=0.7),
    FaithfulnessMetric(threshold=0.8)
]
```

### Model Callback

Function that wraps your LLM application for evaluation.

```python
async def model_callback(prompt: Prompt, golden: Golden) -> str:
    # Interpolate prompt with golden's input
    text = prompt.interpolate(input=golden.input)
    
    # Call your LLM
    response = await your_llm(text)
    
    return response
```

---

## Quick Start

Here's a minimal example to get started:

```python
from deepeval.optimizer import PromptOptimizer
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.prompt import Prompt
from deepeval.dataset import Golden

# 1. Define initial prompt
prompt = Prompt(text_template="Answer this question: {input}")

# 2. Define model callback
async def model_callback(prompt: Prompt, golden: Golden) -> str:
    text = prompt.interpolate(input=golden.input)
    return await your_llm_app(text)

# 3. Create optimizer
optimizer = PromptOptimizer(
    metrics=[AnswerRelevancyMetric()],
    model_callback=model_callback
)

# 4. Run optimization
optimized_prompt = optimizer.optimize(
    prompt=prompt,
    goldens=[
        Golden(input="What is Saturn?", expected_output="Saturn is a car brand"),
        Golden(input="What is Mercury?", expected_output="Mercury is a planet")
    ]
)

# 5. Use optimized prompt
print(optimized_prompt.text_template)
```

Run it:

```bash
python main.py
```

---

## Creating an Optimizer

### Basic Initialization

```python
from deepeval.optimizer import PromptOptimizer
from deepeval.metrics import AnswerRelevancyMetric

optimizer = PromptOptimizer(
    metrics=[AnswerRelevancyMetric()],
    model_callback=model_callback
)
```

### Full Initialization

```python
from deepeval.optimizer import PromptOptimizer
from deepeval.optimizer.algorithms import GEPA
from deepeval.optimizer.configs import AsyncConfig, DisplayConfig, MutationConfig
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

optimizer = PromptOptimizer(
    # Required
    metrics=[
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.8)
    ],
    model_callback=model_callback,
    
    # Optional
    optimizer_model="gpt-4",              # LLM for rewriting prompts
    algorithm=GEPA(iterations=10),        # Optimization algorithm
    async_config=AsyncConfig(             # Concurrency settings
        run_async=True,
        max_concurrent=10,
        throttle_value=0.1
    ),
    display_config=DisplayConfig(         # Display settings
        show_indicator=True,
        announce_ties=False
    ),
    mutation_config=MutationConfig(       # For chat prompts
        target_type="random"
    )
)
```

### Parameters

**Required**:
- `metrics` (List[BaseMetric]): Metrics to optimize for
- `model_callback` (Callable): Function that wraps your LLM app

**Optional**:
- `optimizer_model` (str or DeepEvalBaseLLM): LLM used to rewrite prompts (default: GPT-4)
- `algorithm` (GEPA | MIPROV2 | COPRO | SIMBA): Optimization algorithm (default: GEPA())
- `async_config` (AsyncConfig): Concurrency configuration
- `display_config` (DisplayConfig): Progress display configuration
- `mutation_config` (MutationConfig): Chat prompt mutation configuration

---

## Optimization Algorithms

DeepEval offers 4 state-of-the-art optimization algorithms:

### 1. GEPA (Default)

**Genetic-Pareto Algorithm** - Multi-objective optimization using Pareto frontier.

**How it works**:
1. Split goldens into feedback set and Pareto validation set
2. Sample minibatch from feedback set
3. Generate feedback from metric failures
4. Rewrite prompt using feedback
5. Evaluate on Pareto set
6. Accept if better, maintain Pareto frontier
7. Repeat for N iterations

**Best for**: Multi-objective optimization, balanced exploration

```python
from deepeval.optimizer.algorithms import GEPA

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    algorithm=GEPA(
        iterations=10,           # Number of optimization iterations
        minibatch_size=8,        # Samples per iteration for feedback
        pareto_size=3,           # Size of Pareto validation set
        random_seed=42,          # For reproducibility
        tie_breaker="prefer_child"  # How to break ties
    )
)
```

**Parameters**:
- `iterations` (int, default=5): Number of optimization iterations
- `minibatch_size` (int, default=8): Feedback samples per iteration
- `pareto_size` (int, default=3): Pareto validation set size
- `random_seed` (int, optional): Random seed for reproducibility
- `tie_breaker` (str, default="prefer_child"): Tie-breaking strategy

---

### 2. MIPROv2

**Model-Instructed Prompt Optimization v2** - Zero-shot surrogate-based search.

**How it works**:
1. Generate multiple prompt candidates
2. Evaluate candidates on minibatches
3. Use epsilon-greedy selection
4. Periodically do full evaluations
5. Bootstrap demonstrations from best examples
6. Return best prompt

**Best for**: Large-scale optimization, exploration-exploitation balance

```python
from deepeval.optimizer.algorithms import MIPROV2

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    algorithm=MIPROV2(
        num_candidates=10,       # Prompt candidates per trial
        num_trials=20,           # Total optimization trials
        minibatch_size=25,       # Samples for quick evaluation
        minibatch_full_eval_steps=10,  # Full eval frequency
        max_bootstrapped_demos=4,      # Max bootstrapped examples
        max_labeled_demos=4,           # Max labeled examples
        num_demo_sets=5,               # Demo set variations
        random_seed=42
    )
)
```

**Parameters**:
- `num_candidates` (int, default=10): Candidates per trial
- `num_trials` (int, default=20): Total trials
- `minibatch_size` (int, default=25): Minibatch size
- `minibatch_full_eval_steps` (int, default=10): Full eval frequency
- `max_bootstrapped_demos` (int, default=4): Max bootstrapped demos
- `max_labeled_demos` (int, default=4): Max labeled demos
- `num_demo_sets` (int, default=5): Demo set variations
- `random_seed` (int, optional): Random seed

---

### 3. COPRO

**Contextual Prompt Optimization** - Gradient-free optimization with context.

**Best for**: Context-aware optimization

```python
from deepeval.optimizer.algorithms import COPRO

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    algorithm=COPRO(
        iterations=10,
        random_seed=42
    )
)
```

---

### 4. SIMBA

**Simple Iterative Minibatch-Based Algorithm** - Straightforward iterative approach.

**Best for**: Simple, interpretable optimization

```python
from deepeval.optimizer.algorithms import SIMBA

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    algorithm=SIMBA(
        iterations=10,
        random_seed=42
    )
)
```

---

## Model Callback

The model callback is the bridge between the optimizer and your LLM application.

### Basic Callback

```python
from deepeval.prompt import Prompt
from deepeval.dataset import Golden

async def model_callback(prompt: Prompt, golden: Golden) -> str:
    # 1. Interpolate prompt with golden's input
    text = prompt.interpolate(input=golden.input)
    
    # 2. Call your LLM
    response = await your_llm(text)
    
    # 3. Return response as string
    return response
```

### Chat Callback

```python
async def model_callback(prompt: Prompt, golden: Golden) -> str:
    # Interpolate messages
    messages = prompt.interpolate(
        input=golden.input,
        context=golden.context
    )
    
    # Call chat API
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    
    return response.choices[0].message.content
```

### RAG Callback

```python
async def model_callback(prompt: Prompt, golden: Golden) -> str:
    # Retrieve relevant documents
    docs = await retriever.retrieve(golden.input)
    
    # Interpolate with retrieved context
    text = prompt.interpolate(
        query=golden.input,
        context="\n".join(docs)
    )
    
    # Generate response
    response = await llm.generate(text)
    
    return response
```

### Agent Callback

```python
async def model_callback(prompt: Prompt, golden: Golden) -> str:
    # Set agent's system prompt
    agent.system_prompt = prompt.interpolate(
        task=golden.input,
        tools=agent.available_tools
    )
    
    # Run agent
    result = await agent.run(golden.input)
    
    return result.output
```

### Callback Requirements

**Must accept**:
- `prompt` (Prompt): Current prompt candidate
- `golden` (Golden or ConversationalGolden): Test data

**Must return**:
- `str`: LLM's response

**Best practices**:
- Always use `prompt.interpolate()` to inject variables
- Handle errors gracefully
- Return empty string on failure (don't raise exceptions)
- Use async for better performance

---

## Configuration Options

### Async Config

Control concurrency and throttling during optimization.

```python
from deepeval.optimizer.configs import AsyncConfig

async_config = AsyncConfig(
    run_async=True,          # Enable async execution
    max_concurrent=10,       # Max concurrent evaluations
    throttle_value=0.1       # Delay between requests (seconds)
)

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    async_config=async_config
)
```

**Parameters**:
- `run_async` (bool, default=True): Enable async execution
- `max_concurrent` (int, default=10): Max concurrent tasks
- `throttle_value` (float, default=0.1): Delay between requests

---

### Display Config

Control what's displayed during optimization.

```python
from deepeval.optimizer.configs import DisplayConfig

display_config = DisplayConfig(
    show_indicator=True,     # Show progress bar
    announce_ties=False      # Print tie messages
)

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    display_config=display_config
)
```

**Parameters**:
- `show_indicator` (bool, default=True): Show progress indicator
- `announce_ties` (bool, default=False): Print when ties occur

---

### Mutation Config

Control how chat prompts are mutated (which message to rewrite).

```python
from deepeval.optimizer.configs import MutationConfig

# Random message selection
mutation_config = MutationConfig(
    target_type="random"
)

# Fixed index selection
mutation_config = MutationConfig(
    target_type="fixed_index",
    target_index=0              # Always mutate first message
)

# Role-based selection
mutation_config = MutationConfig(
    target_type="random",
    target_role="system"        # Only mutate system messages
)

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    mutation_config=mutation_config
)
```

**Parameters**:
- `target_type` (str, default="random"): Selection strategy
  - `"random"`: Random message
  - `"fixed_index"`: Specific index
- `target_role` (str, optional): Filter by role ("system", "user", "assistant")
- `target_index` (int, default=0): Index when using "fixed_index"

---

## Optimization Report

After optimization, access detailed results via `optimizer.optimization_report`.

### Report Structure

```python
optimized_prompt = optimizer.optimize(prompt, goldens)

report = optimizer.optimization_report

print(f"Optimization ID: {report.optimization_id}")
print(f"Best prompt ID: {report.best_id}")
print(f"Accepted iterations: {len(report.accepted_iterations)}")
```

### Report Fields

| Field | Type | Description |
|-------|------|-------------|
| `optimization_id` | str | Unique identifier for this run |
| `best_id` | str | ID of best-performing prompt |
| `accepted_iterations` | List[AcceptedIteration] | List of accepted improvements |
| `pareto_scores` | Dict[str, List[float]] | Scores on Pareto validation set |
| `parents` | Dict[str, Optional[str]] | Parent-child relationships |
| `prompt_configurations` | Dict[str, PromptConfigSnapshot] | All prompt variants explored |

### Accepted Iterations

Each accepted iteration shows:

```python
for iteration in report.accepted_iterations:
    print(f"Module: {iteration.module}")
    print(f"Parent: {iteration.parent}")
    print(f"Child: {iteration.child}")
    print(f"Score before: {iteration.before}")
    print(f"Score after: {iteration.after}")
    print(f"Improvement: {iteration.after - iteration.before}")
```

### Prompt Configurations

Access all explored prompts:

```python
# Get best prompt configuration
best_config = report.prompt_configurations[report.best_id]
print(f"Best prompt: {best_config.prompts}")

# Get initial prompt
initial_id = [k for k, v in report.parents.items() if v is None][0]
initial_config = report.prompt_configurations[initial_id]
print(f"Initial prompt: {initial_config.prompts}")

# Trace evolution
current_id = report.best_id
while current_id:
    config = report.prompt_configurations[current_id]
    print(f"Prompt: {config.prompts}")
    current_id = report.parents[current_id]
```

---

## Advanced Usage

### Multi-Objective Optimization

Optimize for multiple metrics with custom weights:

```python
from deepeval.optimizer.types import WeightedObjective
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, HallucinationMetric

# Create scorer with weighted objective
from deepeval.optimizer.scorer import Scorer

scorer = Scorer(
    model_callback=model_callback,
    metrics=[
        AnswerRelevancyMetric(),
        FaithfulnessMetric(),
        HallucinationMetric()
    ],
    max_concurrent=10,
    throttle_seconds=0.1,
    objective_scalar=WeightedObjective(
        weights_by_metric={
            "AnswerRelevancyMetric": 2.0,  # 2x weight
            "FaithfulnessMetric": 1.5,     # 1.5x weight
            "HallucinationMetric": 1.0     # 1x weight
        },
        default_weight=1.0
    )
)

# Use custom scorer in algorithm
algorithm = GEPA(iterations=10)
algorithm.scorer = scorer

optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    algorithm=algorithm
)
```

### Custom Objective Function

Create custom scoring logic:

```python
from deepeval.optimizer.types import Objective

class MaxObjective(Objective):
    """Use maximum score across metrics instead of mean."""
    
    def scalarize(self, scores_by_metric: Dict[str, float]) -> float:
        if not scores_by_metric:
            return 0.0
        return max(scores_by_metric.values())

# Use in scorer
scorer = Scorer(
    model_callback=model_callback,
    metrics=[...],
    max_concurrent=10,
    throttle_seconds=0.1,
    objective_scalar=MaxObjective()
)
```

### Async Optimization

Run optimization asynchronously:

```python
import asyncio

async def main():
    optimizer = PromptOptimizer(
        metrics=[...],
        model_callback=model_callback
    )
    
    optimized_prompt = await optimizer.a_optimize(
        prompt=prompt,
        goldens=goldens
    )
    
    print(optimized_prompt.text_template)

asyncio.run(main())
```

### Conversational Optimization

Optimize chat-based prompts:

```python
from deepeval.dataset import ConversationalGolden
from deepeval.test_case import Turn
from deepeval.metrics import ConversationCompletenessMetric

# Define conversational goldens
goldens = [
    ConversationalGolden(
        turns=[
            Turn(role="user", content="Hello"),
            Turn(role="assistant", content="Hi! How can I help?"),
            Turn(role="user", content="Tell me about Python")
        ]
    )
]

# Conversational callback
async def model_callback(prompt: Prompt, golden: ConversationalGolden) -> str:
    # Get conversation history
    history = golden.turns[:-1]  # All but last turn
    
    # Interpolate system prompt
    messages = prompt.interpolate(
        conversation_history=history,
        current_query=golden.turns[-1].content
    )
    
    # Generate response
    response = await llm.chat(messages)
    return response

# Optimize with conversational metrics
optimizer = PromptOptimizer(
    metrics=[ConversationCompletenessMetric()],
    model_callback=model_callback
)

optimized_prompt = optimizer.optimize(prompt, goldens)
```

---

## Best Practices

### 1. Provide Sufficient Goldens

```python
# Bad: Too few goldens
goldens = [Golden(input="test", expected_output="output")]

# Good: Diverse, representative goldens
goldens = [
    Golden(input="What is Python?", expected_output="Python is a language"),
    Golden(input="What is Java?", expected_output="Java is a language"),
    Golden(input="What is C++?", expected_output="C++ is a language"),
    Golden(input="Compare Python and Java", expected_output="Python is..."),
    # ... at least 10-20 goldens
]
```

**Recommendations**:
- Minimum: 10 goldens
- Recommended: 20-50 goldens
- Ensure diversity in inputs and expected outputs
- Cover edge cases and failure modes

---

### 2. Choose Appropriate Metrics

```python
# For RAG applications
metrics = [
    AnswerRelevancyMetric(threshold=0.7),
    FaithfulnessMetric(threshold=0.8),
    ContextualRelevancyMetric(threshold=0.7)
]

# For creative generation
metrics = [
    GEval(
        name="Creativity",
        criteria="Evaluate creativity and originality",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT]
    )
]

# For safety-critical applications
metrics = [
    HallucinationMetric(threshold=0.3),
    ToxicityMetric(threshold=0.2),
    BiasMetric(threshold=0.3)
]
```

---

### 3. Start with Default Algorithm

```python
# Start simple with GEPA defaults
optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback
    # algorithm defaults to GEPA()
)

# If not satisfied, try MIPROv2
optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    algorithm=MIPROV2()
)
```

---

### 4. Use Async for Performance

```python
# Enable async with appropriate concurrency
optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    async_config=AsyncConfig(
        run_async=True,
        max_concurrent=10,      # Adjust based on API limits
        throttle_value=0.1      # Prevent rate limiting
    )
)
```

---

### 5. Set Random Seed for Reproducibility

```python
optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    algorithm=GEPA(random_seed=42)
)
```

---

### 6. Monitor Optimization Progress

```python
# Enable progress indicator
optimizer = PromptOptimizer(
    metrics=[...],
    model_callback=model_callback,
    display_config=DisplayConfig(
        show_indicator=True,
        announce_ties=True  # See when ties occur
    )
)

# After optimization, check report
optimized_prompt = optimizer.optimize(prompt, goldens)
print(f"Accepted {len(optimizer.optimization_report.accepted_iterations)} improvements")
```

---

### 7. Handle Errors in Callback

```python
async def model_callback(prompt: Prompt, golden: Golden) -> str:
    try:
        text = prompt.interpolate(input=golden.input)
        response = await your_llm(text)
        return response
    except Exception as e:
        print(f"Error in callback: {e}")
        return ""  # Return empty string, don't raise
```

---

### 8. Save and Version Optimized Prompts

```python
from deepeval.prompt import Prompt

# Optimize
optimized_prompt = optimizer.optimize(prompt, goldens)

# Push to Confident AI for versioning
optimized_prompt.alias = "customer-support-v2"
optimized_prompt.push()

# Or save locally
with open("optimized_prompt.txt", "w") as f:
    f.write(optimized_prompt.text_template)
```

---

## Summary

DeepEval's Prompt Optimizer provides:

- **Automated prompt engineering** - No manual tweaking required
- **4 research-backed algorithms** - GEPA, MIPROv2, COPRO, SIMBA
- **Multi-objective optimization** - Optimize for multiple metrics simultaneously
- **Flexible configuration** - Control concurrency, display, and mutation behavior
- **Detailed reporting** - Track optimization progress and prompt evolution
- **Async support** - Fast optimization with concurrent evaluations
- **Integration with DeepEval ecosystem** - Works seamlessly with metrics, prompts, and datasets

The optimizer is designed for production use with features like async execution, error handling, and comprehensive reporting.
