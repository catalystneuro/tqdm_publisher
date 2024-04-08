from typing import Any, Dict, Iterable

from ._publisher import TQDMProgressPublisher


class TQDMProgressSubscriber(TQDMProgressPublisher):
    def __init__(self, iterable: Iterable[Any], on_progress_update: callable, **tqdm_kwargs):
        super().__init__(iterable=iterable, **tqdm_kwargs)

        def run_on_progress_update(format_dict: Dict[str, Any]):
            """
            This is the injection called on every update of the progress bar.

            It calls the `on_progress_update` function, which must take a dictionary
            containing the progress bar ID and `format_dict`.

            It must be defined inside this local scope to include the `.progress_bar_id` attribute from the level above
            without including it in the method signature.
            """
            on_progress_update(dict(progress_bar_id=self.progress_bar_id, format_dict=format_dict))

        self.subscribe(run_on_progress_update)
