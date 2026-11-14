import discord
from discord.ext import commands
from discord.commands import slash_command
import os
import re
import requests
from io import BytesIO
from urllib.parse import urlparse
import datetime

import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration
from handlers.env import get_tiktok_api_key
from utils.embed_helpers import create_embed as utils_create_embed

media_dir = "data/media"
API_KEY = get_tiktok_api_key()
MAX_FILE_SIZE = 25 * 1024 * 1024
TIKTOK_ICON_URL = "https://cdn-icons-png.flaticon.com/512/3046/3046121.png"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

TIKTOK_PATTERN = re.compile(
    r"(?:https?://)?(?:[a-zA-Z0-9_-]+\.)?(?:tiktok\.com|tt\.site)/\S+",
    re.IGNORECASE
)

PUNCT_STRIP_RIGHT = r"[\s.,!?:;)>*~_|\"\'\]\}]+$"
PUNCT_STRIP_LEFT = r"^[\s<([{\"\'*_~|]+"

def clean_raw_match(raw: str) -> str:
    s = re.sub(PUNCT_STRIP_LEFT, "", raw)
    s = re.sub(PUNCT_STRIP_RIGHT, "", s)
    if not s.lower().startswith(("http://", "https://")):
        s = "https://" + s
    return s

def canonicalize_tiktok_url(url: str) -> str:
    # Check if direct video or photo with ID: tiktok.com/@user/video/123 or tiktok.com/@user/photo/123
    m = re.search(r"tiktok\.com/(@?[^/?#\s]+)/(video|photo)/(\d+)", url, re.IGNORECASE)
    if m:
        user = m.group(1)
        if not user.startswith("@"):
            user = "@" + user
        media_type = m.group(2).lower()
        media_id = m.group(3)
        return f"https://www.tiktok.com/{user}/{media_type}/{media_id}"
    return url

def extract_tiktok_urls(text: str) -> list[str]:
    if not text or not isinstance(text, str):
        return []
    matches = TIKTOK_PATTERN.findall(text)
    urls = []
    for m in matches:
        cleaned = clean_raw_match(m)
        if cleaned and cleaned not in urls:
            urls.append(cleaned)
    return urls

def resolve_tiktok_url(url: str) -> str:
    trimmed = clean_raw_match(url)
    try:
        # Check if it's a shortlink or redirect-based link
        if re.search(r"tt\.site|v[mt]\.tiktok\.com|tiktok\.com/t/|m\.tiktok\.com", trimmed, re.IGNORECASE):
            headers = {"User-Agent": DEFAULT_USER_AGENT}
            resp = requests.get(trimmed, headers=headers, allow_redirects=True, stream=True, timeout=8)
            if resp.url and resp.url != trimmed:
                return canonicalize_tiktok_url(resp.url)
    except Exception as e:
        LogDebug(f"Redirect resolve error: {e}")
    return canonicalize_tiktok_url(trimmed)

def get_extension(url: str, default_ext: str) -> str:
    parsed = urlparse(url)
    path = parsed.path
    _, ext = os.path.splitext(path)
    if not ext or "/" in ext or len(ext) > 5:
        return default_ext
    return ext.lstrip(".")

def create_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    embed = utils_create_embed(
        title=title,
        description=description,
        color=color,
        thumbnail=TIKTOK_ICON_URL,
        footer_text="TikTok Downloader • maggi.dev API",
        timestamp=True
    )
    return embed

def safe_embed_field_value(value: str, max_length: int = 1024) -> str:
    """Ensures that a Discord embed field value does not exceed the maximum allowed length."""
    if value is None:
        return ""
    value = str(value)
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value

class TikTokSuggestionView(discord.ui.View):
    def __init__(self, author_id: int, url: str, cog: "Tiktok"):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.url = url
        self.cog = cog

    @discord.ui.button(label="TikTok herunterladen", emoji="📥", style=discord.ButtonStyle.success)
    async def download_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except Exception:
            pass
        await self.cog.process_download(interaction=interaction, link=self.url)

    @discord.ui.button(label="Verwerfen", emoji="✖️", style=discord.ButtonStyle.secondary)
    async def dismiss_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Nur der Verfasser der Nachricht kann diesen Vorschlag verwerfen.",
                ephemeral=True
            )
            return
        try:
            await interaction.message.delete()
        except Exception:
            pass

class Tiktok(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    async def process_download(self, interaction: discord.Interaction, link: str):
        os.makedirs(media_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            resolved_url = resolve_tiktok_url(link)
            LogDebug(f"Resolved TikTok URL: {link} -> {resolved_url}")

            api_base = "https://api.maggi.dev/tiktok"
            api_key = API_KEY or get_tiktok_api_key()
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            api_response = requests.get(api_base, params={"url": resolved_url}, headers=headers, timeout=15)

            if api_response.status_code != 200:
                raise requests.HTTPError(f"API returned HTTP {api_response.status_code}", response=api_response)

            api_data = api_response.json()

            if "error" in api_data:
                error_msg = api_data["error"]
                if "Invalid TikTok URL" in error_msg:
                    raise Exception("Invalid TikTok URL provided")
                elif "Invalid API key" in error_msg:
                    LogError("Invalid TikTok API key used")
                    raise Exception("API Service Error (Code 500)")
                raise Exception(f"API Error: {error_msg}")

            if api_data.get("status") != "success":
                raise Exception("API returned non-success status")

            result = api_data.get("result", {})
            attachments = []
            big_file_links = []
            media_type = result.get("type", "").lower()
            media_headers = {"User-Agent": DEFAULT_USER_AGENT}

            # Download media content
            if media_type == "video" or not (result.get("images") and len(result.get("images")) > 0):
                video_info = result.get("video", {})
                play_addrs = video_info.get("playAddr", [])
                video_downloaded = False

                for url in play_addrs:
                    vid_resp = requests.get(url, headers=media_headers, timeout=30)
                    if vid_resp.status_code == 200:
                        ext = get_extension(url, "mp4")
                        video_filename = os.path.join(media_dir, f"tiktok_video_{timestamp}.{ext}")

                        with open(video_filename, "wb") as vid_file:
                            vid_file.write(vid_resp.content)

                        file_size = os.path.getsize(video_filename)
                        if file_size > MAX_FILE_SIZE:
                            big_file_links.append(url)
                            os.remove(video_filename)
                        else:
                            with open(video_filename, "rb") as f:
                                file_data = BytesIO(f.read())
                            file_data.seek(0)
                            attachments.append(discord.File(fp=file_data, filename=os.path.basename(video_filename)))
                            os.remove(video_filename)
                        video_downloaded = True
                        break
                if not video_downloaded and not big_file_links:
                    raise Exception("Video download failed")
            else:
                images = result.get("images", [])
                for idx, image_url in enumerate(images):
                    img_resp = requests.get(image_url, headers=media_headers, timeout=15)
                    if img_resp.status_code == 200:
                        ext = get_extension(image_url, "jpg")
                        img_filename = os.path.join(media_dir, f"tiktok_image_{timestamp}_{idx}.{ext}")

                        with open(img_filename, "wb") as img_file:
                            img_file.write(img_resp.content)

                        file_size = os.path.getsize(img_filename)
                        if file_size > MAX_FILE_SIZE:
                            big_file_links.append(image_url)
                            os.remove(img_filename)
                        else:
                            with open(img_filename, "rb") as f:
                                file_data = BytesIO(f.read())
                            file_data.seek(0)
                            attachments.append(discord.File(fp=file_data, filename=os.path.basename(img_filename)))
                            os.remove(img_filename)

            # Download music
            music = result.get("music", {})
            music_urls = music.get("playUrl", [])
            if music_urls:
                for m_url in music_urls:
                    mus_resp = requests.get(m_url, headers=media_headers, timeout=15)
                    if mus_resp.status_code == 200:
                        ext = get_extension(m_url, "mp3")
                        music_filename = os.path.join(media_dir, f"tiktok_music_{timestamp}.{ext}")

                        with open(music_filename, "wb") as mus_file:
                            mus_file.write(mus_resp.content)

                        file_size = os.path.getsize(music_filename)
                        if file_size > MAX_FILE_SIZE:
                            big_file_links.append(m_url)
                            os.remove(music_filename)
                        else:
                            with open(music_filename, "rb") as f:
                                file_data = BytesIO(f.read())
                            file_data.seek(0)
                            attachments.append(discord.File(fp=file_data, filename=os.path.basename(music_filename)))
                            os.remove(music_filename)
                        break

            # Create result embed
            raw_desc = result.get("desc") or result.get("description") or "No description available"
            info_embed = create_embed(
                title="🎬 TikTok Media Information",
                description=safe_embed_field_value(raw_desc),
                color=discord.Color.green()
            )
            display_link = f"[Original Link]({resolved_url})"
            info_embed.add_field(
                name="🔗 Source URL",
                value=safe_embed_field_value(display_link),
                inline=False
            )

            if author := result.get("author"):
                author_name = author.get("nickname") or author.get("uniqueId") or author.get("username") or "Unknown"
                if profile_url := author.get("url"):
                    info_embed.add_field(
                        name="👤 Author",
                        value=safe_embed_field_value(f"[{author_name}]({profile_url})"),
                        inline=True
                    )
                else:
                    info_embed.add_field(
                        name="👤 Author",
                        value=safe_embed_field_value(author_name),
                        inline=True
                    )

            info_embed.add_field(
                name="📁 Media Type",
                value=safe_embed_field_value(result.get("type", "N/A").capitalize()),
                inline=True
            )
            info_embed.add_field(
                name="📦 Attachments",
                value=safe_embed_field_value(str(len(attachments))),
                inline=True
            )

            if big_file_links:
                warning_embed = create_embed(
                    title="⚠️ Size Warning",
                    description=safe_embed_field_value(f"{len(big_file_links)} files exceed Discord's size limit"),
                    color=discord.Color.orange()
                )
                warning_embed.add_field(
                    name="Large Files",
                    value=safe_embed_field_value("\n".join(f"• [Link {idx+1}]({url})" for idx, url in enumerate(big_file_links))),
                    inline=False
                )
                await interaction.followup.send(embed=warning_embed)

            if attachments:
                for i in range(0, len(attachments), 10):
                    chunk = attachments[i:i + 10]
                    if i == 0:
                        await interaction.followup.send(
                            content="📁 Downloaded Attachments:",
                            embed=info_embed,
                            files=chunk,
                        )
                    else:
                        await interaction.followup.send(files=chunk)
            else:
                await interaction.followup.send(embed=info_embed)

        except Exception as e:
            error_embed = create_embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed)
            LogError(f"TikTok process_download failed: {str(e)}")

    @slash_command(
        name="media-tiktok",
        description="Download TikTok media (video or images with music)",
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm, discord.InteractionContextType.private_channel}
    )
    async def media_tiktok(self, ctx: discord.ApplicationContext, link: str):
        await ctx.defer()
        await self.process_download(interaction=ctx.interaction, link=link)

    @discord.message_command(name="Download TikTok Video")
    async def message_download_tiktok(self, ctx: discord.ApplicationContext, message: discord.Message):
        urls = extract_tiktok_urls(message.content)
        if not urls and message.embeds:
            for emb in message.embeds:
                if emb.url:
                    urls.extend(extract_tiktok_urls(emb.url))
                if emb.description:
                    urls.extend(extract_tiktok_urls(emb.description))

        if not urls:
            error_embed = create_embed(
                title="❌ Kein TikTok Link gefunden",
                description="In dieser Nachricht wurde kein gültiger TikTok-Link gefunden.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=error_embed, ephemeral=True)
            return

        await ctx.defer()
        await self.process_download(interaction=ctx.interaction, link=urls[0])

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        urls = extract_tiktok_urls(message.content)
        if not urls and message.embeds:
            for emb in message.embeds:
                if emb.url:
                    urls.extend(extract_tiktok_urls(emb.url))
                if emb.description:
                    urls.extend(extract_tiktok_urls(emb.description))

        if not urls:
            return

        first_url = urls[0]
        view = TikTokSuggestionView(author_id=message.author.id, url=first_url, cog=self)
        embed = create_embed(
            title="TikTok Link erkannt",
            description="Möchtest du dieses TikTok-Video herunterladen?",
            color=discord.Color.blue()
        )
        try:
            await message.reply(embed=embed, view=view, mention_author=False)
        except Exception as e:
            LogDebug(f"Failed to send TikTok suggestion: {e}")

def setup(bot: discord.Bot):
    bot.add_cog(Tiktok(bot))
