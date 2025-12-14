"""Supabase client initialization."""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY


_client: Client | None = None


def get_supabase_client() -> Client:
    """Get or create a Supabase client instance.
    
    Returns:
        Supabase client instance.
    """
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

