# MIPROv2 Algorithm

<cite>
**Referenced Files in This Document**   
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py)
- [proposer.py](file://deepeval/optimizer/algorithms/miprov2/proposer.py)
- [bootstrapper.py](file://deepeval/optimizer/algorithms/miprov2/bootstrapper.py)
- [configs.py](file://deepeval/optimizer/algorithms/configs.py)
- [base.py](file://deepeval/optimizer/algorithms/base.py)
- [types.py](file://deepeval/optimizer/types.py)
- [scorer/base.py](file://deepeval/optimizer/scorer/base.py)
- [utils.py](file://deepeval/optimizer/utils.py)
- [prompt_optimizer.py](file://deepeval/optimizer/prompt_optimizer.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Core Components](#core-components)
3. [Architecture Overview](#architecture-overview)
4. [Detailed Component Analysis](#detailed-component-analysis)
5. [Dependency Analysis](#dependency-analysis)
6. [Performance Considerations](#performance-considerations)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Conclusion](#conclusion)

## Introduction
The MIPROv2 (Multiprompt Instruction PRoposal Optimizer Version 2) algorithm is a sophisticated prompt optimization framework that combines intelligent instruction proposal with few-shot demonstration bootstrapping, using Bayesian Optimization to find optimal prompt configurations. Based on the original MIPROv2 paper and DSPy implementation, this algorithm systematically searches the joint space of instruction candidates and demonstration sets to maximize prompt effectiveness. The implementation follows a two-phase approach: first generating diverse instruction candidates and bootstrapped demonstration sets, then using Optuna's TPE sampler for Bayesian Optimization over the combined space. This approach enables efficient exploration of the prompt space while balancing computational cost with optimization quality.

## Core Components

The MIPROv2 algorithm consists of three core components: the MIPROV2 class that orchestrates the optimization process, the InstructionProposer that generates diverse instruction candidates, and the DemoBootstrapper that creates effective demonstration sets. These components work together to implement the two-phase optimization strategy, with the MIPROV2 class managing the overall workflow, the proposer ensuring diversity in instruction generation, and the bootstrapper creating high-quality few-shot examples. The algorithm integrates with the scoring system through the BaseScorer interface, enabling evaluation of prompt effectiveness across various metrics.

**Section sources**
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L91-L753)
- [proposer.py](file://deepeval/optimizer/algorithms/miprov2/proposer.py#L41-L302)
- [bootstrapper.py](file://deepeval/optimizer/algorithms/miprov2/bootstrapper.py#L71-L436)

## Architecture Overview

```mermaid
graph TD
A[MIPROV2 Algorithm] --> B[Phase 1: Proposal]
A --> C[Phase 2: Optimization]
B --> D[Instruction Proposer]
B --> E[Demo Bootstrapper]
D --> F[Generate N diverse instruction candidates]
E --> G[Bootstrap M demo sets from training data]
C --> H[Bayesian Optimization]
H --> I[TPE Sampler]
I --> J[Sample instruction index]
I --> K[Sample demo set index]
J --> L[Get instruction candidate]
K --> M[Get demo set]
L --> N[Render prompt with demos]
M --> N
N --> O[Evaluate on minibatch]
O --> P[Update surrogate model]
P --> Q{Periodic full evaluation?}
Q --> |Yes| R[Full evaluation on best combination]
Q --> |No| S{Trials complete?}
R --> S
S --> |No| H
S --> |Yes| T[Return optimized prompt]
```

**Diagram sources **
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L91-L753)
- [proposer.py](file://deepeval/optimizer/algorithms/miprov2/proposer.py#L41-L302)
- [bootstrapper.py](file://deepeval/optimizer/algorithms/miprov2/bootstrapper.py#L71-L436)

## Detailed Component Analysis

### MIPROV2 Class Analysis
The MIPROV2 class implements the core optimization algorithm, following a two-phase approach. In the proposal phase, it generates diverse instruction candidates using the InstructionProposer and bootstraps demonstration sets using the DemoBootstrapper. In the optimization phase, it employs Bayesian Optimization via Optuna's TPE sampler to search the joint space of (instruction candidate, demo set) combinations. The algorithm maintains state through various data structures including instruction_candidates, demo_sets, and combination_scores, tracking performance across trials. It supports both synchronous and asynchronous execution through execute() and a_execute() methods, with the asynchronous version enabling concurrent proposal and bootstrapping.

**Section sources**
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L91-L753)

### Instruction Proposer Analysis
The InstructionProposer generates diverse instruction candidates by leveraging different "tips" to encourage variation in the generated prompts. It uses a predefined list of 15 tips such as "Be creative and think outside the box" and "Use step-by-step reasoning" to guide the generation process. For each candidate, it composes a specialized prompt that includes the current prompt, example inputs/outputs from goldens, and a specific tip. The proposer ensures diversity by selecting different tips for each candidate and includes mechanisms to avoid duplicates through text comparison and similarity checking. It supports both synchronous and asynchronous generation, with the asynchronous version enabling concurrent candidate generation.

```mermaid
classDiagram
class InstructionProposer {
+optimizer_model : DeepEvalBaseLLM
+random_state : Random
+propose(prompt, goldens, num_candidates) List[Prompt]
+a_propose(prompt, goldens, num_candidates) List[Prompt]
-_format_prompt(prompt) str
-_format_examples(goldens, max_examples) str
-_compose_proposer_prompt(current_prompt, goldens, tip, candidate_index) str
-_select_tips(count) List[str]
-_normalize_output(output) str
-_create_prompt_from_text(original, new_text) Prompt
-_is_duplicate(new_prompt, existing) bool
-_get_prompt_text(prompt) str
}
InstructionProposer --> DeepEvalBaseLLM : "uses"
InstructionProposer --> Prompt : "generates"
InstructionProposer --> Golden : "uses examples from"
```

**Diagram sources **
- [proposer.py](file://deepeval/optimizer/algorithms/miprov2/proposer.py#L41-L302)

### Demo Bootstrapper Analysis
The DemoBootstrapper creates multiple demonstration sets by running the prompt on training examples and collecting successful outputs. Each demo set can contain both bootstrapped demos (model-generated outputs that passed validation) and labeled demos (taken directly from expected_output in goldens). The bootstrapper implements a success check that validates outputs based on non-emptiness and word overlap with expected outputs (minimum 30% overlap). It creates diverse demo sets by randomly sampling from available demos and always includes a 0-shot option (empty demo set) to allow the optimizer to determine whether few-shot examples improve performance. The bootstrapper supports both synchronous and asynchronous operation, with the asynchronous version enabling concurrent generation of multiple demos.

```mermaid
classDiagram
class DemoBootstrapper {
+max_bootstrapped_demos : int
+max_labeled_demos : int
+num_demo_sets : int
+random_state : Random
+bootstrap(prompt, goldens, generate_fn) List[DemoSet]
+a_bootstrap(prompt, goldens, a_generate_fn) List[DemoSet]
-_extract_input(golden) str
-_extract_expected_output(golden) Optional[str]
-_is_successful(actual_output, expected_output) bool
-_create_demo_sets(bootstrapped_demos, labeled_demos) List[DemoSet]
}
class DemoSet {
+demos : List[Demo]
+id : str
+to_text(max_demos) str
}
class Demo {
+input_text : str
+output_text : str
+golden_index : int
}
DemoBootstrapper --> DemoSet : "creates"
DemoSet --> Demo : "contains"
DemoBootstrapper --> Prompt : "uses"
DemoBootstrapper --> Golden : "samples from"
```

**Diagram sources **
- [bootstrapper.py](file://deepeval/optimizer/algorithms/miprov2/bootstrapper.py#L71-L436)

### Optimization Process Analysis
The optimization process in MIPROv2 follows a systematic approach to find the best prompt configuration. During the Bayesian Optimization phase, each trial samples an instruction index and demo set index using Optuna's TPE sampler, renders the prompt with the selected demos, and evaluates it on a minibatch of goldens. The algorithm tracks scores for each combination and periodically performs full evaluations on the best combination to obtain accurate performance estimates. The optimization balances exploration (trying new combinations) and exploitation (focusing on promising regions) through the TPE sampler's probabilistic modeling of good vs. bad parameter values. The process concludes by returning the optimized prompt with the best instruction and demonstration set rendered inline.

```mermaid
sequenceDiagram
participant MIPROV2 as MIPROV2 Algorithm
participant Proposer as InstructionProposer
participant Bootstrapper as DemoBootstrapper
participant Optuna as Optuna TPE Sampler
participant Scorer as BaseScorer
MIPROV2->>Proposer : propose(prompt, goldens, num_candidates)
Proposer-->>MIPROV2 : instruction_candidates
MIPROV2->>Bootstrapper : bootstrap(prompt, goldens, generate_fn)
Bootstrapper-->>MIPROV2 : demo_sets
loop num_trials times
MIPROV2->>Optuna : ask() for trial
Optuna-->>MIPROV2 : trial with sampled parameters
MIPROV2->>MIPROV2 : get instruction candidate
MIPROV2->>MIPROV2 : get demo set
MIPROV2->>MIPROV2 : render prompt with demos
MIPROV2->>Scorer : score_minibatch(rendered_config, minibatch)
Scorer-->>MIPROV2 : score
MIPROV2->>Optuna : tell(trial, score)
alt periodic full evaluation
MIPROV2->>Scorer : score_pareto(best_config, goldens)
Scorer-->>MIPROV2 : full_scores
end
end
MIPROV2->>MIPROV2 : identify best combination
MIPROV2->>MIPROV2 : return optimized prompt
```

**Diagram sources **
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L463-L633)
- [proposer.py](file://deepeval/optimizer/algorithms/miprov2/proposer.py#L136-L178)
- [bootstrapper.py](file://deepeval/optimizer/algorithms/miprov2/bootstrapper.py#L170-L251)

## Dependency Analysis

```mermaid
graph TD
A[MIPROV2] --> B[InstructionProposer]
A --> C[DemoBootstrapper]
A --> D[Optuna]
A --> E[BaseScorer]
A --> F[PromptConfiguration]
B --> G[DeepEvalBaseLLM]
B --> H[Prompt]
B --> I[Golden]
C --> H
C --> I
C --> J[DemoSet]
D --> K[TPESampler]
E --> L[BaseMetric]
F --> M[uuid]
A -.-> N[PromptOptimizer]
N --> A
N --> O[Scorer]
O --> P[ModelCallback]
style A fill:#f9f,stroke:#333
style N fill:#bbf,stroke:#333
```

**Diagram sources **
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L91-L753)
- [prompt_optimizer.py](file://deepeval/optimizer/prompt_optimizer.py#L53-L264)
- [scorer/base.py](file://deepeval/optimizer/scorer/base.py#L10-L87)

**Section sources**
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L91-L753)
- [prompt_optimizer.py](file://deepeval/optimizer/prompt_optimizer.py#L53-L264)
- [base.py](file://deepeval/optimizer/algorithms/base.py#L10-L30)

## Performance Considerations
The MIPROv2 algorithm involves significant API call volume due to its iterative evaluation process. Each optimization trial requires API calls for prompt generation and scoring, with the total number of calls scaling with num_trials and minibatch_size. To manage costs and latency, the algorithm uses minibatch sampling for most evaluations, only performing full dataset evaluations periodically. The default configuration (20 trials with 25 examples each) results in 500 evaluation calls during the optimization phase, plus additional calls for instruction proposal and demo bootstrapping. Users should configure iteration limits based on their budget and performance requirements, with higher num_trials providing more thorough search but increased costs. The algorithm's asynchronous capabilities can help reduce wall-clock time by enabling concurrent operations.

**Section sources**
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L133-L177)
- [configs.py](file://deepeval/optimizer/algorithms/configs.py#L9-L15)

## Troubleshooting Guide
Common issues with MIPROv2 include getting stuck in local optima, excessive API costs, and suboptimal results. To address local optima, users can increase the mutation pool size by raising num_candidates or num_demo_sets to explore a broader search space. Adjusting the temperature parameter of the optimizer model can also increase diversity in instruction generation. For API cost concerns, reducing minibatch_size or num_trials can lower costs, though this may impact optimization quality. If the algorithm fails to improve over the baseline, verifying the quality of goldens and ensuring the scorer metrics align with desired outcomes is recommended. The random_seed parameter can be set to ensure reproducible results during debugging. Users should also ensure optuna is installed, as MIPROv2 depends on it for Bayesian Optimization.

**Section sources**
- [miprov2.py](file://deepeval/optimizer/algorithms/miprov2/miprov2.py#L146-L150)
- [prompt_optimizer.py](file://deepeval/optimizer/prompt_optimizer.py#L53-L264)
- [docs/docs/prompt-optimization-miprov2.mdx](file://docs/docs/prompt-optimization-miprov2.mdx#L1-L194)

## Conclusion
The MIPROv2 algorithm provides a comprehensive framework for prompt optimization that effectively balances exploration and exploitation in the prompt space. By combining diverse instruction proposal, demonstration bootstrapping, and Bayesian Optimization, it offers a systematic approach to finding optimal prompt configurations. The algorithm's modular design separates concerns between candidate generation, demonstration creation, and optimization strategy, enabling flexible configuration and extension. Its integration with the DeepEval ecosystem allows seamless use with various metrics and models, making it a powerful tool for improving LLM performance across diverse tasks. The implementation demonstrates careful consideration of practical concerns including computational efficiency, reproducibility, and user configurability.