import json
import boto3
from langchain_core.tools import tool
from config.config import *
from agents.quiz_system_prompt import QUIZ_AGENT_PROMPT

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

@tool
def quiz_agent_tool(query: str, num_questions: int, difficulty: str) -> list[dict]:
    """
    Generate MCQ quiz questions on a given topic.
    Use the details from request
        topic: The subject to generate questions about
        num_questions: How many questions to generate
        difficulty: Difficulty level - easy, medium, or hard

    provide a list of MCQ question dicts with options and correct answer
    """
   
    try:
        prompt=f"""{QUIZ_AGENT_PROMPT}
        Topic:{query}
        Number of questions: {num_questions}
        Difficulty:{difficulty}
        Generate exactly the gicen number of questions """
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 2048,
                    "temperature": 0.7,
                }
            })
        )

        body     = json.loads(response["body"].read())
        raw_text = body["output"]["message"]["content"][0]["text"].strip()


        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        questions = json.loads(raw_text.strip())
        return questions[:num_questions]


   
    except Exception as e:
        raise Exception("Error in quiz agent")