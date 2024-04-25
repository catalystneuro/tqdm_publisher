# TQDM Publisher Single Bar Demo
This demo shows how to use `tqdm_publisher` to forward progress updates from a single `TQDMPublisher` instance to the browser.

## The Approach
We use `websockets` to establish a connection between the server and the client.

A progress bar is pre-rendered on page load. When the client presses the Create Progress Bar button, the server forwards progress updates to the client using a `TQDMPublisher` instance spawned in a separate thread.

The Create button is disabled until the progress bar is finished to avoid associating updates from multiple progress bars with their respective elements.
