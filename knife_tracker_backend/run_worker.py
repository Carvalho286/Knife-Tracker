import asyncio
from knife_tracker_backend.worker import run_worker

if __name__ == "__main__":
    asyncio.run(run_worker())