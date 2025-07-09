import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import os
import threading
import uuid
import yt_dlp as youtube_dl
from flask import Flask, send_file, abort
import time

media_dir = "data/media"
MAX_FILE_SIZE = 8 * 1024 * 1024
YOUTUBE_ICON_URL = "https://cdn-icons-png.flaticon.com/512/1384/1384060.png"

app = Flask("youtube_downloader")
_token_store = {}

@app.route('/download/<token>')
def download(token):
    info = _token_store.get(token)
    if not info:
        return abort(404)
    file_path = info['path']
    if time.time() > info['expires_at']:
        if os.path.exists(file_path):
            os.remove(file_path)
        _token_store.pop(token, None)
        return abort(404)
    return send_file(file_path, as_attachment=True)

def _cleanup_loop():
    while True:
        now = time.time()
        expired = [t for t, i in _token_store.items() if now > i['expires_at']]
        for t in expired:
            fp = _token_store[t]['path']
            if os.path.exists(fp):
                os.remove(fp)
            _token_store.pop(t, None)
        time.sleep(60)

_flask_started = False

def ensure_flask_running():
    global _flask_started
    if _flask_started:
        return
    _flask_started = True
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5006, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=_cleanup_loop, daemon=True).start()


def create_embed(title: str, description: str, color: discord.Color) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now())
    embed.set_thumbnail(url=YOUTUBE_ICON_URL)
    embed.set_footer(text="YouTube Downloader")
    return embed

class Youtube(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        ensure_flask_running()

    @slash_command(name="media-youtube", description="Download a YouTube video")
    async def media_youtube(self, ctx: discord.ApplicationContext, link: str):
        os.makedirs(media_dir, exist_ok=True)
        processing = create_embed("🔍 Processing Request", "Initializing YouTube download...", discord.Color.blue())
        await ctx.defer()
        await ctx.respond(embed=processing)

        filename_holder = {'name': None}

        def progress_hook(d):
            if d['status'] == 'finished':
                filename_holder['name'] = d['filename']

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(media_dir, '%(title)s-%(id)s.%(ext)s'),
            'noplaylist': True,
            'progress_hooks': [progress_hook],
            'quiet': True,
        }

        try:
            downloading = create_embed("⏳ Downloading", "Fetching media from YouTube...", discord.Color.dark_purple())
            await ctx.interaction.edit_original_response(embed=downloading)

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

            file_path = filename_holder['name']
            if not file_path or not os.path.exists(file_path):
                raise Exception("Download failed")

            token = uuid.uuid4().hex
            _token_store[token] = {
                'path': file_path,
                'expires_at': time.time() + 300
            }
            download_link = f"http://localhost:5006/download/{token}"

            file_size = os.path.getsize(file_path)
            attachments = []
            if file_size <= MAX_FILE_SIZE:
                with open(file_path, 'rb') as f:
                    attachments.append(discord.File(f, filename=os.path.basename(file_path)))

            success = create_embed("✅ Download Complete", "Your video is ready.", discord.Color.green())
            success.add_field(name="📥 Download", value=f"[Click here]({download_link}) (expires in 5 minutes)", inline=False)
            await ctx.interaction.edit_original_response(embed=success)

            if attachments:
                await ctx.followup.send(files=attachments)
            else:
                await ctx.followup.send(content=f"Download link: {download_link}")
        except Exception as e:
            error_embed = create_embed("❌ Error", f"An error occurred: {str(e)}", discord.Color.red())
            await ctx.followup.send(embed=error_embed)


def setup(bot: discord.Bot):
    bot.add_cog(Youtube(bot))
