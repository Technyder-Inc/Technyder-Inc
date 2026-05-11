import os
from supabase import create_client, Client


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def save_ideas(ideas: list[dict]) -> None:
    client = get_client()
    client.table("daily_ideas").insert(ideas).execute()


def fetch_ideas(date: str | None = None) -> list[dict]:
    client = get_client()
    query = client.table("daily_ideas").select("*")
    if date:
        query = query.eq("date", date)
    result = query.order("created_at", desc=True).execute()
    return result.data
