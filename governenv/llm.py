"""
Class for the LLM model
"""

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from governenv.settings import OPENAI_API_KEY


class ChatGPT:
    """
    ChatGPT class to interact with the OpenAI API
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = OPENAI_API_KEY,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _build_prompt(
        self,
        message: str,
        instruction: str | None = None,
    ) -> list[dict[str, str]]:
        """
        Function to build the prompt
        """

        prompt = [{"role": "system", "content": message}]

        if instruction:
            prompt = [{"role": "system", "content": instruction}] + prompt

        return prompt

    # @retry(
    #     stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    # )
    def __call__(
        self,
        message: str,
        instruction: str | None = None,
        max_tokens: int = 200,
        temperature: float = 0.1,
        logprobs: bool = False,
        top_logprobs: int | None = None,
    ):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_prompt(message, instruction),
            max_tokens=max_tokens,
            temperature=temperature,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
        ).choices[0]

        if logprobs:
            return (
                response.message.content,
                response.logprobs.content,
            )
        return response.message.content
