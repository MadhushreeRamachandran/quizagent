from typing import List, TypedDict, Optional
from pydantic import BaseModel, field_validator


from langchain_core.messages import BaseMessage

class AgentInput(TypedDict):
    messages: List[BaseMessage]


class QuizState(TypedDict):
    query: str
    num_questions: int
    difficulty: str
    current_step: str
    questions: Optional[list[str]]
    answers: Optional[list[str]]
    review_result: Optional[dict]   


class QuizRequest(BaseModel):

    query: str
    @field_validator("query")
    @classmethod
    def topic_validation(cls,value):
        if not value.strip():
            raise ValueError("query cannot be empty. Kindly provide query")
        return value 
                          
    num_questions: Optional[int]=3
    
               
    difficulty: Optional[str]="easy"
   


class QuestionFeedback(BaseModel):
    question_number: int
    question: str
    options: dict                
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str

class QuizResponse(BaseModel):
    query: str
    difficulty: str
    total_questions: int
    score: str
    grade: str
    percentage: float
    feedback: list[QuestionFeedback]
    summary: str
    improvement_areas: list[str]