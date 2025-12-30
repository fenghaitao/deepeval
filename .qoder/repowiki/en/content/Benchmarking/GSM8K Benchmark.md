# GSM8K Benchmark

<cite>
**Referenced Files in This Document**   
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py)
- [template.py](file://deepeval/benchmarks/gsm8k/template.py)
- [base_benchmark.py](file://deepeval/benchmarks/base_benchmark.py)
- [schema.py](file://deepeval/benchmarks/schema.py)
- [benchmarks-gsm8k.mdx](file://docs/docs/benchmarks-gsm8k.mdx)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Core Components](#core-components)
3. [Architecture Overview](#architecture-overview)
4. [Detailed Component Analysis](#detailed-component-analysis)
5. [Problem Loading and Dataset Management](#problem-loading-and-dataset-management)
6. [Prompt Templating for Step-by-Step Reasoning](#prompt-templating-for-step-by-step-reasoning)
7. [Answer Extraction and Verification](#answer-extraction-and-verification)
8. [Evaluation Execution and Accuracy Computation](#evaluation-execution-and-accuracy-computation)
9. [Common Challenges in Multi-Step Arithmetic Evaluation](#common-challenges-in-multi-step-arithmetic-evaluation)
10. [Best Practices for Chain-of-Thought Configuration](#best-practices-for-chain-of-thought-configuration)
11. [Practical Example Implementation](#practical-example-implementation)

## Introduction
The **GSM8K** benchmark comprises 1,319 grade school math word problems, each crafted by expert human problem writers. These problems involve elementary arithmetic operations (+ − ×÷) and require between 2 to 8 steps to solve. The dataset is designed to evaluate an LLM’s ability to perform multi-step mathematical reasoning. For more information, you can [read the original GSM8K paper here](https://arxiv.org/abs/2110.14168).

The GSM8K implementation in DeepEval provides a structured framework for assessing language models on their mathematical reasoning capabilities through multi-step problem solving. This document details the implementation architecture, workflow, and best practices for configuring and executing evaluations on this benchmark.

**Section sources**
- [benchmarks-gsm8k.mdx](file://docs/docs/benchmarks-gsm8k.mdx#L1-L10)

## Core Components
The GSM8K benchmark in DeepEval consists of two primary components: the main benchmark class (`GSM8K`) and the template handler (`GSM8KTemplate`). The `GSM8K` class inherits from `DeepEvalBaseBenchmark` and orchestrates the evaluation process, while `GSM8KTemplate` manages prompt construction and answer formatting.

Key parameters include:
- `n_shots`: Number of few-shot examples (maximum 15)
- `enable_cot`: Boolean flag to enable chain-of-thought reasoning
- `n_problems`: Number of problems to evaluate (default: 1319)
- `verbose_mode`: Flag to enable detailed logging during evaluation

**Section sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L15-L44)
- [template.py](file://deepeval/benchmarks/gsm8k/template.py#L4-L13)

## Architecture Overview
The GSM8K evaluation system follows a modular architecture with clear separation of concerns between problem loading, prompt generation, model execution, and result verification.

```mermaid
graph TB
A[Load Benchmark Dataset] --> B[Extract Few-Shot Examples]
B --> C[Generate Prompt Template]
C --> D[Execute Model Prediction]
D --> E[Extract Numerical Answer]
E --> F[Verify Against Ground Truth]
F --> G[Compute Overall Accuracy]
subgraph "Template System"
C1[GSM8KTemplate]
C1 --> C2[Format Examples]
C1 --> C3[Apply Chain-of-Thought]
C1 --> C4[Construct Final Prompt]
end
subgraph "Evaluation Engine"
D1[GSM8K Class]
D1 --> D2[Iterate Through Problems]
D1 --> D3[Track Predictions]
D1 --> D4[Calculate Score]
end
C --> D
C1 --> C
D1 --> A
D1 --> G
```

**Diagram sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L15-L183)
- [template.py](file://deepeval/benchmarks/gsm8k/template.py#L4-L56)

## Detailed Component Analysis

### GSM8K Class Implementation
The `GSM8K` class serves as the main orchestrator for the benchmark evaluation process. It manages the lifecycle from dataset loading to final accuracy computation.

```mermaid
classDiagram
class GSM8K {
+n_shots : int
+enable_cot : bool
+n_problems : int
+verbose_mode : bool
+confinement_instructions : str
+shots_dataset : List[Dict]
+predictions : DataFrame
+overall_score : float
+evaluate(model) : DeepEvalBaseBenchmarkResult
+predict(model, golden) : Dict
+load_benchmark_dataset() : List[Golden]
+print_verbose_logs(idx, input, expected, prediction, score)
}
class DeepEvalBaseBenchmark {
<<abstract>>
}
GSM8K --|> DeepEvalBaseBenchmark
GSM8K --> Scorer : uses
GSM8K --> GSM8KTemplate : delegates
GSM8K --> Golden : processes
```

**Diagram sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L15-L183)

### Template System Analysis
The `GSM8KTemplate` class handles all aspects of prompt construction and answer formatting for the benchmark.

```mermaid
classDiagram
class GSM8KTemplate {
+generate_output(input, train_set, n_shots, enable_cot) : str
+format_example(data, enable_cot) : str
+format_answer(data) : str
+format_subject(subject) : void
}
GSM8KTemplate --> re : uses
```

**Diagram sources**
- [template.py](file://deepeval/benchmarks/gsm8k/template.py#L4-L56)

## Problem Loading and Dataset Management
The GSM8K benchmark loads its dataset from the Hugging Face datasets library using `load_dataset("gsm8k", "main")`. The dataset is divided into training and test sets, with the training set used for few-shot examples and the test set for evaluation.

The `load_benchmark_dataset()` method performs several key functions:
1. Loads the GSM8K dataset from Hugging Face
2. Constructs the few-shot example set from the training portion
3. Formats test problems into `Golden` objects with input and expected output
4. Extracts answers using regex pattern matching on the "####" delimiter

```mermaid
flowchart TD
Start([Start]) --> LoadDataset["Load dataset('gsm8k', 'main')"]
LoadDataset --> CheckCache{"Dataset cached?"}
CheckCache --> |Yes| UseCached["Use cached dataset"]
CheckCache --> |No| CacheDataset["Cache dataset"]
CacheDataset --> ConstructShots["Construct shots_dataset from train set"]
ConstructShots --> FormatTest["Format test set into Goldens"]
FormatTest --> ExtractAnswers["Extract answers using format_answer()"]
ExtractAnswers --> ReturnGoldens["Return List[Golden]"]
ReturnGoldens --> End([End])
```

**Diagram sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L153-L179)

**Section sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L153-L179)

## Prompt Templating for Step-by-Step Reasoning
The prompt templating system is central to the GSM8K benchmark's ability to evaluate chain-of-thought reasoning. The `GSM8KTemplate.generate_output()` method constructs prompts that guide the model through multi-step problem solving.

Key features of the templating system:
- Few-shot prompting with configurable number of examples (n_shots)
- Chain-of-thought activation via "Let's think step-by-step" instruction
- Clear problem and answer formatting using markdown-style headers
- Support for both CoT and direct answer modes

```mermaid
sequenceDiagram
participant User as Evaluation System
participant Template as GSM8KTemplate
participant Model as LLM
User->>Template : generate_output(input, train_set, n_shots=3, enable_cot=True)
Template->>Template : Add header "The following are grade school math word problems"
Template->>Template : Format 3 few-shot examples with solutions
Template->>Template : Add target problem with "**Problem** : [input]"
Template->>Template : Add "Let's think step-by-step."
Template-->>User : Return complete prompt
User->>Model : Send prompt for generation
Model-->>User : Return response with reasoning and answer
```

**Diagram sources**
- [template.py](file://deepeval/benchmarks/gsm8k/template.py#L10-L32)
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L94-L104)

**Section sources**
- [template.py](file://deepeval/benchmarks/gsm8k/template.py#L10-L32)

## Answer Extraction and Verification
The answer extraction system ensures that only the final numerical answer is evaluated, regardless of the length of the reasoning process. This is achieved through several mechanisms:

1. **Structured Output Schema**: Uses `NumberSchema` to constrain model output
2. **Regex-Based Extraction**: Extracts answers following the "####" pattern
3. **Multiple Response Type Handling**: Processes strings, dictionaries, tuples, and objects
4. **Error Resilience**: Implements try-except blocks to handle generation failures

The verification process uses exact match scoring to determine if the predicted answer matches the expected output.

```mermaid
flowchart TD
A[Model Response] --> B{Response Type}
B --> |String| C[Return as-is]
B --> |Dict| D{Contains 'answer'?}
D --> |Yes| E[Return answer field]
D --> |No| F[Convert to string]
B --> |Tuple| G{Has answer attribute?}
G --> |Yes| H[Return answer attribute]
G --> |No| I[Return first element]
C --> J[Compare with expected output]
E --> J
F --> J
H --> J
I --> J
J --> K[Return score: 1 or 0]
```

**Diagram sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L106-L143)

**Section sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L106-L143)

## Evaluation Execution and Accuracy Computation
The evaluation process follows a systematic workflow to assess model performance across all test problems:

```mermaid
flowchart TD
Start([Evaluation Start]) --> Initialize["Initialize counters: correct=0, total=n_problems"]
Initialize --> LoadProblems["Load benchmark dataset"]
LoadProblems --> ProgressBar["Create progress bar for n_problems"]
ProgressBar --> LoopStart["For each golden in dataset"]
LoopStart --> GeneratePrompt["Generate prompt using template"]
GeneratePrompt --> ModelCall["Call model.generate()"]
ModelCall --> ExtractAnswer["Extract numerical answer"]
ExtractAnswer --> VerifyAnswer["Score using exact match"]
VerifyAnswer --> UpdateCounters["If correct, increment correct counter"]
UpdateCounters --> LogResults["Log results if verbose_mode"]
LogResults --> LoopEnd["Continue to next problem"]
LoopEnd --> LoopStart
LoopStart --> |All problems processed| CalculateAccuracy["Calculate accuracy = correct/total"]
CalculateAccuracy --> StoreResults["Store predictions in DataFrame"]
StoreResults --> ReturnResult["Return DeepEvalBaseBenchmarkResult"]
ReturnResult --> End([Evaluation Complete])
```

The final accuracy score is computed as the ratio of correctly answered problems to the total number of problems evaluated.

**Diagram sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L45-L92)

**Section sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L45-L92)

## Common Challenges in Multi-Step Arithmetic Evaluation
The GSM8K benchmark faces several common challenges in evaluating multi-step arithmetic reasoning:

### Error Propagation in Multi-Step Calculations
Small errors in intermediate steps can cascade and lead to incorrect final answers. The current implementation does not provide partial credit for correct reasoning with minor calculation errors.

### Incorrect Unit Handling
Models may produce numerically correct answers but with incorrect units or formatting (e.g., including currency symbols when only the number is expected).

### Model Hallucinations in Arithmetic Operations
Large language models may fabricate arithmetic steps or invent mathematical operations that don't follow standard rules.

### Answer Format Inconsistencies
Variations in decimal precision, fraction representation, or scientific notation can cause valid answers to be marked as incorrect.

```mermaid
graph TD
A[Common Challenges] --> B[Error Propagation]
A --> C[Unit Handling]
A --> D[Model Hallucinations]
A --> E[Format Inconsistencies]
B --> B1[Single step error invalidates entire solution]
B --> B2[No partial credit system]
C --> C1[Including extraneous symbols]
C --> C2[Wrong decimal places]
D --> D1[Fabricated arithmetic rules]
D --> D2[Incorrect operation sequences]
E --> E1[Scientific vs decimal notation]
E --> E2[Fraction vs decimal representation]
```

**Section sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L106-L143)
- [template.py](file://deepeval/benchmarks/gsm8k/template.py#L50-L53)

## Best Practices for Chain-of-Thought Configuration
To maximize the effectiveness of GSM8K evaluations, consider the following best practices:

### Optimal Few-Shot Configuration
- Use 3-8 shot examples for optimal performance
- Ensure few-shot examples cover diverse problem types
- Balance between providing sufficient examples and avoiding prompt overload

### Chain-of-Thought Optimization
- Always enable CoT (`enable_cot=True`) for multi-step problems
- Consider using higher temperature settings to encourage exploration of solution paths
- Monitor for excessive verbosity in reasoning steps

### Model Configuration
- Use models with strong arithmetic capabilities
- Consider models specifically fine-tuned on mathematical reasoning
- Ensure sufficient context window to handle long reasoning chains

### Evaluation Parameters
- Set `n_problems` based on computational resources and required statistical significance
- Use `verbose_mode=True` during development to debug issues
- Validate results with a small subset before full evaluation

```mermaid
flowchart LR
A[Best Practices] --> B[Few-Shot Design]
A --> C[CoT Configuration]
A --> D[Model Selection]
A --> E[Evaluation Setup]
B --> B1[3-8 examples optimal]
B --> B2[Diverse problem coverage]
C --> C1[Enable CoT reasoning]
C --> C2[Monitor reasoning quality]
D --> D1[Strong math capabilities]
D --> D2[Consider fine-tuned models]
E --> E1[Appropriate n_problems]
E --> E2[Use verbose mode for debugging]
```

**Section sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L18-L43)

## Practical Example Implementation
Here is a practical example demonstrating how to evaluate a model on the GSM8K benchmark:

```python
from deepeval.benchmarks import GSM8K
from deepeval.models import DeepEvalBaseLLM

# Define a custom model wrapper
class Mistral7B(DeepEvalBaseLLM):
    def __init__(self):
        # Initialize your model here
        pass
        
    def generate(self, prompt: str) -> str:
        # Implement generation logic
        return "42"  # Example response
        
    def get_model_name(self):
        return "Mistral-7B"

# Configure and run GSM8K evaluation
benchmark = GSM8K(
    n_shots=3,
    enable_cot=True,
    n_problems=100,  # Evaluate on 100 problems
    verbose_mode=True
)

# Run evaluation
model = Mistral7B()
result = benchmark.evaluate(model)

# Access results
print(f"Accuracy: {result.overall_accuracy}")
print(f"Predictions: {benchmark.predictions}")
```

This example demonstrates the complete workflow from model definition to evaluation execution and result retrieval.

**Section sources**
- [gsm8k.py](file://deepeval/benchmarks/gsm8k/gsm8k.py#L15-L92)
- [benchmarks-gsm8k.mdx](file://docs/docs/benchmarks-gsm8k.mdx#L26-L32)