class ElevenLabsException(Exception):
    def __init__(self, message):
        self.message = message

class CreditsException(Exception):
    def __init__(self, message):
        self.message = message

class UserDoesNotExistException(Exception):
    def __init__(self, message):
        self.message = message