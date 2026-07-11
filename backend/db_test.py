import asyncio
import sys
from app.core.database import init_db
from app.models.user import User
from app.services.sync_service import sync_user_emails
from app.services.ai_service import analyze_emails
from google import genai

async def main():
    try:
        print("Initializing DB...")
        await init_db()
        print("DB initialized. Finding users...")
        users = await User.find_all().to_list()
        print(f"Found {len(users)} users.")
        if users:
            user = users[0]
            print("Syncing emails...")
            await sync_user_emails(user)
            print("Analyzing emails...")
            await analyze_emails(user)
            print("Done!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
