from app.tasks import send_welcome_email, process_new_message


def test_send_welcome_email_returns_status():
    result = send_welcome_email("test@example.com", "testuser")
    assert result["status"] == "sent"
    assert result["email"] == "test@example.com"


def test_process_new_message_counts_words():
    result = process_new_message("testuser", "this is four words")
    assert result["word_count"] == 4
