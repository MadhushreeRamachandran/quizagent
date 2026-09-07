from langchain.agents.middleware import wrap_model_call
from agents.quiz_agent import quiz_agent_tool
from agents.reviewer_agent import review_agent_tool
from agents.submit_answers_tool import submit_answers_tool
from agents.review_system_prompt import REVIEW_AGENT_PROMPT

STEP_CONFIG = {
    "quiz_agent": {
        "description": "Handle query — greet, explain or generate quiz",
        "tools":       [quiz_agent_tool],
        "requires":    [],
    },
    "review_agent": {
        "description": "Review MCQ answers and give feedback",
        "tools":       [review_agent_tool],
        "prompt":      REVIEW_AGENT_PROMPT,
        "requires":    ["questions", "answers"],
    },
}


@wrap_model_call  # type: ignore
async def apply_step_middleware(request, handler):

    current_step = request.state.get("current_step", "quiz_agent")

    if current_step not in STEP_CONFIG:
        print(f"[Middleware] Step: '{current_step}' → skipping")
        return await handler(request)

    config = STEP_CONFIG[current_step]
    print(f"[Middleware] Step: '{current_step}' → {config['description']}")

    for key in config["requires"]:
        if not request.state.get(key):
            raise ValueError(
                f"[Middleware] '{key}' must exist in state "
                f"before step '{current_step}'"
            )
    

    if current_step == "quiz_agent":
        request = request.override(
            tools=config["tools"],
    
            
        )

  
    elif current_step == "review_agent":
        request = request.override(
            tools=config["tools"],
            system_prompt=config["prompt"],  
        )

    return await handler(request)

