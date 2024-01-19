from tqdm_publisher import TQDMPublisher
import pytest
from utils import create_tasks
import asyncio

def test_initialization():
    publisher = TQDMPublisher()
    assert len(publisher.callbacks) == 0

@pytest.mark.asyncio
async def test_subscription_and_callback_execution():
    n_callback_executions = 0

    def test_callback(data):
        nonlocal n_callback_executions
        n_callback_executions += 1
        assert 'n' in data and 'total' in data

    tasks = create_tasks()
    publisher = TQDMPublisher(asyncio.as_completed(tasks), total=len(tasks))
    callback_id = publisher.subscribe(test_callback)
    
    assert callback_id in publisher.callbacks

    # Simulate an update to trigger the callback
    for f in publisher:
        await f

    assert n_callback_executions > 0

def test_unsubscription():
    def dummy_callback(data):
        pass

    tasks = []
    publisher = TQDMPublisher(asyncio.as_completed(tasks), total=len(tasks))
    callback_id = publisher.subscribe(dummy_callback)
    result = publisher.unsubscribe(callback_id)
    assert result == True
    assert callback_id not in publisher.callbacks
