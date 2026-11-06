from tom_aimail.state import StateStore


def test_state_remembers_senders_across_instances(tmp_path):
    path = tmp_path / "state.json"
    store = StateStore(path)
    assert store.is_new_sender("Friend@Example.com")
    store.remember_sender("Friend@Example.com")
    assert not store.is_new_sender("friend@example.com")

    reloaded = StateStore(path)
    assert not reloaded.is_new_sender("friend@example.com")
    assert reloaded.is_new_sender("someone-else@example.com")
