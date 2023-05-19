class ProgressInfo:
    def __init__(self, count: int = 1, msg: str = None, total: int = None) -> None:
        """Used to communicate progress info from the Model to the View.

        Args:
            count (int, optional): The amount to add to the current count of progress. Defaults to 1.
            msg (str, optional): The message to send with the progress information. Defaults to None.
            total (int, optional): The total amount of cycles left to run. Defaults to None.
        """
        self.count = count
        self.msg = msg
        self.total = total
