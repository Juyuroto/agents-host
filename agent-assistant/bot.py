import logging
import discord

from agent import reply
from config import DISCORD_CHANNEL_ID

log = logging.getLogger("agent-assistant")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready() -> None:
    log.info("Connecté en tant que %s", client.user)


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.channel.id != DISCORD_CHANNEL_ID or not message.content:
        return
    answer = await reply(message.content)
    await message.channel.send(answer[:2000])
