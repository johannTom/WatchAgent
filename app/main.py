import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.config import ENABLE_POLLER
from app.db.repository import count_events, count_readings
from app.db.session import get_db, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    poller_task = None
    if ENABLE_POLLER:
        from app.poller import poller_loop

        poller_task = asyncio.create_task(poller_loop())  # Section 05: start on app boot
    try:
        yield
    finally:
        if poller_task is not None:
            poller_task.cancel()
            try:
                await poller_task
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    return {
        "status": "ok",
        "readings_stored": count_readings(db),
        "events_stored": count_events(db),
    }
