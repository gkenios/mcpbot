import asyncio
import httpx

from mcpbot.shared.config import PORT


OPTION = 1
CONVERSATION_ID = "mcpbot"
EMAIL = "georgios.gkenios@devoteam.com"

match OPTION:
    case 1:
        QUESTION = "What are the holidays for this year?"
    case 2:
        QUESTION = "Can you book a desk for me for next Sunday? I need a dual screen."
    case 3:
        QUESTION = "Can you unbook my desk for next Sunday?"
    case _:
        raise SystemExit("Invalid option. Please choose 1, 2, or 3.")


async def main():
    token = httpx.post(
        url=f"http://localhost:{PORT}/token",
        data={"username": EMAIL, "password": "gg"},
    ).json()["access_token"]

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            method="POST",
            url=f"http://localhost:{PORT}/v1/{CONVERSATION_ID}/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"message": QUESTION}
        ) as response:
            async for chunk in response.aiter_text():
                await asyncio.sleep(0.01)
                print(chunk, end="")


if __name__ == "__main__":
    asyncio.run(main())
