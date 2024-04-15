import time
import hashlib
import json
import itertools


class BulkCovarianceCache:
    def __init__(self, ttl=1000):
        self.cache = {}
        self.ttl = ttl  # Time-to-live in seconds  #TODO: not used

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
                if key_hashed not in self.cache:  # Assuming TTL handling is to be implemented later
                    missing_pairs.append(key_hashed)
        #NOTE: at first run (cache empty): len(missing_pairs) ==  0.5 * len(listSearchKeys) * (len(listSearchKeys) - 1) + len(listSearchKeys)
        if missing_pairs:
            missing_ts_keys = list(set(itertools.chain.from_iterable(map(lambda x: x.split("/")[0].split(":"), missing_pairs))))
            missing_ts_keys = [k for k in listSearchKeys if k in missing_ts_keys]
            svc_missing = svc
            svc_missing['listSearchKeys'] = [{'tsKey': key} for key in missing_ts_keys]
            new_covariances = await wrapper.get_lower_triangular_square_covariance(svc_missing)

            # Bulk update the cache with new covariances
            for pair in missing_pairs:
                self.cache[pair] = new_covariances[pair.split("/")[0]]

        # Retrieve all requested covariances from the cache
        results = {pair.split("/")[0]: self.cache[pair] for pair in cache_keys}
        return results