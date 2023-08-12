from .emlite_response import EmliteResponse

# Re-export at a more meaningful namespace as it should not be tied to the response.
# See comments in EmliteResponse about this.
ObjectIdEnum = EmliteResponse.ObjectIdType