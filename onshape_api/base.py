from abc import ABC
from requests.auth import HTTPBasicAuth
import functools
import time
from requests_cache import CachedSession

BASE_URL = "https://cad.onshape.com/api/v10"


def api_request(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        while True:
            response = func(*args, **kwargs)
            if not response.ok:
                print(response.text)
                print(f"Too Many Requests {func}")
                time.sleep(120.0)
                continue
            return response

    return wrap


class BaseOnshapeAPI(ABC):
    """Base Class for managing REST calls to the OnshapeAPI"""

    def __init__(self, access_key: str, private_key: str, url_extension: str = ""):
        self.session = CachedSession(
            f"{url_extension}-cache", expire_after=36000, allowable_codes=[200]
        )
        self._access_key: str = access_key
        self._private_key: str = private_key
        self._url_extension: str = url_extension
        self._auth = HTTPBasicAuth(self._access_key, self._private_key)
