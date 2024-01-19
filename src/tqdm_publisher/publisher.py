
from tqdm import tqdm as base_tqdm
from uuid import uuid4

# This class is a subclass of tqdm that allows for an arbitary number of callbacks to be registered
class TQDMPublisher(base_tqdm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callbacks = {}

    # Override the update method to call callbacks 
    def update(self, n=1, always_callback=False):
        if super().update(n) or always_callback:

            for id in list(self.callbacks):
                callback = self.callbacks.get(id)
                if callback:
                    callback(self.format_dict)


    # Subscribe to updates
    def subscribe(self, callback):
        callback_id = str(uuid4())
        self.callbacks[callback_id] = callback
        return callback_id
    
    # Unsubscribe from updates
    def unsubscribe(self, callback_id):
        try:
            del self.callbacks[callback_id]
            return True
        except KeyError:
            return False