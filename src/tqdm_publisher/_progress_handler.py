import queue
from ._progress_subscriber import TQDMProgressSubscriber

class TQDMProgressHandler:
    def __init__(self):
        self.listeners = []

    def listen(self):
        q = queue.Queue(maxsize=25)
        self.listeners.append(q)
        return q
    
    def create(self, iterable, additional_metadata: dict = dict(), **tqdm_kwargs):
        return TQDMProgressSubscriber(iterable, lambda progress_update: self._announce(dict(
            **progress_update,
            **additional_metadata
        )), **tqdm_kwargs)

    def _announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]