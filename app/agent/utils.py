import time
import logging
from groq import RateLimitError, APIError, APIConnectionError

logger = logging.getLogger(__name__)

def call_with_retry(client_call, *args, **kwargs):
    max_retries = 3
    backoff = 2
    for attempt in range(max_retries):
        try:
            return client_call(*args, **kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = backoff ** attempt
            logger.warning(f"RateLimitError encountered. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
            time.sleep(wait_time)
        except APIConnectionError as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = backoff ** attempt
            logger.warning(f"APIConnectionError (network timeout/disconnect). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
            time.sleep(wait_time)
        except APIError as e:
            if hasattr(e, "status_code") and e.status_code == 429:
                if attempt == max_retries - 1:
                    raise e
                wait_time = backoff ** attempt
                logger.warning(f"API Status 429 (Rate Limit) encountered. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
