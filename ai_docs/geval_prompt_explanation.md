# How GEval Evaluates Your Test Case

## The Two-Step Process

GEval makes **two LLM calls** to GPT-4.1:

### Step 1: Generate Evaluation Steps (if not provided)

**Prompt sent to GPT-4.1:**
```
Given an evaluation criteria which outlines how you should judge the Actual Output and Expected Output, 
generate 3-4 concise evaluation steps based on the criteria below. You MUST make it clear how to evaluate 
Actual Output and Expected Output in relation to one another.

Evaluation Criteria:
Determine if the 'actual output' is correct based on the 'expected output'.

**
IMPORTANT: Please make sure to only return in JSON format, with the "steps" key as a list of strings. 
No words or explanation is needed.
Example JSON:
{
    "steps": <list_of_strings>
}
**

JSON:
```

**GPT-4.1 generates steps like:**
```json
{
  "steps": [
    "Compare the actual output with the expected output for semantic similarity",
    "Check if all key information from expected output is present in actual output",
    "Verify that no contradictory information exists in the actual output"
  ]
}
```

---

### Step 2: Evaluate the Test Case

**Prompt sent to GPT-4.1:**
```
You are an evaluator. Given the following evaluation steps, assess the response below and return a JSON 
object with two fields:

- `"score"`: an integer between 0 and 10, with 10 indicating strong alignment with the evaluation steps 
  and 0 indicating no alignment.
- `"reason"`: a brief explanation for why the score was given. This must mention specific strengths or 
  shortcomings, referencing relevant details from the input. Do **not** quote the score itself in the 
  explanation.

Your explanation should:
- Be specific and grounded in the evaluation steps.
- Mention key details from the test case parameters.
- Be concise, clear, and focused on the evaluation logic.

Only return valid JSON. Do **not** include any extra commentary or text.

---

Evaluation Steps:
1. Compare the actual output with the expected output for semantic similarity
2. Check if all key information from expected output is present in actual output
3. Verify that no contradictory information exists in the actual output

Test Case:
Actual Output:
You have 30 days to get a full refund at no extra cost.

Expected Output:
We offer a 30-day full refund at no extra costs.

Parameters:
Actual Output and Expected Output

---
**Example JSON:**
{
    "reason": "your concise and informative reason here",
    "score": 0
}

JSON:
```

**GPT-4.1 responds with:**
```json
{
  "reason": "The actual output conveys all the key information from the expected output: a 30-day full 
            refund at no extra cost. While the wording is different and the actual output adds a condition 
            about shoes not fitting, it does not omit any required details. There are no significant 
            discrepancies or missing elements.",
  "score": 9
}
```

---

## Score Normalization

The raw score (9) is then normalized to 0-1 range:
```
normalized_score = (9 - 0) / (10 - 0) = 0.9
```

This 0.9 is compared against your threshold (0.5), and since 0.9 >= 0.5, the test **PASSES**.

---

## Key Insights

1. **GPT-4.1 acts as the judge** - It evaluates semantic similarity, not exact string matching
2. **The criteria you provide** becomes the evaluation logic
3. **Evaluation steps** break down how to judge the outputs
4. **The test case parameters** (actual_output, expected_output) are inserted into the prompt
5. **GPT-4.1 explains its reasoning** - This is why you see the detailed reason in the test results

This is why GEval is so powerful - it uses LLM intelligence to evaluate LLM outputs based on your custom criteria!
