import time

from quiz_service.state import DEFAULT_TTL_SEC, InMemoryStore, Session


class TestSession:
    def test_session_creation(self):
        model = {"test": "model"}
        session = Session(model=model, created_at=time.time(), ttl_sec=1800)
        assert session.model == model
        assert isinstance(session.created_at, float)
        assert session.ttl_sec == 1800

    def test_session_default_ttl(self):
        session = Session(model=None, created_at=time.time(), ttl_sec=DEFAULT_TTL_SEC)
        assert session.ttl_sec == 1800  # 30 minutes


class TestInMemoryStore:
    def test_store_initialization(self):
        store = InMemoryStore()
        assert store._map == {}

    def test_create_session(self):
        store = InMemoryStore()
        model = {"test": "model"}
        sid = store.create(model)

        assert isinstance(sid, str)
        assert len(sid) > 0
        assert sid in store._map

    def test_create_session_with_custom_ttl(self):
        store = InMemoryStore()
        model = {"test": "model"}
        sid = store.create(model, ttl_sec=3600)

        session = store._map[sid]
        assert session.ttl_sec == 3600

    def test_create_multiple_sessions(self):
        store = InMemoryStore()
        sid1 = store.create({"model": 1})
        sid2 = store.create({"model": 2})

        assert sid1 != sid2
        assert len(store._map) == 2

    def test_get_existing_session(self):
        store = InMemoryStore()
        model = {"test": "model"}
        sid = store.create(model)

        session = store.get(sid)
        assert session is not None
        assert session.model == model

    def test_get_non_existent_session(self):
        store = InMemoryStore()
        session = store.get("non-existent-id")
        assert session is None

    def test_get_expired_session(self):
        store = InMemoryStore()
        model = {"test": "model"}
        sid = store.create(model, ttl_sec=0)  # Already expired

        # Sleep a tiny bit to ensure time has passed
        time.sleep(0.01)

        session = store.get(sid)
        assert session is None
        # Session should be removed from map
        assert sid not in store._map

    def test_get_session_before_expiry(self):
        store = InMemoryStore()
        model = {"test": "model"}
        sid = store.create(model, ttl_sec=10)

        # Get immediately - should still be valid
        session = store.get(sid)
        assert session is not None
        assert session.model == model

    def test_delete_session(self):
        store = InMemoryStore()
        model = {"test": "model"}
        sid = store.create(model)

        assert sid in store._map
        store.delete(sid)
        assert sid not in store._map

    def test_delete_non_existent_session(self):
        store = InMemoryStore()
        # Should not raise an error
        store.delete("non-existent-id")

    def test_multiple_sessions_independent(self):
        store = InMemoryStore()
        sid1 = store.create({"id": 1}, ttl_sec=1800)
        sid2 = store.create({"id": 2}, ttl_sec=3600)

        session1 = store.get(sid1)
        session2 = store.get(sid2)

        assert session1.model["id"] == 1
        assert session2.model["id"] == 2
        assert session1.ttl_sec == 1800
        assert session2.ttl_sec == 3600

    def test_session_expiry_boundary(self):
        store = InMemoryStore()
        model = {"test": "model"}
        # Create session with 1 second TTL
        sid = store.create(model, ttl_sec=1)

        # Should still be valid immediately after creation
        session = store.get(sid)
        assert session is not None

        # Wait for expiry
        time.sleep(1.1)

        # Should now be expired
        session = store.get(sid)
        assert session is None

    def test_create_with_none_model(self):
        store = InMemoryStore()
        sid = store.create(None)

        session = store.get(sid)
        assert session is not None
        assert session.model is None

    def test_store_isolation(self):
        store1 = InMemoryStore()
        store2 = InMemoryStore()

        sid1 = store1.create({"store": 1})

        # Store2 should not have access to store1's sessions
        session = store2.get(sid1)
        assert session is None
