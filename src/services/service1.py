import json
import uuid

from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig

from models.model import *
from agents.quiz_agent import quiz_agent_tool
from agents.reviewer_agent import review_agent_tool
from agents.submit_answers_tool import submit_answers_tool
from config.config import *
from utilities.utils import *
from repositories.repo import Repository
from agents.main_agent_prompt import MAIN_AGENT_PROMPT


def get_grade(p):
    if p >= 90: return "A"
    elif p >= 80: return "B"
    elif p >= 70: return "C"
    elif p >= 60: return "D"
    return "Fail"


class QuizService:

    def __init__(self, repo: Repository):
        self.repo = repo

    async def run_quiz_pipeline(self, request: QuizRequest) -> QuizResponse:
        try:
            thread_id = str(uuid.uuid4())
            llm = get_llm()
            config = RunnableConfig(configurable={"thread_id": thread_id})
            conn_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

            async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                await checkpointer.setup()

                agent = create_agent(
                    model=llm,
                    tools=[quiz_agent_tool, submit_answers_tool, review_agent_tool],
                    checkpointer=checkpointer,
                    system_prompt=MAIN_AGENT_PROMPT,
                )

               
                print(f"\nProcessing query: '{request.query}'\n")

                result = await agent.ainvoke(
                    {
                        "messages": [{
                            "role": "user",
                            "content": (
                                f"{request.query} | "
                                f"num_questions={request.num_questions or 5} | "
                                f"difficulty={request.difficulty or 'medium'}"
                            )
                        }]
                    },
                    config=config,
                )

                
                if "__interrupt__" not in result:
                    raise Exception("Expected interrupt after quiz generation but none occurred")

                interrupt_payload = result["__interrupt__"][0].value
                questions = interrupt_payload.get("questions", [])

                if not questions:
                    raise Exception("No questions found in interrupt payload")

               
                print("\n" + "=" * 50)
                print("QUIZ TIME")
                print("=" * 50)

                for i, q in enumerate(questions):
                    print(f"\nQ{i+1}: {q['question']}")
                    print(f"  A) {q['options']['A']}")
                    print(f"  B) {q['options']['B']}")
                    print(f"  C) {q['options']['C']}")
                    print(f"  D) {q['options']['D']}")

                
                print(f"\nEnter {len(questions)} answers separated by commas (e.g. A,B,C,D): ")
                raw = input("Your answers: ").strip().upper()
                answers = [a.strip() for a in raw.split(",")]

               
               
                final = await agent.ainvoke(
                    Command(resume=answers),
                    config=config,
                )

                
                review_result = None
                for msg in reversed(final.get("messages", [])):
                    content = msg.content if hasattr(msg, "content") else str(msg)
                    content = strip_thinking(str(content)).strip()
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, dict) and "Feedback" in parsed:
                            review_result = parsed
                            break
                    except:
                        continue

                if not review_result:
                    raw_review = strip_thinking(final["messages"][-1].content).strip()
                    try:
                        review_result = json.loads(raw_review)
                    except:
                        review_result = parse_review_text(raw_review)

               
                total = len(questions)
                correct = sum(
                    1 for i, q in enumerate(questions)
                    if i < len(answers)
                    and answers[i].upper() == q.get("correct_answer", "").upper()
                )
                percentage = round((correct / total) * 100, 2) if total > 0 else 0.0

                review_result["score"] = f"{correct}/{total}"
                review_result["grade"] = get_grade(percentage)
                review_result["percentage"] = percentage

               
                feedback_items = []
                per_q = review_result.get("Feedback", {})

                for i, (k, v) in enumerate(per_q.items()):
                    if i >= len(questions):
                        break
                    q = questions[i]
                    feedback_items.append(
                        QuestionFeedback(
                            question_number=i + 1,
                            question=q["question"],
                            options=q["options"],
                            user_answer=answers[i] if i < len(answers) else "",
                            correct_answer=q["correct_answer"],
                            is_correct=(answers[i] == q["correct_answer"]) if i < len(answers) else False,
                            explanation=v
                        )
                    )

                return QuizResponse(
                    query=request.query,
                    difficulty=request.difficulty or "medium",
                    total_questions=total,
                    score=review_result["score"],
                    grade=review_result["grade"],
                    percentage=percentage,
                    feedback=feedback_items,
                    summary=review_result.get("summary", ""),
                    improvement_areas=review_result.get("improvement_areas", []),
                )

        except Exception as e:
            self.repo.log_error(
                file_name="service.py",
                function_name="run_quiz_pipeline",
                error_message=str(e)
            )
            raise Exception(f"service layer error: {e}")