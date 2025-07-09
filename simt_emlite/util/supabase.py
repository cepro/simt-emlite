from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

SCHEMA_NAME = "flows"


def supa_client(
    supabase_url: str,
    supabase_key: str,
    role_key: str | None = None,
    schema: str | None = None,
) -> Client:
    options = SyncClientOptions()
    options.schema = schema if schema is not None else SCHEMA_NAME
    options.auto_refresh_token = False

    if role_key is not None:
        options.headers = {"Authorization": f"Bearer {role_key}"}

    client = create_client(supabase_url, supabase_key, options)

    # a bug in the library blows away the auth header set above/
    # so after client creation we restore it again here:
    client.postgrest.session.headers["authorization"] = f"Bearer {role_key}"

    return client
