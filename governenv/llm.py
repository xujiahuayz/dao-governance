"""
Class for the LLM model
"""

import time
from typing import Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from governenv.settings import OPENAI_API_KEY


def build_batch(
    custom_id: str,
    user_msg: str,
    system_instruction: str,
    json_schema: dict,
    model: str = "gpt-4.1",
    temperature: Optional[float] = 0,
) -> dict:
    """
    Function to build a batch for OpenAI API
    """

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_msg},
    ]

    batch_item = {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": json_schema,
            },
        },
    }

    if temperature is not None:
        batch_item["body"]["temperature"] = temperature

    return batch_item


class ChatGPT:
    """
    ChatGPT class to interact with the OpenAI API
    """

    def __init__(
        self,
        model: str = "gpt-4.1",
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

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def __call__(
        self,
        message: str,
        instruction: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0,
        logprobs: bool = False,
        top_logprobs: int | None = None,
    ) -> str | tuple[str, dict[str, float]]:
        time.sleep(2)

        params = {
            "model": self.model,
            "messages": self._build_prompt(message, instruction),
            "temperature": temperature,
        }

        if json_schema:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": json_schema,
            }

        if logprobs:
            params["logprobs"] = logprobs
            params["top_logprobs"] = top_logprobs

        response = self.client.chat.completions.create(**params).choices[0]
        if logprobs:
            return (
                response.message.content,
                response.logprobs.content,
            )
        return response.message.content

    def send_batch(
        self,
        batch_path: str,
    ) -> str:
        """Function to send a batch request to the GPT-4o API."""
        batch_input_file = self.client.files.create(
            file=open(batch_path, "rb"),
            purpose="batch",
        )
        batch_input_file_id = batch_input_file.id

        batch = self.client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        return batch.id

    def retrieve_batch(self, batch_id: str) -> dict:
        """Function to retrieve the status of a batch request."""
        while True:
            current_batch = self.client.batches.retrieve(batch_id)
            status = current_batch.status
            print(f"Batch status: {status}")
            if status in ("completed", "failed", "cancelled", "expired"):
                break
            time.sleep(10)  # Wait before polling again

        if status != "completed":
            raise RuntimeError(f"Batch ended with status: {status}")

        # Download output file
        output_file_id = current_batch.output_file_id

        return self.client.files.content(output_file_id).content


if __name__ == "__main__":
    chat_gpt = ChatGPT()
    response = chat_gpt(
        "Is Shanghai the capital of China?",
        logprobs=True,
    )
    print(response)
