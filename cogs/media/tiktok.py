import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import os
import requests
from io import BytesIO
from urllib.parse import urlparse

import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration
from handlers.env import get_tiktok_api_key

media_dir = "data/media"
API_KEY = get_tiktok_api_key()
MAX_FILE_SIZE = 8 * 1024 * 1024  
TIKTOK_ICON_URL = "https://cdn-icons-png.flaticon.com/512/3046/3046121.png"

def get_extension(url: str, default_ext: str) -> str:
    parsed = urlparse(url)
    path = parsed.path
    _, ext = os.path.splitext(path)
    if not ext or "/" in ext or len(ext) > 5:
        return default_ext
    return ext.lstrip(".")

def create_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=TIKTOK_ICON_URL)
    embed.set_footer(text="TikTok Downloader • maggi.dev API")
    return embed

def safe_embed_field_value(value: str, max_length: int = 1024) -> str:
    """Ensures that a Discord embed field value does not exceed the maximum allowed length."""
    if value is None:
        return ""
    value = str(value)
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value

class Tiktok(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @slash_command(name="media-tiktok", description="Download TikTok media (video or images with music)")
    async def media_tiktok(self, ctx: discord.ApplicationContext, link: str):
        os.makedirs(media_dir, exist_ok=True)

        # Initial processing embed
        processing_embed = create_embed(
            title="🔍 Processing Request",
            description="Initializing TikTok download...",
            color=discord.Color.blue()
        )
        await ctx.defer()
        await ctx.respond(embed=processing_embed)

        try:
            # Fetch API data
            api_url = f"https://api.maggi.dev/tiktok?url={link}"
            LogDebug(f"Requesting API URL: {api_url}")
            api_response = requests.get(api_url)

            if api_response.status_code != 200:
                raise Exception(f"API returned HTTP {api_response.status_code}")

            api_data = api_response.json()

            # Handle API errors
            if "error" in api_data:
                error_msg = api_data["error"]
                if "Invalid TikTok URL" in error_msg:
                    raise Exception("❌ Invalid TikTok URL provided")
                elif "Invalid API key" in error_msg:
                    LogError("Invalid TikTok API key used")
                    raise Exception("🔑 API Service Error (Code 500)")
                raise Exception(f"API Error: {error_msg}")

            if api_data.get("status") != "success":
                raise Exception("API returned non-success status")

            # Update status embed
            processing_embed = create_embed(
                title="⏳ Downloading Content",
                description="Fetching media from TikTok...",
                color=discord.Color.dark_purple()
            )
            await ctx.interaction.edit_original_response(embed=processing_embed)

            result = api_data.get("result", {})
            attachments = []
            big_file_links = []
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            media_type = result.get("type", "").lower()

            # Download media content
            if media_type == "video" or not (result.get("images") and len(result.get("images")) > 0):
                video_info = result.get("video", {})
                play_addrs = video_info.get("playAddr", [])
                video_downloaded = False

                for url in play_addrs:
                    vid_resp = requests.get(url)
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
                if not video_downloaded:
                    raise Exception("Video download failed")
            else:
                images = result.get("images")
                for idx, image_url in enumerate(images):
                    img_resp = requests.get(image_url)
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
                    mus_resp = requests.get(m_url)
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
            info_embed = create_embed(
                title="🎬 TikTok Media Information",
                description=safe_embed_field_value(result.get("description", "No description available")),
                color=discord.Color.green()
            )
            # Truncate the link if it's too long for the field
            display_link = "[Original Link]({})".format(link)
            info_embed.add_field(
                name="🔗 Source URL",
                value=safe_embed_field_value(display_link),
                inline=False
            )

            if author := result.get("author"):
                author_name = author.get("nickname", author.get("username", "Unknown"))
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

            # Final response
            success_embed = create_embed(
                title="✅ Download Complete",
                description="Successfully processed TikTok media",
                color=discord.Color.green()
            )
            await ctx.interaction.edit_original_response(embed=success_embed)

            content_msg = []
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
                await ctx.followup.send(embed=warning_embed)

            if attachments:
                for i in range(0, len(attachments), 10):
                    chunk = attachments[i:i + 10]
                    if i == 0:
                        await ctx.followup.send(
                            content="📁 Downloaded Attachments:",
                            embed=info_embed,
                            files=chunk,
                        )
                    else:
                        await ctx.followup.send(files=chunk)
            else:
                await ctx.followup.send(embed=info_embed)
        except Exception as e:
            error_embed = create_embed(
                title="❌ Critical Error",
                description=f"An unexpected error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.followup.send(embed=error_embed)
            LogError(f"TikTok command failed: {str(e)}")

def setup(bot: discord.Bot):    bot.add_cog(Tiktok(bot))
