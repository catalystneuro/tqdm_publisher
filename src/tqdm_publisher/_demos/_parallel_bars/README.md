# TQDM Publisher Multiple Bars Demo
This demo shows how to use a global `TQDMPublisher` instance to forward progress updates from parallel `TQDMPublisher` instances to the browser.

## The Approach
In this demo, we track multiple interdependent levels of progress updates by using a global `TQDMPublisher` instance to reflect the execution state of parallel `TQDMPublisher` instances.

Similar to the [multiple bar demo](../_multiple_bars/README.md), a `request_id` is used to associate both the global and parallel progress bars with a specific group of elements on the browser. In particular, the ID of the global progress bar matches the `request_id`, allowing it to be distinguished from the lower-level progress bars.

However, this approach also differs in many ways from the other demos:
1. Instead of a `websockets` server, we use a `flask` server to receive requests from the client and send updates back using the Server-Sent Events (SSE) protocol.
2. A `TQDMProgressHandler` is used to queue progress updates from parallel `TQDMPublisher` instances, avoiding the possibility of overloading the connection and receiving misformatted messages on the client.

## Handling Processes
Since our `TQDMProgressHandler` is managing progress bars across processes, we're using it in an unconventional way.

Instead of using the handler to directly manage `TQDMSubscriber` instances, we declare `TQDMPublisher` instances within the process.

Since we can't pass data directly out of the process, we send an HTTP request to the `flask` server that is directly forwarded to the handler's `announce` method.
