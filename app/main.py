from fastapi import FastAPI
from app.api import auth, task
from app.core.database import Base, engine

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(task.router)
app.include_router(auth.router)