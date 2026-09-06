from prts.history import load_history, save_history


def test_load_history_returns_empty_list_when_file_missing(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    assert load_history(path) == []


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "history.json")
    original = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Good day, Doctor."},
    ]
    save_history(path, original)
    loaded = load_history(path)
    assert loaded == original


def test_load_history_handles_corrupted_file_gracefully(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("not valid json {{{")
    assert load_history(str(path)) == []


def test_save_history_overwrites_previous_content(tmp_path):
    path = str(tmp_path / "history.json")
    save_history(path, [{"role": "user", "content": "first"}])
    save_history(path, [{"role": "user", "content": "second"}])
    assert load_history(path) == [{"role": "user", "content": "second"}]
