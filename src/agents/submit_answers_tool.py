from langgraph.types import interrupt
from langchain_core.tools import tool


@tool
def submit_answers_tool(questions: list[dict]) -> list[str]:
    """
     wait for the user to submit their answers.
    Call this tool after quiz questions are generated.
    Arguments:
    questions: The list of generated MCQ question dicts
    Returns the list of user answers (A/B/C/D).
    """
    answers = interrupt({
        "action": "collect_answers",
        "questions": questions
    })
    return answers