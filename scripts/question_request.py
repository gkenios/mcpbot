import asyncio
import httpx
import json

from mcpbot.shared.config import COMPANY, PORT
from mcpbot.client.messages.create import CreateMessageResponse


OPTION = 1
EMAIL = f"georgios.gkenios@{COMPANY.lower()}.com"

match OPTION:
    case 1:
        QUESTION = "What are the holidays for this year?"
    case 2:
        QUESTION = "Can you book a 2-monitor desk for me for next Sunday?"
    case 3:
        QUESTION = "Can you unbook my desk for next Sunday?"
    case _:
        raise SystemExit("Invalid option. Please choose 1, 2, or 3.")


async def main() -> None:
    token = "-"
    async with httpx.AsyncClient(timeout=None) as client:
        # Create a conversation
        response = await client.post(
            url=f"http://localhost:{PORT}/v1/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        conversation_id = response.json()["id"]

        # Send a message to the conversation
        async with client.stream(
            method="POST",
            url=f"http://localhost:{PORT}/v1/conversations/{conversation_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": QUESTION},
        ) as response:
            async for chunk in response.aiter_bytes():
                response = CreateMessageResponse(**json.loads(chunk))
                print(response.ai.text, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
