from functools import lru_cache

from app.core.config import settings
from app.storage.local import LocalFileStorage


@lru_cache
def get_storage() -> LocalFileStorage:
    return LocalFileStorage(settings.STORAGE_ROOT)
