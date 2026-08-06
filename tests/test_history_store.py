import pytest

from chatbot.history_store import (
    ChatTurn,
    InMemoryChatHistoryStore,
    SqliteChatHistoryStore,
)


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryChatHistoryStore()
    return SqliteChatHistoryStore(db_path=str(tmp_path / "history.db"))


def turn(index: int, user_success: bool = True) -> ChatTurn:
    return ChatTurn(prompt=f"prompt {index}", response=f"response {index}", success=user_success)


def test_new_store_has_no_history(store):
    assert store.get_all("alice") == []
    assert store.get_recent("alice", 5) == []


def test_appended_turns_are_returned_in_order(store):
    for index in range(3):
        store.append("alice", turn(index))

    turns = store.get_all("alice")

    assert [item.prompt for item in turns] == ["prompt 0", "prompt 1", "prompt 2"]


def test_get_recent_returns_last_turns_in_chronological_order(store):
    for index in range(5):
        store.append("alice", turn(index))

    recent = store.get_recent("alice", 2)

    assert [item.prompt for item in recent] == ["prompt 3", "prompt 4"]


def test_history_is_isolated_per_user(store):
    store.append("alice", turn(1))
    store.append("bob", turn(2))

    assert len(store.get_all("alice")) == 1
    assert store.get_all("bob")[0].prompt == "prompt 2"


def test_success_flag_round_trips(store):
    store.append("alice", turn(1, user_success=False))
    assert store.get_all("alice")[0].success is False


def test_clear_returns_number_of_removed_turns(store):
    store.append("alice", turn(1))
    store.append("alice", turn(2))

    assert store.clear("alice") == 2
    assert store.get_all("alice") == []


def test_clear_unknown_user_returns_zero(store):
    assert store.clear("nobody") == 0


def test_list_user_ids_is_sorted_and_distinct(history_store):
    history_store.append("bob", turn(1))
    history_store.append("alice", turn(2))
    history_store.append("alice", turn(3))

    assert history_store.list_user_ids() == ["alice", "bob"]


def test_list_recent_records_returns_newest_first(history_store):
    for index in range(3):
        history_store.append("alice", turn(index))

    records = history_store.list_recent_records(limit=2)

    assert [record["prompt"] for record in records] == ["prompt 2", "prompt 1"]
    assert records[0]["user_id"] == "alice"
    assert records[0]["success"] is True
    assert records[0]["created_at"]


@pytest.mark.parametrize("limit, expected", [(0, 1), (-5, 1), (5000, 3)])
def test_list_recent_records_clamps_limit(history_store, limit, expected):
    for index in range(3):
        history_store.append("alice", turn(index))

    assert len(history_store.list_recent_records(limit=limit)) == expected


def test_sqlite_store_persists_across_connections(tmp_path):
    db_path = str(tmp_path / "persist.db")
    SqliteChatHistoryStore(db_path=db_path).append("alice", turn(1))

    reopened = SqliteChatHistoryStore(db_path=db_path)

    assert [item.prompt for item in reopened.get_all("alice")] == ["prompt 1"]


def test_sqlite_store_creates_parent_directory(tmp_path):
    db_path = tmp_path / "nested" / "dir" / "history.db"
    SqliteChatHistoryStore(db_path=str(db_path))
    assert db_path.parent.is_dir()
