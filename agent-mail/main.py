import os
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

async def main() -> None:
    message = await client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude",
            }
        ],
        model="claude-haiku-4-5-20251001",
    )
    print(message.content)

asyncio.run(main())