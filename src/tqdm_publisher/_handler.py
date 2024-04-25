import queue
from typing import Any, Dict, Iterable, List

from ._subscriber import TQDMProgressSubscriber


class TQDMProgressHandler:
    def __init__(
        self, queue_cls: queue.Queue = queue.Queue  # Can provide different queue implementations (e.g. asyncio.Queue)
    ):
        self._queue = queue_cls
        self.listeners: List[self._queue] = []

    def listen(self) -> queue.Queue:
        new_queue = self._queue(maxsize=0)
        self.listeners.append(new_queue)
        return new_queue

    def create_progress_subscriber(
        self, iterable: Iterable[Any], additional_metadata: dict = dict(), **tqdm_kwargs
    ) -> TQDMProgressSubscriber:

        def on_progress_update(progress_update: dict):
            """
            This is the injection called on every update of the progress bar.

            It triggers the announcement event over all listeners on each update of the progress bar.

            It must be defined inside this local scope to communicate the `additional_metadata` from the level above
            without including it in the method signature.
            """
            self.announce(message=dict(**progress_update, **additional_metadata))

        return TQDMProgressSubscriber(iterable=iterable, on_progress_update=on_progress_update, **tqdm_kwargs)

    def announce(self, message: Dict[Any, Any]):
        """
        Announce a message to all listeners.

        This message can be any dictionary. But, when used internally, is
        expected to contain the progress_bar_id and format_dict of the TQDMProgressSubscriber update function,
        as well as any additional metadata supplied by the create_progress_subscriber method.

        """
        number_of_listeners = len(self.listeners)
        listener_indices = range(number_of_listeners)
        for listener_index in listener_indices:
            self.listeners[listener_index].put_nowait(item=message)

    def unsubscribe(self, listener: queue.Queue) -> bool:
        """
        Unsubscribe a listener from the handler.

        Args:
            listener: The listener to unsubscribe.

        Returns:
            bool: True if the listener was successfully unsubscribed, False otherwise.
        """
        try:
            self.listeners.remove(listener)
            return True
        except ValueError:
            return False
