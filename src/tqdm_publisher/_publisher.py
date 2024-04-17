from typing import Union
from uuid import uuid4

from tqdm import tqdm as base_tqdm


class TQDMProgressPublisher(base_tqdm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progress_bar_id = str(uuid4())
        self.callbacks = dict()

    # Override the update method to run callbacks
    def update(self, n: int = 1) -> Union[bool, None]:
        displayed = super().update(n)

        for callback in self.callbacks.values():
            callback(self.format_dict)

        return displayed

    def subscribe(self, callback: callable) -> str:
        """
        Subscribe to updates from the progress bar.

        This method assigns a unique ID to the given callback and stores it in an internal
        dictionary. It allows the callback to be referenced and activated in the overridden
        update function for TQDM. The unique callback ID is returned, which can be used
        for future operations such as deregistering the callback.

        Parameters
        ----------
        callback : callable
            A callable object (like a function) that will be called back by this object.
            The callback should be able to be invoked with a single argument, the progress
            bar's format_dict.

        Returns
        -------
        callback_id : str
            A unique identifier for the callback. This ID is a UUID string and can be used
            to reference the registered callback in future operations.

        Examples
        --------
        >>> def my_callback(format_dict):
        >>>     print("Progress update", format_dict)
        >>>
        >>> publisher = TQDMPublisher()
        >>> callback_id = publisher.subscribe(my_callback)
        >>> print(callback_id)  # Prints the unique callback ID
        """

        callback_id = str(uuid4())
        self.callbacks[callback_id] = callback
        callback(self.format_dict)  # Call the callback immediately to show the current state
        return callback_id

    def unsubscribe(self, callback_id: str) -> bool:
        """
        Unsubscribe a previously registered callback from the progress bar updates.

        This method removes the callback associated with the given unique ID from the internal
        dictionary. It is used to deregister callbacks that were previously added via the
        `subscribe` method. Once a callback is removed, it will no longer be called during
        the progress bar's update events.

        Parameters
        ----------
        callback_id : str
            The unique identifier of the callback to be unsubscribed. This is the same UUID string
            that was returned by the `subscribe` method when the callback was registered.

        Returns
        -------
        success : bool
            Returns True if the callback was successfully removed, or False if no callback was
            found with the given ID.

        Examples
        --------
        >>> publisher = TQDMPublisher()
        >>> callback_id = publisher.subscribe(my_callback)
        >>> print(callback_id)  # Prints the unique callback ID
        >>> unsubscribed = publisher.unsubscribe(callback_id)
        >>> print(unsubscribed)  # True if successful, False otherwise

        Notes
        -----
        It's important to manage the lifecycle of callbacks, especially in cases where the
        number of subscribers might grow large or change frequently. Unsubscribing callbacks
        when they are no longer needed can help prevent memory leaks and other performance issues.
        """
        if callback_id not in self.callbacks:
            return False

        del self.callbacks[callback_id]
        return True
