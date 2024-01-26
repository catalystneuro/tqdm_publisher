import asyncio
import random

async def sleep_func(sleep_duration: float = 1) -> float:
    await asyncio.sleep(delay=sleep_duration)


def create_tasks():
    n = 10**5
    sleep_durations = [random.uniform(0, 5.0) for _ in range(n)]
    tasks = []

    for sleep_duration in sleep_durations:
        task = asyncio.create_task(sleep_func(sleep_duration=sleep_duration))
        tasks.append(task)

    return tasks
