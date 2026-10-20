# -*- coding: utf-8 -*-
import io
import os
import asyncio
import discord
from discord.ext import commands
import textwrap
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from colorthief import ColorThief
from handlers.locale import t

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
        border_width = 10

        font_text = _load_font("Caveat-Bold.ttf", 60)
        font_italic = _load_font("NotoSans-Italic.ttf", 28)
        font_small = _load_font("NotoSans-Regular.ttf", 22)

        wrapped_text = "\n".join(textwrap.wrap(f'"{text}"', width=30))

        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        text_bbox = temp_draw.multiline_textbbox((0, 0), wrapped_text, font=font_text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        name_bbox = temp_draw.textbbox((0, 0), display_name, font=font_italic)
        user_bbox = temp_draw.textbbox((0, 0), username, font=font_small)
        footer_height = (name_bbox[3] - name_bbox[1]) + (user_bbox[3] - user_bbox[1]) + 15

        content_width = avatar_size + padding + max(text_width, 350) + padding
        total_width = max(650, min(max_width, content_width))
        total_height = max(avatar_size + (padding * 2), text_height + footer_height + (padding * 2))

        main_image = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(main_image)

        if not transparent:
            bg_gradient = Image.new("RGBA", (total_width, total_height), darkened_color)
            main_image.paste(bg_gradient, (0, 0))

        avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        avatar_x = padding
        avatar_y = (total_height - avatar_size) // 2
        main_image.paste(avatar, (avatar_x, avatar_y), mask)

        text_x = avatar_x + avatar_size + padding
        text_y = (total_height - (text_height + footer_height)) // 2
        text_bg_width = total_width - text_x - padding

        draw.multiline_text(
            (text_x, text_y),
            wrapped_text,
            font=font_text,
            fill=(255, 255, 255, 255),
            align="left",
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

    @commands.slash_command(
        name="quote",
        description="Creates a stylish quote image with a profile picture",
        integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install},
        contexts={discord.InteractionContextType.guild, discord.InteractionContextType.bot_dm, discord.InteractionContextType.private_channel}
    )
    async def quote(self, ctx: discord.ApplicationContext, 
                   text: str, 
                   user: discord.User = None,
                   transparent: bool = False):
        await ctx.defer()
        target_user = user or ctx.author

        try:
            timeout = aiohttp.ClientTimeout(total=12)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                avatar_url = str(target_user.display_avatar.with_size(512).url)
                async with session.get(avatar_url) as response:
                    if response.status != 200:
                        return await ctx.followup.send(t("quote.avatar_error", ctx=ctx))
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
            await ctx.followup.send(t("quote.timeout_error", ctx=ctx))
        except Exception as e:
            await ctx.followup.send(t("quote.gen_error", ctx=ctx, error=str(e)))

def setup(bot):
    bot.add_cog(Quote(bot))
