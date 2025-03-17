import io
import discord
from discord.ext import commands
import textwrap
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from colorthief import ColorThief

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Creates a stylish quote image with a profile picture")
    async def quote(self, ctx: discord.ApplicationContext, 
                   text: str, 
                   user: discord.Member = None,
                   transparent: bool = False):
        await ctx.defer()
        target_user = user or ctx.author

        try:
            async with aiohttp.ClientSession() as session:
                avatar_url = str(target_user.display_avatar.with_size(512).url)
                async with session.get(avatar_url) as response:
                    if response.status != 200:
                        return await ctx.followup.send("❌ Couldn't download avatar!")
                    avatar_data = await response.read()

                avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")
                color_thief = ColorThief(io.BytesIO(avatar_data))
                dominant_color = color_thief.get_color(quality=1)
                darkened_color = tuple([max(0, c - 40) for c in dominant_color])

                avatar_size = 160
                padding = 40
                max_width = 850
                border_width = 5

                try:
                    font_regular = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 32)
                    font_italic = ImageFont.truetype("fonts/NotoSans-Italic.ttf", 28)
                    font_small = ImageFont.truetype("fonts/NotoSans-Regular.ttf", 24)
                except:
                    font_regular = ImageFont.load_default(32)
                    font_italic = ImageFont.load_default(28)
                    font_small = ImageFont.load_default(24)

                draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
                wrapped_text = textwrap.fill(text, width=34)
                text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font_regular)
                text_height = text_bbox[3] - text_bbox[1]

                display_name = f"~ {target_user.display_name}"
                username = f"@{target_user.name}"
                name_bbox = draw.textbbox((0, 0), display_name, font=font_italic)
                user_bbox = draw.textbbox((0, 0), username, font=font_small)
                name_height = name_bbox[3] - name_bbox[1] + user_bbox[3] - user_bbox[1] + 10

                total_height = max(250, text_height + name_height + padding * 2 + 50)
                text_width = min(max_width - avatar_size - padding * 2, 650)
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

                text_x = avatar_size + padding * 2
                text_bg_width = total_width - text_x - padding
                gradient = Image.new('RGBA', (text_bg_width, total_height), color=0)
                for x in range(text_bg_width):
                    opacity = int(255 * (0.5 + 0.5 * (x / text_bg_width)))
                    gradient.putpixel((x, 0), (*darkened_color, opacity))
                main_image.paste(gradient, (text_x, 0), gradient)

                text_y = (total_height - text_height - name_height - 30) // 2
                draw.multiline_text(
                    (text_x + 25, text_y),
                    wrapped_text,
                    font=font_regular,
                    fill=(255, 255, 255, 255),
                    spacing=10,
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

                with io.BytesIO() as output:
                    combined_image.save(output, format="PNG", bitmap_format="png")
                    output.seek(0)
                    await ctx.followup.send(file=discord.File(output, "quote.png"))

        except Exception as e:
            await ctx.followup.send(f"❌ Error generating image: {str(e)}")

def setup(bot):
    bot.add_cog(Quote(bot))