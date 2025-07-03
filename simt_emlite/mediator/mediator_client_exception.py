class MediatorClientException(Exception):
    def __init__(self, code_str: str, message: str):
        self.code_str = code_str
        self.message = message
        super().__init__(self.message)
