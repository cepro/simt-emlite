from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

SCHEMA_NAME = 'flows'


def supa_client(supabase_url: str, supabase_key: str, role_key: str) -> Client:
    options = ClientOptions()
    options.schema = SCHEMA_NAME
    options.headers = {'Authorization': f'Bearer {role_key}'}

    client = create_client(
        supabase_url,
        supabase_key,
        options
    )

    # a bug in the library blows away the auth header set above/
    # so after client creation we restore it again here:
    client.postgrest.session.headers['authorization'] = f'Bearer {role_key}'

    return client
