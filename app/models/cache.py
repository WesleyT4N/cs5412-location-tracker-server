from flask_caching.backends import MemcachedCache
import bmemcached


class BMemcachedCache(MemcachedCache):
    def __init__(
        self,
        servers=None,
        default_timeout=300,
        key_prefix=None,
        username=None,
        password=None,
        **kwargs
    ):
        super(BMemcachedCache, self).__init__(default_timeout)

        if servers is None:
            servers = ["127.0.0.1:11211"]

        self._client = bmemcached.Client(
            servers, username=username, password=password
        )

        self.key_prefix = key_prefix

    def set(self, key, value, timeout=None):
        key = self._normalize_key(key)
        timeout = self._normalize_timeout(timeout)
        return self._client.set(key, value, time=timeout)


def cache(app, config, args, kwargs):
    return BMemcachedCache(
        servers=config["CACHE_MEMCACHED_SERVERS"],
        username=config["CACHE_MEMCACHED_USERNAME"],
        password=config["CACHE_MEMCACHED_PASSWORD"],
        *args, **kwargs,
    )
