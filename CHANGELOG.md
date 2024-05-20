## Unreleased
* Update the arguments for all `tqdm_publisher` classes to mirror the `tqdm` constructor, adding additional parameters as required keyword arguments.

## v0.1.0 (April 26th, 2024)
* The first alpha release of `tqdm_publisher`.

### Bug Fixes
- Removed unused `RELATIVE_DEMO_BASE_FOLDER_PATH` variable that improperly used `Path.cwd()` in the built package.
- Returned a value from the parallel demo's `update` endpoint to prevent errors from being thrown each time the endpoint is called.
