import discord
from discord.ext import commands
import asyncio
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import io
import textwrap

class TrollCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="jumpscare", 
        description="Perform a jumpscare on a user by joining their voice channel and playing a sound."
    )
    async def jumpscare(self, ctx: discord.ApplicationContext, user: discord.Member, name: str):
        if not user.voice or not user.voice.channel:
            embed = discord.Embed(
                title="Voice Channel Not Found",
                description=f"❌ {user.mention} is not in any voice channel.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        voice_channel = user.voice.channel

        try:
            vc = await voice_channel.connect()
        except Exception as e:
            embed = discord.Embed(
                title="Connection Error",
                description=f"❌ Failed to join {voice_channel.mention}: {e}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="Jumpscare Initiated",
            description=f"😱 Preparing jumpscare for {user.mention} in {voice_channel.mention}...",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed)

        await asyncio.sleep(1)

        file_path = os.path.join("assets", f"{name}.mp3")
        if not os.path.exists(file_path):
            embed = discord.Embed(
                title="File Not Found",
                description=f"❌ The file `{name}.mp3` was not found in the assets folder.",
                color=discord.Color.red()
            )
            await vc.disconnect()
            await ctx.followup.send(embed=embed, ephemeral=True)
            return

        try:
            source = discord.FFmpegPCMAudio(file_path)
            vc.play(source)
        except Exception as e:
            await vc.disconnect()
            raise Exception(f"Failed to play audio: {e}")


        await asyncio.sleep(1)
        await vc.disconnect()

        embed = discord.Embed(
            title="Jumpscare Complete",
            description=f"😈 Jumpscare for {user.mention} has been executed.",
            color=discord.Color.green()
        )
        await ctx.followup.send(embed=embed)

    @commands.slash_command(description="Creates a quote image with your profile picture")
    async def quote(self, ctx: discord.ApplicationContext, text: str):
        await ctx.defer()  

        # Fetch profile picture
        avatar_url = ctx.author.display_avatar.url
        response = requests.get(avatar_url)
        avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")

        # Image dimensions and padding
        avatar_size = 128
        padding = 20  
        text_area_width = 400
        total_width = avatar_size + text_area_width + padding
        total_height = 150

        # Gradient background creation
        gradient = Image.new('RGBA', (text_area_width, total_height), color=0)
        draw = ImageDraw.Draw(gradient)
        for x in range(text_area_width):
            opacity = int(255 * (x / text_area_width))
            draw.line([(x, 0), (x, total_height)], fill=(0, 0, 0, opacity))

        # Load fonts
        try:
            font_path_regular = "arial.ttf"  
            font_path_bold = "arialbd.ttf"   
            font_regular = ImageFont.truetype(font_path_regular, 24)
            font_bold = ImageFont.truetype(font_path_bold, 24)
        except IOError:
            font_regular = ImageFont.load_default()
            font_bold = ImageFont.load_default()

        # Text wrapping
        max_chars_per_line = 40  
        wrapped_text = textwrap.fill(text, max_chars_per_line)  

        # Text positioning
        text_x = avatar_size + padding + 10  
        text_y = 20  
        username_y = text_y + 40  

        # Draw text
        draw.text((text_x, text_y), wrapped_text, font=font_regular, fill=(255, 255, 255, 255))
        draw.text((text_x, username_y), f"~ {ctx.author.display_name}", font=font_bold, fill=(255, 255, 255, 255))

        # Combine images
        combined = Image.new('RGBA', (total_width, total_height))
        combined.paste(avatar.resize((avatar_size, avatar_size)), (10, 10))  
        combined.paste(gradient, (avatar_size + padding, 0), mask=gradient)

        # Add subtle rounded corners
        border_radius = 20
        mask = Image.new('L', combined.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, combined.width, combined.height), radius=border_radius, fill=255)
        combined.putalpha(mask)

        # Add subtle shadow
        shadow = combined.filter(ImageFilter.GaussianBlur(radius=5))
        shadow_offset = (5, 5)
        final_image = Image.new('RGBA', (combined.width + shadow_offset[0], combined.height + shadow_offset[1]), (0, 0, 0, 0))
        final_image.paste(shadow, shadow_offset)
        final_image.paste(combined, (0, 0), combined)

        # Save and send image
        with io.BytesIO() as image_binary:
            final_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.followup.send(file=discord.File(fp=image_binary, filename='quote.png'))




def setup(bot: commands.Bot):
    bot.add_cog(TrollCommands(bot))
