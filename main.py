import os
import discord
import asyncio
import aiohttp
import io
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands

intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set.")
if CHANNEL_ID <= 0:
    raise RuntimeError("DISCORD_CHANNEL_ID environment variable is not set or invalid.")

async def create_welcome_card(member: discord.Member) -> io.BytesIO:
    avatar_url = member.display_avatar.replace(size=1024, format="png").url
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as response:
            response.raise_for_status()
            avatar_bytes = await response.read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar_size = 330
    avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
    avatar.putalpha(mask)

    card_width, card_height = 900, 520
    card = Image.new("RGB", (card_width, card_height), (18, 18, 18))
    draw = ImageDraw.Draw(card)

    def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        font_names = ["arialbd.ttf", "arial.ttf", "seguisb.ttf", "segoeui.ttf"]
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except OSError:
                continue
        return ImageFont.load_default()

    title_font = load_font(40, bold=True)
    subtitle_font = load_font(28)

    title_text = f"{member.display_name} just joined the server"
    subtitle_text = f"Member #{member.discriminator}" if member.discriminator else "New member"

    draw.text((card_width / 2, 70), title_text, font=title_font, anchor="mm", fill=(255, 255, 255))
    draw.text((card_width / 2, 120), subtitle_text, font=subtitle_font, anchor="mm", fill=(200, 200, 200))

    border_size = avatar_size + 20
    border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.ellipse((0, 0, border_size, border_size), fill=(35, 35, 35, 255))
    border_draw.ellipse((10, 10, border_size - 10, border_size - 10), fill=(0, 0, 0, 0))
    avatar_top = 170
    card.paste(border, ((card_width - border_size) // 2, avatar_top), border)
    card.paste(avatar, ((card_width - avatar_size) // 2, avatar_top + 10), avatar)

    output = io.BytesIO()
    card.save(output, format="PNG")
    output.seek(0)
    return output

@client.event
async def on_ready():
    print("The bot is now online!")

@client.event
async def on_member_join(member):
    channel = client.get_channel(CHANNEL_ID)
    if channel is not None:
        welcome_text = f"Hey {member.mention}, welcome to **TEAM STARK ⟡𓆪**!"
        card = await create_welcome_card(member)
        file = discord.File(card, filename="welcome_card.png")
        embed = discord.Embed(color=discord.Color.dark_grey())
        embed.set_image(url="attachment://welcome_card.png")
        await channel.send(content=welcome_text, embed=embed, file=file)
    else:
        print("Channel not found. Please check the CHANNEL_ID.")

async def main():
    async with client:
        await client.start(TOKEN)

asyncio.run(main())