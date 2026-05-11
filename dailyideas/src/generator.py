import os
import anthropic
from datetime import date


_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def generate_daily_ideas(topic: str = "general", count: int = 5) -> list[dict]:
    today = date.today().isoformat()
    prompt = (
        f"Generate {count} creative, actionable ideas related to '{topic}' "
        f"for {today}. Return a JSON array where each item has: "
        '"title" (short), "description" (1-2 sentences), "category" (string), '
        '"priority" (high/medium/low).'
    )

    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    text = message.content[0].text
    start = text.find("[")
    end = text.rfind("]") + 1
    ideas = json.loads(text[start:end])
    return [{"date": today, "topic": topic, **idea} for idea in ideas]
