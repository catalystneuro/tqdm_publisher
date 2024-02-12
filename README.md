# tqdm-publisher
[![PyPI version](https://badge.fury.io/py/tqdm_publisher.svg)](https://badge.fury.io/py/tqdm_publisher.svg)
[![codecov](https://codecov.io/github/catalystneuro/tqdm_publisher/coverage.svg?branch=main)](https://codecov.io/github/catalystneuro/tqdm_publisher?branch=main)
[![License](https://img.shields.io/pypi/l/tqdm_publisher.svg)](https://github.com/catalystneuro/tqdm_publisher/blob/main/license.txt)

`tqdm_publisher` is a small Python package that allows you to subscribe to updates from `tqdm` progress bars with arbitrary callback functions.

This is useful if you want to use `tqdm` to track the progress of a long-running task, but you also want to do something else with the progress information (e.g., forward it to a user interface, log it to a file, etc.).

## Installation
```bash
pip install tqdm_publisher
```

## Getting Started

### Basic Usage
To convert an existing TQDM progress bar into a `TQDMPublisher`, simply swap the `tqdm` and `TQDMPublisher` constructors. 

You'll need to declare a callback function to handle progress updates, which you can declare wherever you like.

Then, before iterating, subscribe your callback to the `TQDMPublisher` updates using the `subscribe` method.

#### Original Code
```python
import random
import asyncio

from tqdm import tqdm

async def sleep_func(sleep_duration = 1):
    await asyncio.sleep(delay=sleep_duration)

async def run_multiple_sleeps(sleep_durations):

    tasks = []

    # Create a list of tasks to run
    for sleep_duration in sleep_durations:
        task = asyncio.create_task(sleep_func(sleep_duration=sleep_duration))
        tasks.append(task)

    # Create a progress bar to track the tasks
    progress_bar = tqdm(asyncio.as_completed(tasks), total=len(tasks))

    # Iterate over the progress bar to run the tasks
    for f in progress_bar:
        await f
        
number_of_tasks = 10**5
sleep_durations = [random.uniform(0, 5.0) for _ in range(number_of_tasks)]
asyncio.run(run_multiple_sleeps(sleep_durations=sleep_durations))
```

#### Modified Code

```python
import random
import asyncio

from tqdm_publisher import TQDMPublisher

async def sleep_func(sleep_duration = 1):
    await asyncio.sleep(delay=sleep_duration)

async def run_multiple_sleeps(sleep_durations, on_update):

    tasks = []

    for sleep_duration in sleep_durations:
        task = asyncio.create_task(sleep_func(sleep_duration=sleep_duration))
        tasks.append(task)

    # Replace the progress bar with a TQDMPublisher
    progress_bar = TQDMPublisher(asyncio.as_completed(tasks), total=len(tasks))

    # Subscribe to updates from the progress bar
    callback_id = progress_bar.subscribe(on_update)

    # Start the tasks
    for f in progress_bar:
        await f

    # Unsubscribe from updates (optional)
    progress_bar.unsubscribe(callback_id)

# Define a callback function to handle progress updates
main_callback = lambda info: print('Progress Update', info)

number_of_tasks = 10**5
sleep_durations = [random.uniform(0, 5.0) for _ in range(number_of_tasks)]

# Pass your callback function to the coroutine
asyncio.run(run_multiple_sleeps(sleep_durations=sleep_durations, on_update=main_callback))
```

## Demo
A complete demo of `tqdm_publisher` can be found in the `demo` directory, which shows how to forward progress updates from the same `TQDMPublisher` instance to multiple clients.

To run the demo, first install the dependencies:
```bash
pip install tqdm_publisher[demo]
```

Then, run the base CLI command to start the demo server and client:
```bash
tqdm_publisher demo
```

> **Note:** Alternatively, you can run each part of the demo separately by running `tqdm_publisher demo --server` and `tqdm_publisher demo --client` in separate terminals.

Finally, you can click the Create Progress Bar button to create a new `TQDMPublisher` instance, which will begin updating based on the `TQDMPublisher` instance in the Python script.
