import discord
from discord.ext import commands
import json
import datetime
import handlers.debug as DebugHandler
import time
import random
import os
import asyncio

class Miscellaneous(commands.Cog):
        def __init__(self, bot):
            self.bot = bot


        @commands.slash_command(name= "ismypconfire", description="Is my PC on fire? 🔥")
        async def ismypconfire(self, ctx):
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



        @commands.slash_command(name="serverinfo", description="Get detailed information about the server")
        async def serverinfo(self, ctx: discord.ApplicationContext):
            await ctx.defer() 
            server = ctx.guild

            thumbnail_url = server.icon.url if server.icon else None
            owner = server.owner
            owner_avatar = owner.display_avatar.url if owner else None

            verification_level = str(server.verification_level).title()

            boost_level = server.premium_tier
            boosts = server.premium_subscription_count

            features = server.features
            features_list = [f.replace('_', ' ').title() for f in features]
            if features_list:
                features_str = ", ".join(features_list)
                if len(features_str) > 1024:
                    features_str = features_str[:1021] + "..."
            else:
                features_str = "None"

            text_channels = len(server.text_channels)
            voice_channels = len(server.voice_channels)
            categories = len(server.categories)
            channels_str = f"💬 Text: {text_channels}\n🔊 Voice: {voice_channels}\n📁 Categories: {categories}"

            embed = discord.Embed(
                title=f"📊  𝚂𝙴𝚁𝚅𝙴𝚁 𝙸𝙽𝙵𝙾: {server.name}",
                description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{server.description or '*No description*'}",
                color=0x5865F2
            )

            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            if server.banner:
                embed.set_image(url=server.banner.url)

            embed.add_field(name="\n👑  𝙾𝚠𝚗𝚎𝚛", 
                            value=f"» {owner.mention if owner else 'Unknown'}\n{'-'*18}", 
                            inline=False)

            embed.add_field(name="🆔  𝚂𝚎𝚛𝚟𝚎𝚛 𝙸𝙳", 
                            value=f"```{server.id}```",
                            inline=True)

            embed.add_field(name="📆  𝙲𝚛𝚎𝚊𝚝𝚎𝚍 𝙾𝚗", 
                            value=f"» {discord.utils.format_dt(server.created_at, 'D')}\n» ({discord.utils.format_dt(server.created_at, 'R')})",
                            inline=True)

            embed.add_field(name="\n👥  𝙼𝚎𝚖𝚋𝚎𝚛𝚜", 
                            value=f"▹ **Total:** {server.member_count}\n"
                                  f"▹ **Online:** {server.approximate_presence_count if hasattr(server, 'approximate_presence_count') else 'N/A'}\n"
                                  f"{'-'*30}",
                            inline=False)

            embed.add_field(name="🚀  𝙱𝚘𝚘𝚜𝚝𝚜", 
                            value=f"» Level {boost_level}\n"
                                  f"» {boosts} Boosts", 
                            inline=True)

            embed.add_field(name="🛡️  𝚅𝚎𝚛𝚒𝚏𝚒𝚌𝚊𝚝𝚒𝚘𝚗", 
                            value=f"» {verification_level}", 
                            inline=True)

            embed.add_field(name="\n📚  𝙲𝚑𝚊𝚗𝚗𝚎𝚕𝚜", 
                            value=f"▹ 💬 Text: {text_channels}\n"
                                  f"▹ 🔊 Voice: {voice_channels}\n"
                                  f"▹ 📁 Categories: {categories}\n"
                                  f"{'-'*30}",
                            inline=False)

            embed.add_field(name="🎭  𝚁𝚘𝚕𝚎𝚜", 
                            value=f"» {len(server.roles)}", 
                            inline=True)

            embed.add_field(name="😄  𝙴𝚖𝚘𝚓𝚒𝚜", 
                            value=f"» {len(server.emojis)}", 
                            inline=True)

            embed.add_field(name="\n✨  𝙵𝚎𝚊𝚝𝚞𝚛𝚎𝚜", 
                            value=f"```{features_str}```\n"
                                  f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", 
                            inline=False)

            embed.set_footer(
                text=f"🔮 Requested by {ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.timestamp = server.created_at

            await ctx.respond(embed=embed)



        @commands.slash_command(name="userinfo", description="Get detailed information about a user")
        async def userinfo(self, ctx: discord.ApplicationContext, target: discord.Member = None):
            await ctx.defer()
            target = target or ctx.author

            # Pre-calculate values with error handling
            created_at = discord.utils.format_dt(target.created_at, "F")
            joined_at = discord.utils.format_dt(target.joined_at, "F") if target.joined_at else "Unknown"
            premium_since = discord.utils.format_dt(target.premium_since, "R") if target.premium_since else "Not boosting"
            user_guilds_count = sum(1 for guild in self.bot.guilds if target in guild.members)

            # Activity parsing
            activity = ""
            if target.activities:
                for act in target.activities:
                    if isinstance(act, discord.CustomActivity):
                        activity = f"🎨 Custom Status: {act.name}"
                    elif act.type == discord.ActivityType.playing:
                        activity = f"🎮 Playing {act.name}"
                    elif act.type == discord.ActivityType.streaming:
                        activity = f"📺 Streaming [{act.name}]({act.url})"
                    elif act.type == discord.ActivityType.listening:
                        activity = f"🎧 Listening to {act.title}" if hasattr(act, "title") else f"🎧 {act.name}"
                    elif act.type == discord.ActivityType.watching:
                        activity = f"📽️ Watching {act.name}"

            # Badge parsing
            flags = target.public_flags
            badges = []
            if flags.staff: badges.append("👑 Staff")
            if flags.partner: badges.append("🤝 Partner")
            if flags.hypesquad: badges.append("⚔️ HypeSquad")
            if flags.bug_hunter: badges.append("🐛 Bug Hunter")
            if flags.bug_hunter_level_2: badges.append("🐛 Bug Hunter Lv2")
            if flags.early_supporter: badges.append("🌟 Early Supporter")
            if flags.active_developer: badges.append("💻 Active Developer")
            if flags.verified_bot_developer: badges.append("🤖 Bot Developer")


            mutual_guilds = [guild.name for guild in self.bot.guilds if target in guild.members][:5]
            mutual_guilds_str = "\n".join(mutual_guilds) + (f"\n+ {len(mutual_guilds)-5} more..." if len(mutual_guilds) > 5 else "")


            roles = [role.mention for role in target.roles[1:]]  # Exclude @everyone
            roles_str = " ".join(roles) if roles else "No special roles"
            
            embed = discord.Embed(
                title=f"📋  𝚄𝚂𝙴𝚁 𝙸𝙽𝙵𝙾𝚁𝙼𝙰𝚃𝙸𝙾𝙽 - {target.display_name}",
                color=target.color if target.color.value != 0 else 0x5865F2,
                timestamp=discord.utils.utcnow()
            )

            # Header Section
            embed.set_author(name=f"{target}", icon_url=target.display_avatar.url)
            embed.set_thumbnail(url=target.display_avatar.url)

            if target.banner:
                embed.set_image(url=target.banner.url)

            # Basic Information
            embed.add_field(
                name="\n🔖  𝙱𝙰𝚂𝙸𝙲 𝙸𝙽𝙵𝙾𝚁𝙼𝙰𝚃𝙸𝙾𝙽",
                value=f"""
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            » **Name:** {target.name}
            » **ID:** `{target.id}`
            » **Discriminator:** #{target.discriminator}
            » **Bot:** {'✅' if target.bot else '❌'}

            » **Account Created:**  
            {created_at}
            » **Server Join Date:**  
            {joined_at}
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                """,
                inline=False
            )

            # Server Profile
            embed.add_field(
                name="\n🏰  𝚂𝙴𝚁𝚅𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴",
                value=f"""
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            » **Top Role:** {target.top_role.mention if target.top_role else 'None'}
            » **Boosting Since:**  
            {premium_since}
            » **Current Status:**  
            {str(target.status).title()}
            » **Active Client:**  
            {'📱 Mobile' if target.is_on_mobile() else '💻 Desktop'}
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                """,
                inline=False
            )

            if activity:
                embed.add_field(
                    name="\n📡  𝙲𝚄𝚁𝚁𝙴𝙽𝚃 𝙰𝙲𝚃𝙸𝚅𝙸𝚃𝚈",
                    value=f"""
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            {activity}
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                    """,
                    inline=False
                )

            if badges:
                embed.add_field(
                    name="\n🏆  𝙱𝙰𝙳𝙶𝙴𝚂",
                    value=f"""
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            {'  '.join(badges)}
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                    """,
                    inline=False
                )

            embed.add_field(
                name=f"\n🤝  𝙼𝚄𝚃𝚄𝙰𝙻 𝚂𝙴𝚁𝚅𝙴𝚁𝚂 ({user_guilds_count})",
                value=f"""
            ▬▬▬▬▬▬▬▬▬▬
            {mutual_guilds_str if mutual_guilds else 'None'}
            ▬▬▬▬▬▬▬▬▬▬
                """,
                inline=True
            )

            embed.add_field(
                name=f"\n🎭  𝚁𝙾𝙻𝙴𝚂 ({len(roles)})",
                value=f"""
            ▬▬▬▬▬▬▬▬▬▬
            {roles_str}
            ▬▬▬▬▬▬▬▬▬▬
                """,
                inline=True
            )

            embed.set_footer(
                text=f"🔮  𝚁𝙴𝚀𝚄𝙴𝚂𝚃𝙴𝙳 𝙱𝚈 {ctx.author}  •  𝚄𝚂𝙴𝚁 𝙸𝙳: {target.id}",
                icon_url=ctx.author.display_avatar.url
            )

            await ctx.respond(embed=embed)

        @commands.slash_command(name="test", description='TEST COMMAND')
        async def test(self, ctx):
            await ctx.respond('Test')

        @commands.slash_command(name="ping", description="Check the bot's latency")
        async def ping(self, ctx):
            loading_embed = discord.Embed(
                title="🏓 Pong!",
                description="Calculating latency... ⏳",
                color=discord.Color.blue()
            )
            loading_message = await ctx.respond(embed=loading_embed)

            latency = self.bot.latency * 1000
            await asyncio.sleep(1)

            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Latency: `{latency:.2f} ms`",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await loading_message.edit(embed=embed)




        @commands.slash_command(name="dm-clean", description="Let the bot clean your DMs.")
        @commands.cooldown(1, 180, commands.BucketType.user)
        async def dm_clean(self, ctx):
            await ctx.respond("Cleaning DMs...")
            await ctx.author.send("Please confirm that you want to clean your DMs by typing `yes` in this chat.")

            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda message: message.author == ctx.author and message.content.lower() == "yes",
                    timeout=60
                )

                async for message in ctx.author.dm_channel.history(limit=100):
                    if message.author == self.bot.user:
                        await message.delete()

                message = await ctx.author.send("Your DMs have been cleaned.")
                await asyncio.sleep(5)
                await message.delete()

            except asyncio.TimeoutError:
                embed = discord.Embed(title="🚫 Timed out!", description="You took too long to respond.", color=discord.Color.red())
                await ctx.author.send(embed=embed)

            except Exception as e:
                DebugHandler.LogError(f" An error occurred: {e}")
                raise Exception ("An error occurred while cleaning DMs." + str(e))
                

def setup(bot):
    bot.add_cog(Miscellaneous(bot))