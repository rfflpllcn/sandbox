import time
import hashlib
import json
import itertools


class Throttler:
    """
    tracks the number of fetch operations within a specified time window.
    If the count exceeds a threshold, subsequent operations can be delayed or dropped until the next time window.
    """
    def __init__(self, limit, window):
        self.calls = 0
        self.limit = limit
        self.window = window
        self.reset_time = time.time() + window

    def allow(self):
        current_time = time.time()
        if current_time > self.reset_time:
            self.calls = 0
            self.reset_time = current_time + self.window
        if self.calls < self.limit:
            self.calls += 1
            return True
        return False


class BulkCovarianceCache:
    def __init__(self, ttl=1000, request_limit=10, time_window=60):
        self.cache = {}
        self.ttl = ttl  # Time-to-live in seconds  #TODO: not used
        self.throttler = Throttler(request_limit, time_window)

    async def get_covariances(self,  wrapper, svc):
        # TODO: parametrize by KF, LF

        # hash svc['calcCovarianceParameter']
        serialized_data = json.dumps(svc['calcCovarianceParameter'], sort_keys=True)
        hash_object = hashlib.sha256(serialized_data.encode())
        hash_hex = hash_object.hexdigest()

        now = time.time()
        # Generate a unique cache key for each pair considering F
        cache_keys = []
        missing_pairs = []
        # Ensure we only generate and check unique pairs considering symmetry
        listSearchKeys = [elem['tsKey'] for elem in svc['listSearchKeys']]
        for i, row in enumerate(listSearchKeys):
            for col in listSearchKeys[i:]:  # Start from current row to avoid duplicates
                # key = f"{min(row, col)}:{max(row, col)}"
                key = f"{row}:{col}"
                key_hashed = f"{key}/{hash_hex}"
                cache_keys.append(key_hashed)
                if key_hashed not in self.cache:  # or (now - self.cache[key_hashed]['timestamp'] > self.ttl)
                    missing_pairs.append(key_hashed)
        #NOTE: at first run (cache empty): len(missing_pairs) ==  0.5 * len(listSearchKeys) * (len(listSearchKeys) - 1) + len(listSearchKeys)
        if missing_pairs and self.throttler.allow():
            missing_ts_keys = list(set(itertools.chain.from_iterable(map(lambda x: x.split("/")[0].split(":"), missing_pairs))))
            missing_ts_keys = [k for k in listSearchKeys if k in missing_ts_keys]
            svc_missing = svc.copy()
            svc_missing['listSearchKeys'] = [{'tsKey': key} for key in missing_ts_keys]
            new_covariances = await wrapper.get_lower_triangular_square_covariance(svc_missing)

            # Bulk update the cache with new covariances
            for pair in missing_pairs:
                self.cache[pair] = new_covariances[pair.split("/")[0]] # self.cache[pair] = {'value': new_covariances[row_col], 'timestamp': now}

        # Retrieve all requested covariances from the cache
        results = {pair.split("/")[0]: self.cache[pair] for pair in cache_keys}
        return results