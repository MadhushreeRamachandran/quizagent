from sqlalchemy.orm import Session
from sqlalchemy import select
 
from repositories.schemas.schema import ErrorLog
 
 
class Repository:
 
    def __init__(self, db: Session):
        self.db = db
  
    def log_error(self, file_name:str, function_name: str,error_message:str):
        try:
            error_log=ErrorLog(
                file_name=file_name,
                function_name=function_name,
                error_message=error_message
            )
            self.db.add(error_log)
            self.db.commit()
        except Exception:
            self.db.rollback()

    
    def get_all_error_logs(self):
        stmt = select(ErrorLog).order_by(ErrorLog.created_at.desc())
        logs = self.db.execute(stmt).scalars().all()
        
        result = []
        for log in logs:
            result.append({
                "file_name":     log.file_name,
                "function_name": log.function_name,
                "error_message": log.error_message,
                "created_at":    str(log.created_at)
            })
        return result




    

