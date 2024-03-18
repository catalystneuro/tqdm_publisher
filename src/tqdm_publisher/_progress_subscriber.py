from ._publisher import TQDMPublisher


class TQDMProgressSubscriber(TQDMPublisher):
    def __init__(self, iterable, *, announcer: "?", request_id: str, message: dict, **tqdm_kwargs):
        super().__init__(iterable, **tqdm_kwargs)

        def on_progress_update(format_dict) -> None:
            """
            Describe what this announcer is all about...
            """
            announcer.announce(dict(request_id=request_id, **message))

        self.subscribe(callback=on_progress_update)
