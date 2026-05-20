import logging
import time

from openai import APIStatusError, OpenAI, RateLimitError

from app.config.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODELS,
    OPENROUTER_RETRY_ATTEMPTS,
    OPENROUTER_RETRY_DELAY_SEC,
)

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


def parse_with_retry(text_format, prompt: str):
    last_error = None

    for model in OPENROUTER_MODELS:
        for attempt in range(1, OPENROUTER_RETRY_ATTEMPTS + 1):
            try:
                response = client.responses.parse(
                    model=model,
                    input=prompt,
                    text_format=text_format,
                )
                return response.output_parsed
            except RateLimitError as error:
                last_error = error
                wait = OPENROUTER_RETRY_DELAY_SEC * attempt
                logger.warning(
                    "Rate limit on %s (attempt %s/%s), wait %ss",
                    model,
                    attempt,
                    OPENROUTER_RETRY_ATTEMPTS,
                    wait,
                )
                time.sleep(wait)
            except APIStatusError as error:
                last_error = error
                if error.status_code == 429:
                    wait = OPENROUTER_RETRY_DELAY_SEC * attempt
                    logger.warning(
                        "429 on %s (attempt %s/%s), wait %ss",
                        model,
                        attempt,
                        OPENROUTER_RETRY_ATTEMPTS,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                raise

        logger.warning("Model %s failed, trying next fallback", model)

    raise last_error or RuntimeError("All AI models failed")
