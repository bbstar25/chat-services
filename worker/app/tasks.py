import time
from app.celery_app import celery_app


@celery_app.task(name="send_welcome_email")
def send_welcome_email(email: str, username: str):
    print(f"[WORKER] Preparing welcome email for {username} <{email}>...")
    time.sleep(5)  # simulate a slow operation (a real email API call, etc.)
    print(f"[WORKER] Welcome email sent to {email}!")
    return {"status": "sent", "email": email}


@celery_app.task(name="process_new_message")
def process_new_message(username: str, content: str):
    print(f"[WORKER] Analyzing message from {username}: '{content}'...")
    time.sleep(2)
    word_count = len(content.split())
    print(f"[WORKER] Analysis complete: {word_count} words")
    return {"word_count": word_count}
