import io
import os
import asyncio
import discord
from discord.ext import commands
import textwrap
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from colorthief import ColorThief

# Resolve font directory relative to the project root (two levels up from this file)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FONTS_DIR = os.path.join(_PROJECT_ROOT, "fonts")


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Try bundled font → common system fonts → Pillow default (scaled)."""
    # 1) Bundled font
    bundled = os.path.join(_FONTS_DIR, name)
    if os.path.isfile(bundled):
        return ImageFont.truetype(bundled, size)
    # 2) System fonts (Windows paths)
    for system_dir in [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/noto",
    ]:
        system_path = os.path.join(system_dir, name)
        if os.path.isfile(system_path):
            return ImageFont.truetype(system_path, size)
    # 3) Try common Windows fallbacks by name
    for fallback in ["arial.ttf", "segoeui.ttf", "calibri.ttf"]:
        try:
            return ImageFont.truetype(fallback, size)
        except (IOError, OSError):
            continue
    # 4) Absolute last resort – Pillow default (bitmap, not scalable)
    return ImageFont.load_default()


class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _build_quote_image(
        avatar_data: bytes,
        text: str,
        display_name: str,
        username: str,
        transparent: bool,
    ) -> io.BytesIO:
        avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")
        color_thief = ColorThief(io.BytesIO(avatar_data))
        dominant_color = color_thief.get_color(quality=1)
        darkened_color = tuple([max(0, c - 40) for c in dominant_color])

        avatar_size = 220
        padding = 40
        max_width = 1200
        border_width = 5

        font_regular = _load_font("NotoSans-Regular.ttf", 44)
        font_italic = _load_font("NotoSans-Italic.ttf", 34)
        font_small = _load_font("NotoSans-Regular.ttf", 28)

        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        text_width = min(max_width - avatar_size - padding * 2, 900)
        # Measure real average character width to wrap accurately
        sample = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        sample_bbox = draw.textbbox((0, 0), sample, font=font_regular)
        avg_char_w = (sample_bbox[2] - sample_bbox[0]) / len(sample)
        usable_width = text_width - 80  # leave comfortable margin
        chars_per_line = max(18, int(usable_width / avg_char_w))
        wrapped_text = textwrap.fill(text, width=chars_per_line)
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font_regular)
        text_height = text_bbox[3] - text_bbox[1]

        name_bbox = draw.textbbox((0, 0), display_name, font=font_italic)
        user_bbox = draw.textbbox((0, 0), username, font=font_small)
        name_height = name_bbox[3] - name_bbox[1] + user_bbox[3] - user_bbox[1] + 10

        total_height = max(340, text_height + name_height + padding * 2 + 70)
        total_width = avatar_size + text_width + padding * 2

        bg_color = (0, 0, 0, 0) if transparent else (0, 0, 0, 255)
        main_image = Image.new('RGBA', (total_width, total_height), bg_color)
        draw = ImageDraw.Draw(main_image)

        mask = Image.new('L', (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        avatar = avatar.resize((avatar_size, avatar_size)).convert("RGBA")
        avatar.putalpha(mask)

        avatar_x = padding
        avatar_y = (total_height - avatar_size) // 2
        border_size = avatar_size + border_width * 2
        border_layer = Image.new('RGBA', (border_size, border_size), (0, 0, 0, 0))
        ImageDraw.Draw(border_layer).ellipse((0, 0, border_size, border_size), fill=darkened_color)
        main_image.paste(border_layer, (avatar_x - border_width, avatar_y - border_width), border_layer)
        main_image.paste(avatar, (avatar_x, avatar_y), avatar)

        text_x = avatar_size + padding * 2 + 10
        text_bg_width = total_width - text_x - padding
        gradient = Image.new('RGBA', (text_bg_width, total_height), color=0)
        for x in range(text_bg_width):
            opacity = int(255 * (0.5 + 0.5 * (x / text_bg_width)))
            gradient.putpixel((x, 0), (*darkened_color, opacity))
        main_image.paste(gradient, (text_x, 0), gradient)

        text_y = (total_height - text_height - name_height - 40) // 2
        draw.multiline_text(
            (text_x + 25, text_y),
            wrapped_text,
            font=font_regular,
            fill=(255, 255, 255, 255),
            spacing=14,
            embedded_color=True
        )

        max_line_width = max(
            draw.textbbox((0, 0), display_name, font=font_italic)[2],
            draw.textbbox((0, 0), username, font=font_small)[2]
        )
        username_x = text_x + text_bg_width - 25 - max_line_width
        draw.text((username_x, text_y + text_height + 25), display_name, font=font_italic, fill=(255, 255, 255, 230))
        draw.text((username_x, text_y + text_height + 25 + (name_bbox[3] - name_bbox[1]) + 5), username, font=font_small, fill=(255, 255, 255, 200))

        final_image = ImageOps.expand(main_image, border=border_width, fill=darkened_color).convert("RGBA")
        shadow = final_image.filter(ImageFilter.GaussianBlur(radius=10))
        combined_image = Image.new('RGBA', (final_image.width + 20, final_image.height + 20), (0, 0, 0, 0))
        combined_image.paste(shadow, (10, 15), shadow)
        combined_image.paste(final_image, (10, 10), final_image)

        output = io.BytesIO()
        combined_image.save(output, format="PNG", bitmap_format="png")
        output.seek(0)
        return output

    @commands.slash_command(description="Creates a stylish quote image with a profile picture")
    async def quote(self, ctx: discord.ApplicationContext, 
                   text: str, 
                   user: discord.Member = None,
                   transparent: bool = False):
        await ctx.defer()
        target_user = user or ctx.author

        try:
            timeout = aiohttp.ClientTimeout(total=12)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                avatar_url = str(target_user.display_avatar.with_size(512).url)
                async with session.get(avatar_url) as response:
                    if response.status != 200:
                        return await ctx.followup.send("❌ Couldn't download avatar!")
                    avatar_data = await response.read()
            display_name = f"~ {target_user.display_name}"
            username = f"@{target_user.name}"
            output = await asyncio.to_thread(
                self._build_quote_image,
                avatar_data,
                text,
                display_name,
                username,
                transparent,
            )
            await ctx.followup.send(file=discord.File(output, "quote.png"))
            output.close()
        except asyncio.TimeoutError:
            await ctx.followup.send("❌ Avatar download timeout. Please try again.")
        except Exception as e:
            await ctx.followup.send(f"❌ Error generating image: {str(e)}")

def setup(bot):
    bot.add_cog(Quote(bot))
