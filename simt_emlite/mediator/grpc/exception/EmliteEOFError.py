# This is raised by the client when it sees the server encountered an EOFError
# when reading response data from an emlite meter.
#
# NOTE: it's not clear yet why we see these but they are occuring a few times
# a day currently. Handling currently involves logging them as a warning and
# moving on. We could add a retry in these cases and see if a second call
# works.
#
# It effectively translates the servers INTERNAL error into something more
# specific for clients.
class EmliteEOFError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
