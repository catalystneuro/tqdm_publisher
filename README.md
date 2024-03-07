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
To monitor the progress of an existing `tqdm` progress bar, simply swap the `tqdm`and `TQDMPublisher` constructors. Then, declare a callback function to handle progress updates, and subscribe it to the `TQDMPublisher` updates using the `subscribe` method _before iteration begins_.

#### Original Code
```python
import random
import time

from tqdm import tqdm

N_TASKS = 100

# Create a list of tasks
durations = [ random.uniform(0, 1.0) for _ in range(N_TASKS) ]

# Create a progress bar
progress_bar = tqdm(durations)

# Iterate over the progress bar
for duration in progress_bar:
    time.sleep(duration) # Execute the task
```

#### Modified Code

```python
import random
import time

from tqdm_publisher import TQDMPublisher

N_TASKS = 100
durations = [ random.uniform(0, 1.0) for _ in range(N_TASKS) ]
progress_bar = TQDMPublisher(durations)

# Declare a callback function to handle progress updates
on_update = lambda info: print('Progress Update', info)

# Subscribe the callback to the TQDMPublisher
progress_bar.subscribe(on_update)

for duration in progress_bar:
    time.sleep(duration)
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
