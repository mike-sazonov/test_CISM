import asyncio

from app.workers.consumer import run_worker

if __name__ == "__main__":
    asyncio.run(run_worker())