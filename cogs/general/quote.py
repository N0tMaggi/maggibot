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

        @commands.slash_command(description="Creates a stylish quote image with your profile picture")
        async def quote(self, ctx: discord.ApplicationContext, *, text: str):
            await ctx.defer()

            try:
                async with aiohttp.ClientSession() as session:
                    avatar_url = str(ctx.author.display_avatar.with_size(512).url)
                    async with session.get(avatar_url) as response:
                        if response.status != 200:
                            return await ctx.followup.send("❌ Couldn't download your avatar!")
                        avatar_data = await response.read()

                    avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")

                    color_thief = ColorThief(io.BytesIO(avatar_data))
                    dominant_color = color_thief.get_color(quality=1)

                    avatar_size = 150
                    padding = 30
                    max_width = 800
                    min_height = 200
                    border_radius = 25

                    try:
                        font_regular = ImageFont.truetype("fonts/Roboto-Regular.ttf", 28)
                        font_bold = ImageFont.truetype("fonts/Roboto-Bold.ttf", 28)
                        font_italic = ImageFont.truetype("fonts/Roboto-Italic.ttf", 24)
                    except:
                        font_regular = ImageFont.load_default(28)
                        font_bold = ImageFont.load_default(28)
                        font_italic = ImageFont.load_default(24)

                    text_width = min(max_width - avatar_size - padding * 2, 600)
                    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))

                    wrapped_text = textwrap.fill(text, width=32)
                    text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font_regular)
                    text_height = text_bbox[3] - text_bbox[1]

                    username_text = f"~ {ctx.author.display_name}"
                    username_bbox = draw.textbbox((0, 0), username_text, font=font_italic)
                    username_height = username_bbox[3] - username_bbox[1]

                    total_height = max(min_height, text_height + username_height + padding * 2 + 40)
                    total_width = avatar_size + text_width + padding * 2

                    main_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(main_image)

                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    avatar = avatar.resize((avatar_size, avatar_size))
                    avatar.putalpha(mask)

                    avatar_with_border = ImageOps.expand(avatar, border=3, fill=dominant_color)
                    main_image.paste(avatar_with_border, (padding, (total_height - avatar_size) // 2), avatar_with_border)

                    text_x = avatar_size + padding * 2
                    text_bg_width = total_width - text_x - padding

                    gradient = Image.new('RGBA', (text_bg_width, total_height), color=0)
                    for x in range(text_bg_width):
                        opacity = int(255 * (0.3 + 0.7 * (x / text_bg_width)))
                        gradient.putpixel((x, 0), (*dominant_color, opacity))

                    main_image.paste(gradient, (text_x, 0), gradient)

                    text_y = (total_height - text_height - username_height - 20) // 2
                    draw.multiline_text(
                        (text_x + 20, text_y),
                        wrapped_text,
                        font=font_regular,
                        fill=(255, 255, 255, 230),
                        spacing=8
                    )

                    username_x = text_x + text_bg_width - 20 - username_bbox[2]
                    draw.text(
                        (username_x, text_y + text_height + 20),
                        username_text,
                        font=font_italic,
                        fill=(*dominant_color, 200)
                    )

                    shadow = main_image.filter(ImageFilter.GaussianBlur(radius=7))
                    shadow = ImageOps.expand(shadow, border=10, fill=(0, 0, 0, 0))
                    shadow_offset = (5, 10)

                    final_image = Image.new('RGBA', 
                        (main_image.width + 20, main_image.height + 20),
                        (0, 0, 0, 0))
                    final_image.paste(shadow, shadow_offset, shadow)
                    final_image.paste(main_image, (10, 5), main_image)

                    with io.BytesIO() as output:
                        final_image.save(output, format="PNG")
                        output.seek(0)
                        await ctx.followup.send(file=discord.File(output, "quote.png"))

            except Exception as e:
                await ctx.followup.send(f"❌ Error generating image: {str(e)}")

def setup(bot):
    bot.add_cog(Quote(bot))