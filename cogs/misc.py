import discord
from discord.ext import commands
from discord.commands import slash_command
from datetime import datetime
import os
import random
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap

class Miscellaneous(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        
        @bot.slash_command(description='TEST COMMAND')
        async def test(ctx):
            await ctx.respond('Test')

        @bot.slash_command(description='Check the bot\'s latency')
        async def ping(ctx):
            latency = bot.latency * 1000  # Convert latency to milliseconds
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Latency: `{latency:.2f}ms`",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
        
        @bot.slash_command(description='Get Info from a user')
        async def userinfo(ctx, target: discord.Member = None):
            target = target or ctx.author
            embed = discord.Embed(title="User Information",
                                  colour=target.colour,
                                  timestamp=datetime.utcnow())
            embed.set_thumbnail(url=target.avatar.url)
            fields = [("Name", str(target), True),
                      ("ID", target.id, True),
                      ("Bot?", target.bot, True),
                      ("Top role", target.top_role.mention, True),
                      ("Status", str(target.status).title(), True),
                      ("Activity", f"{str(target.activity.type).split('.')[-1].title() if target.activity else 'N/A'} {target.activity.name if target.activity else ''}", True),
                      ("Created at", target.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                      ("Joined at", target.joined_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                      ("Boosted", bool(target.premium_since), True)]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await ctx.respond(embed=embed)
        
        @commands.has_permissions(administrator=True)
        @bot.slash_command(description='Stops the bot')
        async def stop(ctx):
            if ctx.author.id == 1227911822875693120:  # Check if the author ID matches yours
                embed = discord.Embed(
                    title="🛑 Bot Shutdown",
                    description="Bot is shutting down...",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
                await ctx.respond(embed=embed)
                await self.bot.close()  # Close the bot
            else:
                embed = discord.Embed(
                    title="🚫 Permission Denied",
                    description="You do not have permission to stop the bot.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
                await ctx.respond(embed=embed)   


        @bot.slash_command(description="Is my PC on fire? 🔥")
        async def ismypconfire(ctx):
            responses = [
                "🔥 Your PC is now classified as a nuclear reactor. RUN! 🏃💨",
                "💻 Your PC is fine... for now. But I hear the fans screaming. 👀",
                "🚒 Firefighters are on the way! Hope you have backups! 😨",
                "🥵 Your PC is sweating harder than a gaming laptop in summer!",
                "❄️ Nope, your PC is chilling. Maybe too much? Try overclocking! 😆",
                "🧯 Everything is fine! But keep an extinguisher nearby... just in case. 👀",
                "💀 Your PC died from overheating. It’s now in a better place. R.I.P. 😭",
                "🔥🔥🔥 SYSTEM OVERHEATING! RELEASING MAGIC SMOKE! 🔥🔥🔥"
            ]

            await ctx.respond(random.choice(responses))





        @bot.slash_command(description="Erstellt ein Zitatbild mit deinem Profilbild")
        async def quote(ctx, text: str):
           # Profilbild abrufen
           avatar_url = ctx.author.display_avatar.url
           response = requests.get(avatar_url)
           avatar = Image.open(BytesIO(response.content)).convert("RGBA")
           # Bildgrößen und Abstände
           avatar_size = 128
           padding = 5  # Kleinerer Abstand zwischen Profilbild und Text
           text_area_width = 400
           total_width = avatar_size + text_area_width + padding
           total_height = 150  # Höhere Bildhöhe für lange Texte
           # Farbverlauf-Hintergrund erstellen
           gradient = Image.new('RGBA', (text_area_width, total_height), color=0)
           draw = ImageDraw.Draw(gradient)
           for x in range(text_area_width):
               opacity = int(255 * (x / text_area_width))
               draw.line([(x, 0), (x, total_height)], fill=(0, 0, 0, opacity))
           # Schriftart laden
           font_path = "times.ttf"
           try:
               font = ImageFont.truetype(font_path, 24)
           except IOError:
               font = ImageFont.load_default()
           # **Textumbruch hinzufügen**
           max_chars_per_line = 30  # Maximale Zeichen pro Zeile (kann angepasst werden)
           wrapped_text = textwrap.fill(text, max_chars_per_line)  # Automatischer Umbruch
           # **Textposition anpassen**
           text_x = avatar_size + padding + 15  # Weiter links starten
           text_y = 20  # Text etwas höher setzen
           username_y = text_y + 60  # Abstand zwischen Text und Username
           draw.text((text_x, text_y), wrapped_text, font=font, fill=(255, 255, 255, 255))
           draw.text((text_x, username_y), f"~ {ctx.author.display_name}", font=font, fill=(255, 255, 255, 255))
           # Bilder kombinieren
           combined = Image.new('RGBA', (total_width, total_height))
           combined.paste(avatar.resize((avatar_size, avatar_size)), (0, 10))  # Avatar leicht nach unten setzen
           combined.paste(gradient, (avatar_size + padding, 0), mask=gradient)
           # Bild speichern und senden
           with BytesIO() as image_binary:
               combined.save(image_binary, 'PNG')
               image_binary.seek(0)
               await ctx.respond(file=discord.File(fp=image_binary, filename='quote.png'))



def setup(bot: discord.Bot):
    bot.add_cog(Miscellaneous(bot))




