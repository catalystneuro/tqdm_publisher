from ._publisher import TQDMPublisher

class TQDMProgressSubscriber(TQDMPublisher):
    def __init__(self, iterable, on_progress_update: callable, **tqdm_kwargs):
        super().__init__(iterable, **tqdm_kwargs)
        self.subscribe(lambda format_dict: on_progress_update(dict(progress_bar_id=self.id, format_dict=format_dict)))
