import boto3
import os
from langchain_aws import ChatBedrock
import re


def get_bedrock_client():
    try:

        return boto3.client(
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            service_name="bedrock-runtime",
        )
    except:
        raise Exception("Creation of client get failed")


def get_llm(max_tokens=500, temperature=0):
    try:

        return ChatBedrock(
            client=get_bedrock_client(),
            model="arn:aws:bedrock:us-east-1:451433485314:application-inference-profile/eyhgqon7j4gk",
            provider="amazon",
            model_kwargs={"max_tokens": max_tokens, "temperature": temperature},
        )
    except:
        raise Exception("LLM creation failed")


def strip_thinking(text: str) -> str:
    try:

        text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
        return text.strip()
    except:
        raise Exception("stripping of thinking tag failed")
    



def parse_review_text(raw_review: str):
    try:

        feedback = {}
        summary = ""
        improvement_areas = []

    
        text = raw_review.strip()

        feedback_matches = re.findall(
            r"\*\*Feedback:\*\*\s*(.+?)(?=\n###|\n\*\*|\Z)",
            text,
            re.DOTALL
        )

        for i, fb in enumerate(feedback_matches, start=1):
            feedback[f"Q{i}"] = fb.strip()

    
        summary_match = re.search(
        r"\*\*Summary:\*\*\s*(.+?)(?=\n- \*\*|\n###|\Z)",
        text,
        re.DOTALL
    )
        

        if summary_match:
            summary = summary_match.group(1).strip()
        else:
         
            fallback = re.search(r"Summary:\s*(.+)", text)
            if fallback:
                summary = fallback.group(1).strip()

    
        improvement_match = re.search(
            r"\*\*Areas for Improvement:\*\*\s*(.+)",
            text,
            re.DOTALL
        )

        if improvement_match:
            areas_text = improvement_match.group(1)

            parts = re.split(r"\.\s+|\n", areas_text)

            improvement_areas = [
                p.strip(" -*") for p in parts if p.strip()
            ]

    
        if not feedback:
            lines = text.split("\n")
            q_count = 1
            for line in lines:
                if "Feedback:" in line:
                    feedback[f"Q{q_count}"] = line.split("Feedback:")[-1].strip()
                    q_count += 1

        return {
            "Feedback": feedback,
            "summary": summary,
            "improvement_areas": improvement_areas,
        }
    except:
        raise Exception("parsing failed")