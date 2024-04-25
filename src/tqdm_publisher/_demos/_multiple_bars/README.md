# TQDM Publisher Multiple Bars Demo
This demo shows how to use `tqdm_publisher` to forward progress updates from multiple `TQDMPublisher` instances to the browser.

## The Approach
This demo is nearly identical to the [single bar demo](../_single_bar/README.md), except that progress bars are managed through a scoped class definition.

This allows us to easily track a `request_id` passed when the client requests a new progress bar, associating each progress bar with a pre-populated element on the browser.
