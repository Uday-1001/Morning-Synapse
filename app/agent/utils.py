import time
from groq import RateLimitError, APIError

def call_with_retry(client_call, *args, **kwargs):
    max_retries = 1
    backoff = 2
    for attempt in range(max_retries):
        try:
            return client_call(*args, **kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = backoff ** attempt
            time.sleep(wait_time)
        except APIError as e:
            if e.status_code == 429:
                if attempt == max_retries - 1:
                    raise e
                wait_time = backoff ** attempt
                time.sleep(wait_time)
            else:
                raise e
