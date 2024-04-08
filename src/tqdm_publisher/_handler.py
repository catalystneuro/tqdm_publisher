import queue
from typing import Any, Dict, Iterable, List

from ._subscriber import TQDMProgressSubscriber


class TQDMProgressHandler:
    def __init__(self):
        self.listeners: List[queue.Queue] = []

    def listen(self) -> queue.Queue:
        new_queue = queue.Queue(maxsize=25)
        self.listeners.append(new_queue)
        return new_queue

    def create_progress_subscriber(
        self, iterable: Iterable[Any], additional_metadata: dict = dict(), **tqdm_kwargs
    ) -> TQDMProgressSubscriber:

        def on_progress_update(progress_update: dict):
            """
            This is the injection called on every update of the progress bar.

            It triggers the announcement event over all listeners on each update of the progress bar.
            """
            self._announce(message=dict(**progress_update, **additional_metadata))

        return TQDMProgressSubscriber(iterable=iterable, on_progress_update=on_progress_update, **tqdm_kwargs)

    def _announce(self, message: Dict[Any, Any]):
        """
        Announce a message to all listeners.

        @garrett - can you describe the expected structure of this message?
        """
        number_of_listeners = len(self.listeners)
        listener_indices = range(number_of_listeners)
        listener_indices_from_newest_to_oldest = reversed(listener_indices)
        for listener_index in listener_indices_from_newest_to_oldest:
            if not self.listeners[listener_index].full():
                self.listeners[listener_index].put_nowait(item=message)
            else:  # When full, remove the newest listener in the stack
                del self.listeners[listener_index]
