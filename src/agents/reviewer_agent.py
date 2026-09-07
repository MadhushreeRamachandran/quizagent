import json
import boto3
from langchain_core.tools import tool
from config.config import *
from agents.review_system_prompt import REVIEW_AGENT_PROMPT
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

@tool
def review_agent_tool(questions: list[dict], answers: list[str]) -> dict:
    """
    Evaluate MCQ answers and return detailed feedback.
    The arguments are:
        questions: List of MCQ question dicts with options and correct_answer
        answers: List of user selected answers (A/B/C/D) per question
    Return a Dictionary with score, grade, percentage, per-question feedback and summary
    """
    try:

        qa_pairs = "\n\n".join([
            f"Q{i+1}: {q['question']}\n"
            f"  A: {q['options']['A']}\n"
            f"  B: {q['options']['B']}\n"
            f"  C: {q['options']['C']}\n"
            f"  D: {q['options']['D']}\n"
            f"Correct Answer: {q['correct_answer']}\n"
            f"User Answer: {answers[i] if i < len(answers) else 'No answer'}"
            for i, q in enumerate(questions)
        ])
        
        print(qa_pairs)
        final_prompt = f"""
        {REVIEW_AGENT_PROMPT}

        QUESTIONS AND ANSWERS:
        {qa_pairs}"""

        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": final_prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 4096,
                    "temperature": 0.3,
                }
            })
        )

        body     = json.loads(response["body"].read())
        raw_text = body["output"]["message"]["content"][0]["text"].strip()

        print("")
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        result = json.loads(raw_text.strip())
        return result

    except Exception as e:
        
        raise Exception("Error in reviewer agent")