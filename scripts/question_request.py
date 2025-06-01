import asyncio
import httpx
import json
import os

from mcpbot.shared.config import COMPANY, PORT
from mcpbot.client.endpoints.messages.create import CreateMessageResponse


OPTION = 1
EMAIL = f"georgios.gkenios@{COMPANY.lower()}.com"

match OPTION:
    case 1:
        QUESTION = "What are the holidays for this year?"
    case 2:
        QUESTION = "Can you book a 2-monitor desk for next Sunday morning?"
    case 3:
        QUESTION = "Can you unbook my desk for next Sunday?"
    case _:
        raise SystemExit("Invalid option. Please choose 1, 2, or 3.")


async def main() -> None:
    # Get an acess token
    provider_token = os.popen("gcloud auth print-identity-token").read().strip()
    response = httpx.post(
        url=f"http://localhost:{PORT}/token",
        data={"token": provider_token},
    )
    token = response.json()["access_token"]

    async with httpx.AsyncClient(timeout=None) as client:
        # Create a conversation
        response = await client.post(
            url=f"http://localhost:{PORT}/v1/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        conversation_id = response.json()["id"]

        # Send a message to the conversation
        async with client.stream(
            method="POST",
            url=f"http://localhost:{PORT}/v1/conversations/{conversation_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": QUESTION},
        ) as response:
            async for chunk in response.aiter_bytes():
                response = CreateMessageResponse(**json.loads(chunk))  # type: ignore[assignment]
                print(response.ai.text, end="", flush=True)  # type: ignore[attr-defined]


if __name__ == "__main__":
    asyncio.run(main())
