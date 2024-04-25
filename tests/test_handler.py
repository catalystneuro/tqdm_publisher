import asyncio
from uuid import UUID

import pytest

from tqdm_publisher import TQDMProgressHandler
from tqdm_publisher.testing import create_tasks

N_SUBSCRIBERS = 3
N_TASKS_PER_SUBSCRIBER = 3


# Test concurrent callback execution
@pytest.mark.asyncio
async def test_subscription_and_callback_execution():

    handler = TQDMProgressHandler(asyncio.Queue)

    n_callback_executions = dict()

    def test_callback(data):

        nonlocal n_callback_executions

        assert "progress_bar_id" in data
        identifier = data["progress_bar_id"]
        assert str(UUID(identifier, version=4)) == identifier

        if identifier not in n_callback_executions:
            n_callback_executions[identifier] = 0

        n_callback_executions[identifier] += 1

        assert "format_dict" in data
        format = data["format_dict"]
        assert "n" in format and "total" in format

    queue = handler.listen()

    for _ in range(N_SUBSCRIBERS):

        subscriber = handler.create_progress_subscriber(
            asyncio.as_completed(create_tasks(number_of_tasks=N_TASKS_PER_SUBSCRIBER)), total=N_TASKS_PER_SUBSCRIBER
        )

        for f in subscriber:
            await f

    while not queue.empty():
        message = await queue.get()
        test_callback(message)
        queue.task_done()

    assert len(n_callback_executions) == N_SUBSCRIBERS

    for _, n_executions in n_callback_executions.items():
        assert n_executions > 1


def test_unsubscription():
    handler = TQDMProgressHandler(asyncio.Queue)
    queue = handler.listen()
    assert len(handler.listeners) == 1
    result = handler.unsubscribe(queue)
    assert result == True
    assert len(handler.listeners) == 0
    result = handler.unsubscribe(queue)
    assert result == False
