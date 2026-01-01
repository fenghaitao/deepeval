import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from openai import OpenAI


def get_chatbot_response(user_query: str, context: str) -> str:
    """
    Simulates a RAG chatbot that answers questions based on retrieved context.
    
    The LLM's role: Act as a customer service assistant that answers questions
    based ONLY on the provided context about return policies.
    """
    client = OpenAI()  # Requires OPENAI_API_KEY in environment
    
    # This is the system prompt that defines the LLM's behavior
    system_prompt = """You are a helpful customer service assistant for an e-commerce store.
Answer customer questions based ONLY on the provided context.
Be concise and friendly. If the context doesn't contain the answer, say so."""
    
    # Construct the user message with retrieved context (RAG pattern)
    user_message = f"""Context: {context}

Customer Question: {user_query}

Please answer the customer's question based on the context above."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    return response.choices[0].message.content


def test_case():
    """
    Test that the chatbot correctly answers return policy questions.
    
    When you run: deepeval test run test_chatbot.py
    
    What happens:
    1. The chatbot (get_chatbot_response) receives the input question
    2. It uses the retrieval_context to answer (simulating RAG)
    3. GEval metric uses an LLM to judge if actual_output matches expected_output
    4. Test passes if the correctness score >= 0.5 (threshold)
    """
    # Define the evaluation metric
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.5
    )
    
    # Test data
    input_query = "What if these shoes don't fit?"
    retrieval_context = ["All customers are eligible for a 30 day full refund at no extra costs."]
    expected_output = "We offer a 30-day full refund at no extra costs."
    
    # Get actual output from the LLM chatbot
    actual_output = get_chatbot_response(input_query, retrieval_context[0])
    
    print(f"\n{'='*60}")
    print(f"Input: {input_query}")
    print(f"Context: {retrieval_context[0]}")
    print(f"Actual Output: {actual_output}")
    print(f"Expected Output: {expected_output}")
    print(f"{'='*60}\n")
    
    # Create test case and evaluate
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        expected_output=expected_output,
        retrieval_context=retrieval_context
    )
    
    assert_test(test_case, [correctness_metric])
