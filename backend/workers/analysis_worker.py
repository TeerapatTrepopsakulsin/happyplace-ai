import logging

# Import all models to ensure they are registered with SQLAlchemy
import app.models  # noqa: F401
import asyncio

from workers.base import WorkerBase
from app.events.handlers import handle_danger, handle_emotion

logger = logging.getLogger(__name__)


class AnalysisWorker(WorkerBase):
    async def handle_payload(self, payload: dict, db):
        await handle_emotion(payload, db)
        await handle_danger(payload, db)


def main():
    worker = AnalysisWorker(channel="message.created")
    asyncio.run(worker.run())


if __name__ == "__main__":
    main()
