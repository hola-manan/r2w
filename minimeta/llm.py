# minimeta/llm.py
import os
from google import genai
from google.genai import types, errors
import asyncio

DEFAULT_MODEL = "gemini-2.5-flash-lite"  # higher free-tier quota; agents make many calls


class LLM:
    """Thin async wrapper around the Gemini SDK (google.genai).

    Public surface is unchanged: every Role owns an LLM, everyone calls aask().
    """

    def __init__(self, system_prompt: str | None = None, model: str = DEFAULT_MODEL):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Environment variable 'GEMINI_API_KEY' is not set")
        # TODO 1: create self.client = genai.Client(api_key=api_key)
        self.client = genai.Client(api_key=api_key)
        # TODO 2: store self.model = model
        self.model = model
        # TODO 3: store self.system_prompt = system_prompt
        self.system_prompt = system_prompt
    

    async def aask(self, prompt: str, json_mode: bool = False, max_retries: int = 4) -> str:
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            response_mime_type="application/json" if json_mode else None,
        )
        for attempt in range(max_retries):
            try:
                resp = await self.client.aio.models.generate_content(
                    model=self.model, contents=prompt, config=config,
                )
                return resp.text
            except errors.ClientError as e:
                # TODO 1: only retry on rate-limit (HTTP 429); re-raise anything else immediately
                #         (hint: e.code == 429). On the LAST attempt, also re-raise.
                if e.code != 429 or attempt == max_retries:
                    raise
                timeout = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, 8s
                # TODO 2: wait with EXPONENTIAL BACKOFF before retrying, e.g.
                #         await asyncio.sleep(2 ** attempt)   # 1s, 2s, 4s, 8s
                await asyncio.sleep(timeout)


