import schedule
import time
from dotenv import load_dotenv
from generator import generate_daily_ideas
from storage import save_ideas

load_dotenv()


def run_daily_job(topic: str = "technology and AI automation") -> None:
    print(f"Generating ideas for topic: {topic}")
    ideas = generate_daily_ideas(topic=topic, count=5)
    save_ideas(ideas)
    print(f"Saved {len(ideas)} ideas.")


if __name__ == "__main__":
    schedule.every().day.at("08:00").do(run_daily_job)
    print("DailyIdeas scheduler started. Running at 08:00 daily.")
    while True:
        schedule.run_pending()
        time.sleep(60)
