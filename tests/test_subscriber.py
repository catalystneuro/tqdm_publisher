import time

from tqdm_publisher import TQDMProgressSubscriber


def test_initialization():
    publisher = TQDMProgressSubscriber([], on_progress_update=lambda data: print(data))
    assert len(publisher.callbacks) == 1


# Test single callback execution
def test_single_callback_execution():
    n_tasks = 100
    n_callback_executions = 0

    def test_callback(data):
        nonlocal n_callback_executions
        n_callback_executions += 1
        print("CAllin")
        assert "progress_bar_id" in data and "format_dict" in data
        assert "n" in data["format_dict"] and "total" in data["format_dict"]

    all_task_durations_in_seconds = [0.1 for _ in range(10)]
    publisher = TQDMProgressSubscriber(
        all_task_durations_in_seconds, on_progress_update=lambda data: test_callback(data)
    )

    # Simulate an update to trigger the callback
    for duration in publisher:
        time.sleep(duration)

    assert n_callback_executions == len(all_task_durations_in_seconds)
