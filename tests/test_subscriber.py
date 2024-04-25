import asyncio
from uuid import UUID

import pytest

from tqdm_publisher import TQDMProgressSubscriber
from tqdm_publisher.testing import create_tasks


def test_initialization():
    subscriber = TQDMProgressSubscriber(iterable=[], on_progress_update=lambda x: x)
    assert len(subscriber.callbacks) == 1


# Test concurrent callback execution
@pytest.mark.asyncio
async def test_subscription_and_callback_execution():
    n_callback_executions = 0

    def test_callback(data):
        nonlocal n_callback_executions
        n_callback_executions += 1

        assert "progress_bar_id" in data
        identifier = data["progress_bar_id"]
        assert str(UUID(identifier, version=4)) == identifier

        assert "format_dict" in data
        format = data["format_dict"]
        assert "n" in format and "total" in format

    tasks = create_tasks()
    subscriber = TQDMProgressSubscriber(asyncio.as_completed(tasks), test_callback, total=len(tasks))

    # Simulate an update to trigger the callback
    for f in subscriber:
        await f

    assert n_callback_executions > 1
