"""进程内 TTL 缓存：用户信息与登录态（demo 无 Redis）。"""

import time


class TTLCache:
    """通用 TTL 缓存。"""

    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[float, object]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str):
        """读取缓存，过期返回 None。"""
        item = self._store.get(key)
        if item is None:
            return None
        expire_at, value = item
        if time.time() > expire_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value, ttl: int | None = None):
        """写入缓存。"""
        self._store[key] = (time.time() + (self._default_ttl if ttl is None else ttl), value)

    def delete(self, key: str):
        """删除缓存。"""
        self._store.pop(key, None)


_user_cache = TTLCache()
_token_cache = TTLCache(default_ttl=120)


def get_user_cache(username: str):
    """按登录名读用户缓存。"""
    return _user_cache.get(f"user:{username}")


def put_user_cache(user):
    """写入用户缓存。"""
    _user_cache.set(f"user:{user.username}", user)


def invalidate_user_cache(username: str):
    """失效用户缓存。"""
    _user_cache.delete(f"user:{username}")


def get_token_session(token: str):
    """按 token 读登录态。"""
    return _token_cache.get(f"token:{token}")


def put_token_session(token: str, user):
    """写入登录态缓存。"""
    _token_cache.set(f"token:{token}", user)
