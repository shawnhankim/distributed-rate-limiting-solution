"""Business Logic for Rate Limiter Status API"""

from core.common.constants import RateLimitPer as Per
from core.common.utils import data_not_found
from http import HTTPStatus


class RateLimitStatus:
    """Business Logic for Rate Limit Status API"""

    def __init__(self, namespace=None, datastore=None):
        self.namespace = namespace
        self.datastore = datastore

    def list(self):
        res = []
        for bucket in self.datastore.list_buckets():
            res.append(self._data(bucket))
        return res, 200 if res else 404

    def get(self, user_id='global'):
        item = self.datastore.get_bucket(user_id)
        if item and len(item) > 0:
            return self._data(item), HTTPStatus.OK
        data_not_found(user_id, self.namespace)

    def _data(self, bucket):
        return {
            'bucket_name': bucket['user_id'],
            'quota_limit': int(bucket['quota_limit']),
            'quota_remaining': int(bucket['quota_remaining']),
            'limit_per': Per.SEC,
            'last_update': float(bucket['last_update'])
        }
