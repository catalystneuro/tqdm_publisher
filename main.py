import random
import time
import asyncio
from typing import List
from tqdm_publisher import TQDMPublisher

# Helper Functions for the Demo
async def sleep_func(sleep_duration: float = 1) -> float:
    start_time = time.time()
    await asyncio.sleep(delay=sleep_duration)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return elapsed_time

async def run_multiple_sleeps(sleep_durations: List[float]) -> List[float]:
    tasks = []

    for sleep_duration in sleep_durations:
        task = asyncio.create_task(sleep_func(sleep_duration=sleep_duration))
        tasks.append(task)

    progress_bar = TQDMPublisher(asyncio.as_completed(tasks), total=len(tasks))
    callback_id = progress_bar.subscribe(lambda info: print(info))

    actual_sleep_durations = [await f for f in progress_bar]

    progress_bar.unsubscribe(callback_id)

n = 10**5
sleep_durations = [random.uniform(0, 5.0) for _ in range(n)]
asyncio.run(run_multiple_sleeps(sleep_durations=sleep_durations))