from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

SCHEMA_NAME = 'flows'


def supa_client(supabase_url: str, supabase_key: str) -> Client:
    options = ClientOptions()
    options.schema = SCHEMA_NAME
    return create_client(
        supabase_url,
        supabase_key,
        options
    )
