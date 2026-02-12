import pytest

from answer_gen.exceptions import StorageWriteError
from answer_gen.storage.persistence import Persistence


def test_commit_raises_storage_write_error_and_rolls_back():
    class _FakeSession:
        def __init__(self):
            self.rolled_back = False

        def commit(self):
            raise RuntimeError("db down")

        def rollback(self):
            self.rolled_back = True

    session = _FakeSession()
    store = Persistence(session)

    with pytest.raises(StorageWriteError):
        store.commit()

    assert session.rolled_back is True
