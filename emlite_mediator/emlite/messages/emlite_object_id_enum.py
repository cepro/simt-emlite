from .emlite_message import EmliteMessage

# Re-export at a more meaningful namespace as it should not be tied to the message.
# See comments in EmliteMessage about this.
ObjectIdEnum = EmliteMessage.ObjectIdType
