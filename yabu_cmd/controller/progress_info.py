class ProgressInfo:
    def __init__(self, count: int = 1, msg: str = None, total: int = None) -> None:
        self.count = count
        self.msg = msg
        self.total = total
