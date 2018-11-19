class DataOperationError(Exception):
    """
    This exception should be raised when fail to operate data.
    """

    def __init__(self, message):
        super().__init__()
        self.message = message
