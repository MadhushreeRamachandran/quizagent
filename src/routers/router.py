from fastapi import APIRouter, Depends
from requests import Session
from models.model import *
from services.service import QuizService
from Database.database import db_provider
from repositories.repo import Repository

router = APIRouter(prefix="/quiz", tags=["Quiz"])



def get_repo(db: Session = Depends(db_provider.get_session)):
    return Repository(db) # type: ignore

def get_service(repo:Repository=Depends(get_repo)):
    return QuizService(repo)


@router.post("/start", response_model=QuizResponse)
async def start_quiz(request: QuizRequest, service:QuizService=Depends(get_service), repo:Repository=Depends(get_repo)):
    try:
        result = await service.run_quiz_pipeline(request)
        return result
    except Exception as e:
        repo.log_error(file_name="router.py",function_name="process()", error_message=str(e))
        raise Exception("router layer error") 