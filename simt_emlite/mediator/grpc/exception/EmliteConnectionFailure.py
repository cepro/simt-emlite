# This is raised by the client when it sees the server failed to connect to an
# emlite meter after a number of retries.
#
# It effectively translates the servers INTERNAL error into something more
# specific for clients.
class EmliteConnectionFailure(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
