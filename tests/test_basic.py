import asyncio

import pytest

from tqdm_publisher import TQDMPublisher
from tqdm_publisher.testing import create_tasks


def test_initialization():
    publisher = TQDMPublisher()
    assert len(publisher.callbacks) == 0


# Test concurrent callback execution
@pytest.mark.asyncio
async def test_subscription_and_callback_execution():
    n_callback_executions = dict()

    def test_callback(identifier, data):
        nonlocal n_callback_executions

        if identifier not in n_callback_executions:
            n_callback_executions[identifier] = 0

        n_callback_executions[identifier] += 1

        assert "n" in data and "total" in data

    tasks = create_tasks()
    publisher = TQDMPublisher(asyncio.as_completed(tasks), total=len(tasks))

    n_subscriptions = 10
    for i in range(n_subscriptions):
        callback_id = publisher.subscribe(
            lambda data, i=i: test_callback(i, data)
        )  # Creates a new scoped i value for subscription
        assert callback_id in publisher.callbacks

    # Simulate an update to trigger the callback
    for f in publisher:
        await f

    assert len(n_callback_executions) == n_subscriptions

    for identifier, n_executions in n_callback_executions.items():
        assert n_executions > 1


def test_unsubscription():
    def dummy_callback(data):
        pass

    tasks = []
    publisher = TQDMPublisher(asyncio.as_completed(tasks), total=len(tasks))
    callback_id = publisher.subscribe(dummy_callback)
    result = publisher.unsubscribe(callback_id)
    assert result == True
    assert callback_id not in publisher.callbacks

    result = publisher.unsubscribe(callback_id)
    assert result == False

