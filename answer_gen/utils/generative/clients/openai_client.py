import openai
import asyncio
import random
from io import BytesIO
import uuid
import logging

from answer_gen.exceptions import MissingGenerativeAction, GenerativeOutputError

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, api_key : str):
        """Create an async OpenAI client wrapper."""
        self._api_key = api_key
        self._client = openai.AsyncOpenAI(api_key= api_key)

    async def _send_request(self, method : str,
                            retries = 3,
                            hard_wait = 4,
                            max_wait = 60,
                            client = None,
                            *args, **kwargs):
        """Execute a retried OpenAI SDK `.create()` call with backoff."""
        client = client or self._client

        if not hasattr(client, method):
            raise MissingGenerativeAction(self, method)

        resource = getattr(client, method)
        last_exc: Exception | None = None

        # attempts are 1-indexed for backoff math
        for attempt in range(1, retries + 1):
            try:
                if attempt == 1:
                    logger.debug("Calling openai.%s.create retries=%s", method, retries)
                return await resource.create(*args, **kwargs)
            except openai.APITimeoutError as e:
                logger.warning("OpenAI timeout method=%s attempt=%s/%s", method, attempt, retries)
                last_exc = e
            except openai.InternalServerError as e:
                logger.warning("OpenAI internal server error method=%s attempt=%s/%s", method, attempt, retries)
                last_exc = e
            except openai.RateLimitError as e:
                logger.warning("OpenAI rate limited method=%s attempt=%s/%s", method, attempt, retries)
                last_exc = e
            except openai.BadRequestError as e:
                # Not retryable: request is invalid.
                logger.error("Bad OpenAI request method=%s error=%s", method, str(e))
                raise
            except openai.AuthenticationError as e:
                # Not retryable: credentials are invalid.
                logger.error("OpenAI authentication failed")
                raise
            except Exception as e:
                # Unknown error: surface immediately rather than hiding behind retries.
                logger.exception("Unexpected OpenAI client error method=%s", method)
                raise

            if attempt >= retries:
                break

            # Exponential backoff with jitter; rate limits get a slightly higher base.
            base = hard_wait * (2 if isinstance(last_exc, openai.RateLimitError) else 1)
            timeout = min(max_wait, base * (2 ** (attempt - 1)))
            timeout *= random.uniform(0.5, 1.5)
            logger.info("Retrying OpenAI call after backoff seconds=%.2f", timeout)
            await asyncio.sleep(timeout)

        logger.error("OpenAI call failed after retries method=%s retries=%s", method, retries)
        raise GenerativeOutputError("Failed to complete OpenAI request after retries.") from last_exc

    async def generate_text(self, model : str, prompt : str, retries = 3, hard_wait = 4):
        """Generate plain text output from the OpenAI Responses API."""
        logger.info("Generating text with OpenAI model=%s", model)

        try:
            out = await self._send_request(
                "responses",
                retries,
                hard_wait,
                model = model,
                input = prompt
            )
        except Exception:
            logger.exception("OpenAI text generation failed model=%s", model)
            raise

        return out.output_text

    async def generate_text_with_file(self, model : str, prompt : str, file : bytes, retries = 3, hard_wait = 4):
        """Generate text by sending both prompt text and an uploaded file."""
        logger.info("Generating text with file using OpenAI model=%s", model)
        try:
            file_id = await self._upload_file(file)

            out = await self._send_request(
                "responses",
                retries,
                hard_wait,
                model=model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_file", "file_id": file_id},
                            {"type": "input_text", "text": prompt},
                        ],
                    }
                ],
            )
        except Exception:
            logger.exception("OpenAI file-backed generation failed model=%s", model)
            raise

        return out.output_text

    async def _upload_file(self, file_bytes: bytes, retries: int = 2, hard_wait: int = 20):
        """Upload bytes to OpenAI Files API and return the file identifier."""
        # OpenAI expects a filename + content-type when uploading raw bytes.
        fn = str(uuid.uuid4())
        payload = (f"{fn}.pdf", BytesIO(file_bytes), "application/pdf")

        try:
            uploaded = await self._send_request(
                "files",
                retries,
                hard_wait,
                file=payload,
                purpose="user_data",
            )
        except Exception:
            logger.exception("OpenAI file upload failed payload_mime=application/pdf")
            raise

        if uploaded is None:
            logger.error("OpenAI file upload returned empty response")
            raise GenerativeOutputError("Failed to upload file to OpenAI.")

        return uploaded.id
