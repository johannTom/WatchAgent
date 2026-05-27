from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.db.repository import count_events, count_readings
from app.db.session import get_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    return {
        "status": "ok",
        "readings_stored": count_readings(db),
        "events_stored": count_events(db),
    }
