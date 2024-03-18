import time

from tqdm_publisher import TQDMPublisher


def test_initialization():
    publisher = TQDMPublisher()
    assert len(publisher.callbacks) == 0


# Test concurrent callback execution
def test_subscription_and_callback_execution():
    n_callback_executions = dict()

    def test_callback(identifier, data):
        nonlocal n_callback_executions

        if identifier not in n_callback_executions:
            n_callback_executions[identifier] = 0

        n_callback_executions[identifier] += 1

        assert "n" in data and "total" in data

    all_task_durations_in_seconds = [0.1 for _ in range(10)]

    publisher = TQDMPublisher(all_task_durations_in_seconds)

    n_subscriptions = 10
    for i in range(n_subscriptions):
        callback_id = publisher.subscribe(
            lambda data, i=i: test_callback(i, data)
        )  # Creates a new scoped i value for subscription
        assert callback_id in publisher.callbacks

    # Simulate an update to trigger the callback
    for duration in publisher:
        time.sleep(duration)

    assert len(n_callback_executions) == n_subscriptions

    for identifier, n_executions in n_callback_executions.items():
        assert n_executions > 1


def test_unsubscription():
    def dummy_callback(data):
        pass

    tasks = []
    publisher = TQDMPublisher(tasks)
    callback_id = publisher.subscribe(dummy_callback)
    result = publisher.unsubscribe(callback_id)
    assert result == True
    assert callback_id not in publisher.callbacks

    result = publisher.unsubscribe(callback_id)
    assert result == False
