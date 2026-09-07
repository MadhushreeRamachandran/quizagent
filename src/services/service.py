import json
import uuid
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from models.model import *
from agents.quiz_agent import quiz_agent_tool
from agents.reviewer_agent import review_agent_tool
from middlewares.step_middleware import apply_step_middleware
from config.config import *
from utilities.utils import *
from repositories.repo import Repository
from agents.main_agent_prompt import MAIN_AGENT_PROMPT
from langchain_core.runnables import RunnableConfig

class QuizService:

    def __init__(self, repo: Repository):
        self.repo = repo

    async def run_quiz_pipeline(self, request: QuizRequest) -> QuizResponse:
        try:

            user_id = str(uuid.uuid4())
            thread_id = user_id
            state: QuizState = {
                "query": request.query,
                "num_questions": request.num_questions or 0,
                "difficulty":    request.difficulty    or "",
                "current_step":  "quiz_agent",
                "questions":None,
                "answers": None,
                "review_result": None,
            } # type: ignore

        
            llm = get_llm()

            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )

            conn_string = (
                f"postgresql://"
                f"{DB_USER}:{DB_PASSWORD}"
                f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )

        
            async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                await checkpointer.setup()
                print("Checkpointer ready\n")

                agent = create_agent(
                    model=llm,
                    tools=[quiz_agent_tool, review_agent_tool],
                    middleware=[apply_step_middleware],  # type: ignore
                    checkpointer=checkpointer,
                    system_prompt=MAIN_AGENT_PROMPT,     
                )

            
                print(f"\nProcessing query: '{state['query']}'\n")

                quiz_result = await agent.ainvoke(
                    {
                        "current_step":  "quiz_agent",
                        "query":         state["query"],
                        "num_questions": state["num_questions"],
                        "difficulty":    state["difficulty"],
                        "questions": [],
                        "answers": [],
                        "review_result": {},
                        "messages": [
                            {
                                "role":    "user",
                                "content":(f"{state["query"]} | ",
                                        f"num_questions={state['num_questions']} |"
                                        f" difficulty={state['difficulty']}"  
                                )

                            }
                        ],
                    }, # type: ignore
                    config=config,
                )

                all_messages = quiz_result.get("messages", [])

                print("=== ALL MESSAGES ===")
                for i, msg in enumerate(all_messages):
                    content = msg.content if hasattr(msg, "content") else str(msg)
                    print(f"[{i}] {type(msg).__name__}: {str(content)[:120]}")
                print("\n")

            
                questions = []
                is_quiz   = False

                for msg in reversed(all_messages):
                    content = msg.content if hasattr(msg, "content") else str(msg)

                    
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") if isinstance(c, dict) else str(c)
                            for c in content
                        )

                    content = strip_thinking(str(content)).strip()

                
                    clean = content
                    if "```" in clean:
                        clean = clean.split("```")[1]
                        if clean.startswith("json"):
                            clean = clean[4:]
                    clean = clean.strip()


                    if clean.startswith("["):
                        try:
                            parsed = json.loads(clean)
                            if (
                                isinstance(parsed, list)
                                and len(parsed) > 0
                                and isinstance(parsed[0], dict)
                                and "question" in parsed[0]
                                and "options"  in parsed[0]
                            ):
                                questions = parsed
                                is_quiz   = True
                                print(f"Quiz JSON found in "
                                    f"{type(msg).__name__}\n")
                                break
                        except (json.JSONDecodeError, ValueError):
                            continue

                print(f"checking ... is_quiz={is_quiz}, questions={len(questions)}\n")

            
                raw = strip_thinking(
                    str(all_messages[-1].content)
                    if hasattr(all_messages[-1], "content")
                    else str(all_messages[-1])
                ).strip()

            
                if not is_quiz:
                    print("Non-quiz response — returning message directly\n")
                    return QuizResponse(
                        query=             state["query"],  # type: ignore
                        difficulty=        state["difficulty"],
                        total_questions=   0,
                        score=  "N/A",
                        grade=             "N/A",
                        percentage=        0.0,
                        feedback=          [],
                        summary=           raw,
                        improvement_areas= [],
                    )

                
                state["questions"] = questions
                print(f"Questions generated: {len(questions)}\n")

            
                print("=" * 55)
                print("QUIZ TIME — Select the correct option (A/B/C/D)")
                print("=" * 55)

                answers = []
                for i, question in enumerate(state["questions"]):
                    print(f"\nQ{i + 1}: {question['question']}")
                    print(f"  A) {question['options']['A']}")
                    print(f"  B) {question['options']['B']}")
                    print(f"  C) {question['options']['C']}")
                    print(f"  D) {question['options']['D']}")

                    while True:
                        answer = input("Your Answer (A/B/C/D): ").strip().upper()
                        if answer in ["A", "B", "C", "D"]:
                            answers.append(answer)
                            break
                        else:
                            print("Invalid. Please enter A, B, C or D only.")

                state["answers"]      = answers
                state["current_step"] = "review_agent"
                print("\n All answers collected.\n")

                print(" Reviewing your answers...\n")

                review_result_raw = await agent.ainvoke(
                    {
                        "current_step":  "review_agent",
                        "query":  state["query"],
                        "num_questions": state["num_questions"],
                        "difficulty":  state["difficulty"],
                        "questions": state["questions"],
                        "answers": state["answers"],
                        "review_result": {},
                        "messages": [
                            {
                                "role":    "user",
                                "content": (
                                    f"Review these MCQ questions: {state['questions']} "
                                    f"and user answers: {answers}. "
                                    f"Provide per-question feedback, score, grade, "
                                    f"percentage, summary and improvement areas."
                                ),
                            }
                        ],
                    }, # type: ignore
                    config=config,
                )
                print("step==",state["current_step"])

                print("whole output: ", review_result_raw)



                raw_review = review_result_raw["messages"][-1].content
               
                raw_review = strip_thinking(raw_review)
                print("type:", type(raw_review))
                print(" RAW REVIEW OUTPUT:\n", raw_review, "\n")
            
                


                if "```" in raw_review:
                    raw_review = raw_review.split("```")[1]
                    if raw_review.startswith("json"):
                        raw_review = raw_review[4:]
                raw_review = raw_review.strip()

                

                

                
                review_result = {}
                try:
                        review_result = json.loads(raw_review)
                        print("yes json")
                except json.JSONDecodeError:
                        
                        review_result = parse_review_text(raw_review)
                
                    
                    

                print("review json: ", review_result)
                total  = len(state["questions"])
                correct_count = sum(
                    1
                    for i, q in enumerate(state["questions"])
                    if i < len(answers)
                    and answers[i].upper() == q.get("correct_answer", "").upper()
                )
                percentage = round((correct_count / total) * 100, 2) if total > 0 else 0.0

                def get_grade(pct: float) -> str:
                    if pct >= 90: return "A"
                    elif pct >= 80: return "B"
                    elif pct >= 70: return "C"
                    elif pct >= 60: return "D"
                    else:  return "Fail"

            
                if (
                    "per_question_feedback" in raw_review
                    or "Feedback"  in review_result
                ):
                    per_q         = review_result["Feedback"]
                    
                    print("reviews: ",per_q)
                    feedback_list = []
                    for i, (key, explanation) in enumerate(per_q.items()):
                        q = state["questions"][i] if i < len(state["questions"]) else {}
                        feedback_list.append({
                            "question_number": i + 1,
                            "question": q.get("question", ""),
                            "options": q.get("options", {}),
                            "user_answer":answers[i] if i < len(answers) else "",
                            "correct_answer":  q.get("correct_answer", ""),
                            "is_correct": (
                                answers[i].upper() == q.get("correct_answer", "").upper()
                                if i < len(answers) else False
                            ),
                            "explanation": explanation,
                        })
                    review_result["feedback"] = feedback_list

                if isinstance(review_result, list):
                    review_result = {"feedback": review_result}

                if not isinstance(review_result, dict):
                    review_result = {}

        
                
                

            
                review_result["score"] = f"{correct_count}/{total}"  # type: ignore
                review_result["grade"] = get_grade(percentage)        # type: ignore
                review_result["percentage"] = percentage                   # type: ignore

                review_result.setdefault(
                    "summary",
                    f"You scored {correct_count}/{total} ({percentage}%). "
                    + (
                        "Excellent work!" if percentage >= 90 else
                        "Great job!"  if percentage >= 80 else
                        "Good effort!"if percentage >= 70 else
                        "Fair attempt."if percentage >= 60 else
                        "Keep practicing."
                    ), # type: ignore
                )
                review_result.setdefault(
                    "improvement_areas",
                    [
                        state["questions"][i].get("question", "") + "..."
                        for i in range(len(state["questions"]))
                        if i < len(answers)
                        and answers[i].upper()
                        != state["questions"][i].get("correct_answer", "").upper()
                    ],
                )

                state["review_result"] = review_result

                print(f"\nScore:  {review_result['score']}")
                print(f" Grade: {review_result['grade']}")
                print(f"Percentage: {review_result['percentage']}%\n")

                feedback_items = [
                    QuestionFeedback(
                        question_number=item.get("question_number", i + 1),
                        question= item.get("question", ""),
                        options= item.get("options", {}),
                        user_answer= item.get("user_answer", ""),
                        correct_answer= item.get("correct_answer", ""),
                        is_correct= item.get("is_correct", False),
                        explanation= item.get("explanation", ""),
                    )
                    for i, item in enumerate(review_result.get("feedback", []))
                ]

                return QuizResponse(
                    query=  state["query"],
                    difficulty= state["difficulty"],
                    total_questions=   state["num_questions"],
                    score=    review_result["score"], # type: ignore
                    grade=  review_result["grade"], # type: ignore
                    percentage=float(review_result["percentage"]), # type: ignore
                    feedback=feedback_items,
                    summary= review_result["summary"],  # type: ignore
                    improvement_areas= review_result["improvement_areas"],
                )
        
        except Exception as e:
            self.repo.log_error(file_name="router.py",function_name="run_quiz_pipeline", error_message=str(e))
            raise Exception("service layer error")
              


                    
def parse_json_string(json_string):
    """
    
    """
    try:
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return None




