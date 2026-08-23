from app.main import handle_event


def test_handle_message_event(capsys):
    handle_event({
        "type": "message",
        "username": "alice",
        "content": "hello world"
    })
    captured = capsys.readouterr()
    assert "alice" in captured.out
    assert "hello world" in captured.out


def test_handle_user_joined_event(capsys):
    handle_event({
        "type": "user_joined",
        "username": "bob"
    })
    captured = capsys.readouterr()
    assert "bob" in captured.out
    assert "joined" in captured.out


def test_handle_user_left_event(capsys):
    handle_event({
        "type": "user_left",
        "username": "carol"
    })
    captured = capsys.readouterr()
    assert "carol" in captured.out
    assert "left" in captured.out


def test_handle_unknown_event_type(capsys):
    handle_event({"type": "something_weird"})
    captured = capsys.readouterr()
    assert "Unknown event" in captured.out
