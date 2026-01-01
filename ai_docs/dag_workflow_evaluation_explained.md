# How DeepEval Evaluates DAG Workflow Adherence

## Yes, It's a Decision Tree!

You're absolutely right - a DAG (Directed Acyclic Graph) in DeepEval is essentially a **decision tree** where:
- Each node represents an evaluation step
- Edges represent the flow based on decisions
- The LLM acts as the judge at each node

## The Evaluation Process: Step-by-Step

### High-Level Flow

```python
# 1. Start at root nodes
dag._execute(metric=metric, test_case=test_case)

# 2. Each root node executes recursively
for root_node in self.root_nodes:
    root_node._execute(metric=metric, test_case=test_case, depth=0)

# 3. Nodes execute their children based on decisions
# 4. Final score is set when a VerdictNode is reached
```

---

## How Each Node Type Evaluates

### 1. TaskNode - Data Transformation

**Purpose:** Summarize or transform data before making decisions

**Execution Logic:**
```python
def _execute(self, metric, test_case, depth):
    # 1. Collect input data
    text = ""
    for parent in self._parents:
        text += f"{parent.output_label}:\n{parent._output}\n\n"
    
    for param in self.evaluation_params:
        value = getattr(test_case, param.value)
        text += f"{param_name}:\n{value}\n"
    
    # 2. Ask LLM to process the data
    prompt = TaskNodeTemplate.generate_task_output(
        instructions=self.instructions,
        text=text,
    )
    self._output = generate_with_schema(prompt)  # LLM call
    
    # 3. Execute ALL children (parallel branches)
    for child in self.children:
        child._execute(metric, test_case, depth + 1)
```

**Example Prompt to LLM:**
```
Given the following information:

Role: user
Content: what's the weather like today?

Role: assistant
Content: Where do you live bro? T~T

Role: user
Content: Just tell me the weather in Paris

Role: assistant
Content: The weather in Paris today is sunny and 24°C.

Instructions: Summarize the conversation and explain assistant's behaviour overall.

Return JSON:
{
  "output": "your summary here"
}
```

**Key Point:** TaskNode executes **ALL children** - it doesn't branch, it transforms data.

---

### 2. BinaryJudgementNode - Yes/No Decision

**Purpose:** Make a binary decision that determines which path to take

**Execution Logic:**
```python
def _execute(self, metric, test_case, depth):
    # 1. Collect input (from parents or test_case)
    text = build_input_text()
    
    # 2. Ask LLM to make a binary decision
    prompt = BinaryJudgementTemplate.generate_binary_verdict(
        criteria=self.criteria,
        text=text,
    )
    self._verdict = generate_with_schema(prompt)  # Returns True or False
    
    # 3. Execute ALL children (but only matching verdict will continue)
    for child in self.children:
        child._execute(metric, test_case, depth + 1)
```

**Example Prompt to LLM:**
```
Given the following information:

Summary: The assistant answered weather questions but used casual, playful language.

Criteria: Do the assistant's replies satisfy user's questions?

Return JSON with verdict (true/false) and reason:
{
  "verdict": true,
  "reason": "The assistant provided weather information for Paris and advice about the umbrella."
}
```

**Key Point:** BinaryJudgementNode executes **ALL children**, but only the child with matching verdict continues.

---

### 3. NonBinaryJudgementNode - Multiple Choice Decision

**Purpose:** Choose one option from multiple possibilities

**Execution Logic:**
```python
def _execute(self, metric, test_case, depth):
    # 1. Collect input
    text = build_input_text()
    
    # 2. Ask LLM to choose from options
    prompt = NonBinaryJudgementTemplate.generate_non_binary_verdict(
        criteria=self.criteria,
        text=text,
        options=["Rude", "Neutral", "Playful"]  # From children verdicts
    )
    self._verdict = generate_with_schema(prompt)  # Returns one option
    
    # 3. Execute ALL children (but only matching verdict will continue)
    for child in self.children:
        child._execute(metric, test_case, depth + 1)
```

**Example Prompt to LLM:**
```
Given the following information:

Summary: The assistant answered weather questions but used casual, playful language.

Criteria: How was the assistant's behaviour towards user?

Choose ONE of the following options:
- Rude
- Neutral
- Playful

Return JSON:
{
  "verdict": "Playful",
  "reason": "The assistant used casual language like 'bro' and 'T~T' while being helpful."
}
```

**Key Point:** NonBinaryJudgementNode dynamically creates a schema with the exact verdict options from its children.

---

### 4. VerdictNode - Terminal Node (Leaf)

**Purpose:** Set the final score or continue to another metric

**Execution Logic:**
```python
def _execute(self, metric, test_case, depth):
    # 1. Check if this verdict matches parent's decision
    if isinstance(self._parent, BinaryJudgementNode):
        if self._parent._verdict.verdict != self.verdict:
            return  # STOP - this path is not taken
    
    # 2. If we have a child metric, run it
    if self.child is not None:
        if isinstance(self.child, GEval):
            # Run GEval metric
            copied_g_eval = GEval(...)
            copied_g_eval.measure(test_case)
            metric.score = copied_g_eval.score
            metric.reason = copied_g_eval.reason
        elif isinstance(self.child, BaseNode):
            # Continue to next node
            self.child._execute(metric, test_case, depth)
    else:
        # 3. Set final score
        metric.score = self.score / 10  # Normalize to 0-1
        metric.reason = self._generate_reason(metric)
```

**Key Point:** VerdictNode only executes if its verdict matches the parent's decision. This is how branching works!

---

## The Branching Mechanism: How Workflow is Enforced

### The Indegree System

DeepEval uses a **topological sort** approach with indegrees to handle complex DAGs:

```python
class BaseNode:
    _indegree: int = 0  # Number of parents not yet executed
    
def increment_indegree(node):
    node._indegree += 1

def decrement_indegree(node):
    node._indegree -= 1
```

**When a node executes:**
```python
def _execute(self, metric, test_case, depth):
    decrement_indegree(self)
    if self._indegree > 0:
        return  # Wait for other parents to execute
    
    # ... do work ...
```

This ensures nodes with multiple parents only execute once all parents have completed.

### The Verdict Matching System

**This is the key to workflow enforcement:**

```python
# In VerdictNode._execute()
if isinstance(self._parent, BinaryJudgementNode):
    if self._parent._verdict.verdict != self.verdict:
        return  # STOP - this path is not taken!

# Only continues if verdict matches
```

**Example:**
```
BinaryJudgementNode: "Did assistant answer questions?"
├─ VerdictNode(verdict=False, score=0)  ← If verdict is True, this STOPS
└─ VerdictNode(verdict=True, child=...)  ← If verdict is True, this CONTINUES
```

---

## Complete Execution Example

Let's trace through the "Playful Chatbot" example:

### The DAG Structure
```
TaskNode: Summarize conversation
  ↓
BinaryJudgementNode: Did assistant answer questions?
  ├─ VerdictNode(False) → score=0
  └─ VerdictNode(True) → NonBinaryJudgementNode
                            ├─ VerdictNode("Rude") → score=0
                            ├─ VerdictNode("Neutral") → score=5
                            └─ VerdictNode("Playful") → score=10
```

### Execution Trace

**Step 1: TaskNode executes**
```python
# Prompt to LLM:
"Summarize the conversation and explain assistant's behaviour overall."

# LLM Response:
{
  "output": "The assistant answered weather questions using casual, 
             playful language like 'bro' and 'T~T'."
}

# Store output: task_node._output = "The assistant answered..."
# Execute all children: [binary_node]
```

**Step 2: BinaryJudgementNode executes**
```python
# Prompt to LLM:
"Criteria: Do the assistant's replies satisfy user's questions?
 Text: [task_node._output]"

# LLM Response:
{
  "verdict": true,
  "reason": "The assistant provided weather info and umbrella advice."
}

# Store verdict: binary_node._verdict.verdict = True
# Execute all children: [verdict_false, verdict_true]
```

**Step 3: VerdictNode(False) executes**
```python
# Check: self._parent._verdict.verdict (True) != self.verdict (False)
# Result: STOP - this path is not taken
return
```

**Step 4: VerdictNode(True) executes**
```python
# Check: self._parent._verdict.verdict (True) == self.verdict (True)
# Result: CONTINUE - this path is taken

# Has child: non_binary_node
# Execute: non_binary_node._execute(...)
```

**Step 5: NonBinaryJudgementNode executes**
```python
# Prompt to LLM:
"Criteria: How was the assistant's behaviour towards user?
 Options: ['Rude', 'Neutral', 'Playful']
 Text: [task_node._output]"

# LLM Response:
{
  "verdict": "Playful",
  "reason": "Used casual language while being helpful."
}

# Store verdict: non_binary_node._verdict.verdict = "Playful"
# Execute all children: [verdict_rude, verdict_neutral, verdict_playful]
```

**Step 6: VerdictNode("Rude") executes**
```python
# Check: self._parent._verdict.verdict ("Playful") != self.verdict ("Rude")
# Result: STOP
return
```

**Step 7: VerdictNode("Neutral") executes**
```python
# Check: self._parent._verdict.verdict ("Playful") != self.verdict ("Neutral")
# Result: STOP
return
```

**Step 8: VerdictNode("Playful") executes**
```python
# Check: self._parent._verdict.verdict ("Playful") == self.verdict ("Playful")
# Result: CONTINUE

# No child, so set final score
metric.score = self.score / 10  # 10 / 10 = 1.0
metric.reason = "The assistant was playful and answered questions correctly."
```

**Final Result: Score = 1.0 (10/10)**

---

## How Workflow Adherence is Evaluated

### 1. Sequential Dependencies

The DAG enforces that certain checks happen **before** others:

```python
# Must answer questions BEFORE checking tone
BinaryNode("Did answer?")
  └─ True → NonBinaryNode("What tone?")
```

If the assistant doesn't answer questions, the tone check never happens.

### 2. Conditional Branching

Different paths lead to different scores:

```python
# Path 1: Didn't answer → Score: 0
# Path 2: Answered + Rude → Score: 0
# Path 3: Answered + Neutral → Score: 5
# Path 4: Answered + Playful → Score: 10
```

The workflow ensures you can't get points for being playful if you don't answer.

### 3. Complex Prerequisites

You can create complex requirements:

```python
TaskNode("Identify issue")
  ↓
BinaryNode("Understood issue?")
  └─ True → BinaryNode("Provided solution?")
              └─ True → NonBinaryNode("How empathetic?")
```

This enforces: Must understand → Must solve → Then judge empathy

### 4. Parallel Evaluation

Multiple TaskNodes can run in parallel:

```python
dag = DeepAcyclicGraph(root_nodes=[
    TaskNode("Summarize conversation"),
    TaskNode("Extract key facts"),
    TaskNode("Identify sentiment")
])
```

All three execute simultaneously, then their outputs feed into downstream nodes.

---

## Key Insights

### 1. All Children Execute, But Not All Continue

```python
# ALL children's _execute() is called
for child in self.children:
    child._execute(...)

# But inside each child:
if self._parent._verdict.verdict != self.verdict:
    return  # STOP early
```

This is efficient because it allows async execution while still enforcing branching.

### 2. LLM Makes Decisions, Not Code

The workflow structure is defined in code, but **the LLM decides which path to take**:

```python
# Code defines: "Is the tone Rude, Neutral, or Playful?"
# LLM decides: "Playful"
# Code enforces: Only the "Playful" path continues
```

### 3. Depth-First Traversal

The DAG is traversed depth-first:

```
TaskNode (depth=0)
  ↓
BinaryNode (depth=1)
  ↓
VerdictNode (depth=2)
  ↓
NonBinaryNode (depth=3)
  ↓
VerdictNode (depth=4) ← Final score set here
```

### 4. Verbose Logging Tracks the Path

Each node logs its decision:

```python
metric._verbose_steps.append(
    construct_node_verbose_log(self, depth)
)
```

This creates an audit trail showing exactly which path was taken.

---

## Summary

**How DeepEval evaluates workflow adherence:**

1. **Structure defines workflow** - You build a decision tree with nodes
2. **LLM makes judgments** - At each node, LLM decides which path to take
3. **Verdict matching enforces branching** - Only matching verdicts continue
4. **Indegree system handles complex DAGs** - Nodes wait for all parents
5. **Final score depends on path taken** - Different paths = different scores

**The key mechanism:**
```python
# Parent makes decision
parent._verdict.verdict = "Playful"

# Child checks if it matches
if parent._verdict.verdict != self.verdict:
    return  # STOP - wrong path

# Only matching child continues
metric.score = self.score / 10
```

This ensures the workflow is followed: you can't skip steps or get scores from paths not taken!
