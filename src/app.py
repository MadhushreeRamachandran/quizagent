from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers.router import router
from migrations.migration import Migration


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run migrations and seed data on startup"""
    migration = Migration()
    migration.run_startup_migration()
    print("tables created")
    yield
    
app = FastAPI(
    title="Quiz & Review Multi-Agent System",
    description="LangGraph-style multi-agent quiz pipeline with middleware + interrupt",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(router)







