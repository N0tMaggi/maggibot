import discord
from discord.ext import commands
import json
import datetime
from handlers.debug import LogDebug, LogError
import time
import random
import os
import asyncio
from utils.components import build_container, build_view

class Miscellaneous(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

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

            server_container = build_container(
                title=f"📊  𝚂𝙴𝚁𝚅𝙴𝚁 𝙸𝙽𝙵𝙾: {server.name}",
                description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{server.description or '*No description*'}",
                color=0x5865F2,
                thumbnail=thumbnail_url,
                image=server.banner.url if server.banner else None,
                footer_text=f"🔮 Requested by {ctx.author}",
                timestamp=True,
                fields=[
                    ("\n👑  𝙾𝚠𝚗𝚎𝚛", f"» {owner.mention if owner else 'Unknown'}\n{'-'*18}", False),
                    ("🆔  𝚂𝚎𝚛𝚟𝚎𝚛 𝙸𝙳", f"```{server.id}```", True),
                    (
                        "📆  𝙲𝚛𝚎𝚊𝚝𝚎𝚍 𝙾𝚗",
                        f"» {discord.utils.format_dt(server.created_at, 'D')}\n» ({discord.utils.format_dt(server.created_at, 'R')})",
                        True,
                    ),
                    (
                        "\n👥  𝙼𝚎𝚖𝚋𝚎𝚛𝚜",
                        f"▹ **Total:** {server.member_count}\n"
                        f"▹ **Online:** {server.approximate_presence_count if hasattr(server, 'approximate_presence_count') else 'N/A'}\n"
                        f"{'-'*30}",
                        False,
                    ),
                    ("🚀  𝙱𝚘𝚘𝚜𝚝𝚜", f"» Level {boost_level}\n» {boosts} Boosts", True),
                    ("🛡️  𝚅𝚎𝚛𝚒𝚏𝚒𝚌𝚊𝚝𝚒𝚘𝚗", f"» {verification_level}", True),
                    (
                        "\n📚  𝙲𝚑𝚊𝚗𝚗𝚎𝚕𝚜",
                        f"▹ 💬 Text: {text_channels}\n"
                        f"▹ 🔊 Voice: {voice_channels}\n"
                        f"▹ 📁 Categories: {categories}\n"
                        f"{'-'*30}",
                        False,
                    ),
                    ("🎭  𝚁𝚘𝚕𝚎𝚜", f"» {len(server.roles)}", True),
                    ("😄  𝙴𝚖𝚘𝚓𝚒𝚜", f"» {len(server.emojis)}", True),
                    ("\n✨  𝙵𝚎𝚊𝚝𝚞𝚛𝚎𝚜", f"```{features_str}```\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", False),
                ],
            )

            await ctx.respond(view=build_view(server_container))



        @commands.slash_command(name="userinfo", description="Get detailed information about a user")
        async def userinfo(self, ctx: discord.ApplicationContext, target: discord.Member = None):
            await ctx.defer()
            target = target or ctx.author

            created_at = discord.utils.format_dt(target.created_at, "F")
            joined_at = discord.utils.format_dt(target.joined_at, "F") if target.joined_at else "Unknown"
            premium_since = discord.utils.format_dt(target.premium_since, "R") if target.premium_since else "Not boosting"
            user_guilds_count = sum(1 for guild in self.bot.guilds if target in guild.members)

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


            roles = [role.mention for role in target.roles[1:]]  
            roles_str = " ".join(roles) if roles else "No special roles"
            
            fields = [
                (
                    "\n🔖  𝙱𝙰𝚂𝙸𝙲 𝙸𝙽𝙵𝙾𝚁𝙼𝙰𝚃𝙸𝙾𝙽",
                    f"""
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
                    False,
                ),
                (
                    "\n🏰  𝚂𝙴𝚁𝚅𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴",
                    f"""
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
                    False,
                ),
            ]

            if activity:
                fields.append(
                    (
                        "\n📡  𝙲𝚄𝚁𝚁𝙴𝙽𝚃 𝙰𝙲𝚃𝙸𝚅𝙸𝚃𝚈",
                        f"""
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            {activity}
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                    """,
                        False,
                    )
                )

            if badges:
                fields.append(
                    (
                        "\n🏆  𝙱𝙰𝙳𝙶𝙴𝚂",
                        f"""
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            {'  '.join(badges)}
            ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                    """,
                        False,
                    )
                )

            fields.extend([
                (
                    f"\n🤝  𝙼𝚄𝚃𝚄𝙰𝙻 𝚂𝙴𝚁𝚅𝙴𝚁𝚂 ({user_guilds_count})",
                    f"""
            ▬▬▬▬▬▬▬▬▬▬
            {mutual_guilds_str if mutual_guilds else 'None'}
            ▬▬▬▬▬▬▬▬▬▬
                """,
                    True,
                ),
                (
                    f"\n🎭  𝚁𝙾𝙻𝙴𝚂 ({len(roles)})",
                    f"""
            ▬▬▬▬▬▬▬▬▬▬
            {roles_str}
            ▬▬▬▬▬▬▬▬▬▬
                """,
                    True,
                ),
            ])

            user_container = build_container(
                title=f"📋  𝚄𝚂𝙴𝚁 𝙸𝙽𝙵𝙾𝚁𝙼𝙰𝚃𝙸𝙾𝙽 - {target.display_name}",
                color=target.color if target.color.value != 0 else 0x5865F2,
                timestamp=True,
                author=target,
                thumbnail=target.display_avatar.url,
                image=target.banner.url if target.banner else None,
                footer_text=f"🔮  𝚁𝙴𝚀𝚄𝙴𝚂𝚃𝙴𝙳 𝙱𝚈 {ctx.author}  •  𝚄𝚂𝙴𝚁 𝙸𝙳: {target.id}",
                fields=fields,
            )

            await ctx.respond(view=build_view(user_container))

        @commands.slash_command(name="test", description='TEST COMMAND')
        async def test(self, ctx):
            await ctx.respond('Test')

        @commands.slash_command(name="ping", description="Check the bot's latency")
        async def ping(self, ctx):
            loading_container = build_container(
                title="🏓 Pong!",
                description="Calculating latency... ⏳",
                color="info",
            )
            loading_message = await ctx.respond(view=build_view(loading_container))

            latency = self.bot.latency * 1000
            await asyncio.sleep(1)

            pong_container = build_container(
                title="🏓 Pong!",
                description=f"Latency: `{latency:.2f} ms`",
                color="success",
                footer_text=f"Requested by {ctx.author}",
            )
            await loading_message.edit(view=build_view(pong_container))



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
                timeout_container = build_container(
                    title="🚫 Timed out!",
                    description="You took too long to respond.",
                    color="error",
                )
                await ctx.author.send(view=build_view(timeout_container))

            except Exception as e:
                LogError(f" An error occurred: {e}")
                raise Exception ("An error occurred while cleaning DMs." + str(e))
                

def setup(bot):
    bot.add_cog(Miscellaneous(bot))
