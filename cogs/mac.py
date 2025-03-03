import discord
from discord.ext import commands
import json
import datetime
import os
import asyncio
import traceback

AUTHORIZED_ID = int(os.getenv("OWNER_ID"))
JSON_FILE = "data/mac.json"
NOTIFY_CHANNEL_ID = 1341152168077557870  

def load_bans():
    if not os.path.exists(JSON_FILE):
        return []
    with open(JSON_FILE, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

def save_bans(bans):
    with open(JSON_FILE, "w") as f:
        json.dump(bans, f, indent=4)

def trim_field(value: str, max_length: int = 1024) -> str:
    return value if len(value) <= max_length else value[:max_length-3] + "..."

class MacBan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_authorized(self, ctx: discord.ApplicationContext) -> bool:
        return ctx.author.id == AUTHORIZED_ID

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        bans = load_bans()
        if any(ban["id"] == member.id for ban in bans):
            ban_record = next(ban for ban in bans if ban["id"] == member.id)
            attempted_server = member.guild.name

            # Try to send the user a DM
            try:
                dm_embed = discord.Embed(
                    title="🚫 Global Ban Notification",
                    description="You are globally banned by MAC™ and cannot join this server.",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="🛡️ Server", value=attempted_server, inline=True)
                dm_embed.add_field(name="📅 Ban Date", value=ban_record.get("bandate", "Unknown"), inline=True)
                dm_embed.add_field(name="📝 Reason", value=trim_field(ban_record.get("reason", "No reason provided")), inline=True)
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass

            # Kick the user
            try:
                await member.kick(reason="Globally banned user attempted to join.")
            except Exception as e:
                pass

            # Send a notification in the defined channel
            channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
            if channel:
                notify_embed = discord.Embed(
                    title="🚫 Global Ban Detected",
                    description=(
                        f"⚠️ {member.mention} attempted to join **{attempted_server}** but is globally banned and has been kicked."
                    ),
                    color=discord.Color.red()
                )
                notify_embed.add_field(name="📅 Ban Date", value=ban_record.get("bandate", "Unknown"), inline=True)
                notify_embed.add_field(name="📝 Reason", value=trim_field(ban_record.get("reason", "No reason provided")), inline=True)
                notify_embed.set_footer(text="🔒 User is on the global ban list.")
                await channel.send(embed=notify_embed)
    
    @commands.slash_command(name="macban", description="Globally ban a user and add them to the global ban list.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def macban(self, ctx: discord.ApplicationContext, user: discord.User, reason: str = "No reason provided"):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        bans = load_bans()
        if any(ban["id"] == user.id for ban in bans):
            embed = discord.Embed(
                title="User Already Banned",
                description=f"🔨 {user.mention} is already globally banned.",
                color=discord.Color.orange()
            )
            await ctx.respond(embed=embed)
            return

        ban_record = {
            "id": user.id,
            "name": user.name,
            "bandate": datetime.datetime.utcnow().isoformat(),
            "reason": reason,
            "serverid": ctx.guild.id if ctx.guild else None,
            "servername": ctx.guild.name if ctx.guild else None,
            "bannedby": ctx.author.name
        }
        bans.append(ban_record)
        save_bans(bans)
        embed = discord.Embed(
            title="Global Ban Added",
            description=f"🔨 {user.mention} has been globally banned.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Banned By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Ban Date", value=ban_record["bandate"], inline=True)
        await ctx.respond(embed=embed)

        try:
            user_embed = discord.Embed(
                title="Global Ban Notification",
                description="You have been globally banned by MAC™ and cannot join any server where MAC™ is present.",
                color=discord.Color.red()
            )
            user_embed.add_field(name="📅 Ban Date", value=ban_record["bandate"], inline=True)
            user_embed.add_field(name="📝 Reason", value=trim_field(reason), inline=True)   
            await user.send(embed=user_embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="User DM Error",
                description="The user has their DMs closed.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)


    @commands.slash_command(name="macunban", description="Remove a global ban for a user.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def macunban(self, ctx: discord.ApplicationContext, user: discord.User):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        bans = load_bans()
        new_bans = [ban for ban in bans if ban["id"] != user.id]
        if len(new_bans) == len(bans):
            embed = discord.Embed(
                title="User Not Banned",
                description=f"ℹ️ {user.mention} is not globally banned.",
                color=discord.Color.orange()
            )
            await ctx.respond(embed=embed)
            return

        save_bans(new_bans)
        embed = discord.Embed(
            title="Global Ban Removed",
            description=f"✅ {user.mention} has been removed from the global ban list.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

        try:
            user_embed = discord.Embed(
                title="Global Ban Removed",
                description="You have been removed from the global ban list by MAC™.",
                color=discord.Color.green()
            )
            await user.send(embed=user_embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="User DM Error",
                description="The user has their DMs closed.",
                color=discord.Color.red()
                )
            await ctx.send(embed=embed)
            

    @commands.slash_command(name="macinfo", description="Display overall info about the global ban list.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def macinfo(self, ctx: discord.ApplicationContext):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return
    
        bans = load_bans()
        embed = discord.Embed(title="🌍 Global Ban List Info", color=discord.Color.blue())
        embed.add_field(name="📊 Total Global Bans", value=str(len(bans)), inline=False)
    
        if bans:
            ban_list = ""
            for ban in bans[:5]:
                ban_list += f"• **{ban['name']}** (ID: `{ban['id']}`) - Banned on **{ban['bandate']}**\n"
            embed.add_field(name="📰 Recent Bans", value=trim_field(ban_list), inline=False)
        else:
            embed.add_field(name="🚫 No Bans", value="The global ban list is empty.", inline=False)
    
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="maclookup", description="Lookup detailed ban info for a user.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def maclookup(self, ctx: discord.ApplicationContext, user: discord.User):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        bans = load_bans()
        for ban in bans:
            if ban["id"] == user.id:
                embed = discord.Embed(title="Global Ban Record Found", color=discord.Color.red())
                embed.add_field(name="User", value=f"{ban['name']} (ID: {ban['id']})", inline=False)
                embed.add_field(name="Ban Date", value=ban["bandate"], inline=True)
                embed.add_field(name="Reason", value=trim_field(ban["reason"]), inline=True)
                embed.add_field(name="Server", value=f"{ban['servername']} (ID: {ban['serverid']})", inline=False)
                embed.add_field(name="Banned By", value=ban["bannedby"], inline=True)
                await ctx.respond(embed=embed)
                return

        embed = discord.Embed(
            title="No Ban Record",
            description=f"ℹ️ {user.mention} is not globally banned.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(name="maccheck", description="Check if a user is globally banned.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def maccheck(self, ctx: discord.ApplicationContext, user: discord.User):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        bans = load_bans()
        for ban in bans:
            if ban["id"] == user.id:
                embed = discord.Embed(
                    title="User is Globally Banned",
                    description=f"🔨 {user.mention} is globally banned.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Reason", value=trim_field(ban["reason"]), inline=False)
                await ctx.respond(embed=embed)
                return

        embed = discord.Embed(
            title="User is Not Globally Banned",
            description=f"✅ {user.mention} is not globally banned.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(name="macbanall", description="Ban all users from the global ban list in this server.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def macbanall(self, ctx: discord.ApplicationContext):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        await ctx.defer()
        working_embed = discord.Embed(
            title="⏳ Processing Global Ban All",
            description="Please wait while I ban all users from the global ban list...",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=working_embed)

        bans = load_bans()
        if not bans:
            embed = discord.Embed(
                title="No Global Bans",
                description="ℹ️ The global ban list is empty.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed)
            return

        banned_members = []
        failed_members = []
        for ban in bans:
            user_id = ban["id"]
            member = ctx.guild.get_member(user_id)
            if member:
                try:
                    await ctx.guild.ban(member, reason=f"Global ban executed by MAC: {ban['reason']}")
                    banned_members.append(f"{member.name} ({member.id})")
                except Exception as e:
                    failed_members.append(f"{ban['name']} ({ban['id']})")
                await asyncio.sleep(2)
        embed = discord.Embed(title="Global Ban All Executed", color=discord.Color.red())
        embed.add_field(name="Successfully Banned", value="\n".join(banned_members) if banned_members else "None", inline=False)
        embed.add_field(name="Failed to Ban", value="\n".join(failed_members) if failed_members else "None", inline=False)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="macgetserverbannedusersandban", description="Import all banned users from this server into the global ban list.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def macgetserverbannedusersandban(self, ctx: discord.ApplicationContext):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        # Defer the response so the user sees that the bot is working
        await ctx.defer(ephemeral=True)
        working_embed = discord.Embed(
            title="⏳ Importing Server Bans",
            description="Fetching server ban list. Please wait...",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=working_embed)

        try:
            bans_list = [ban async for ban in ctx.guild.bans()]
        except Exception as e:
            await ctx.respond(f"❌ Failed to fetch bans: {e}")
            return

        if not bans_list:
            embed = discord.Embed(
                title="No Server Bans Found",
                description="ℹ️ There are no banned users in this server.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed)
            return

        global_bans = load_bans()
        imported_users = []
        skipped_users = []
        file_lines = []  # Für die TXT-Datei
        for ban_entry in bans_list:
            user = ban_entry.user
            if any(ban["id"] == user.id for ban in global_bans):
                skipped_users.append(f"{user.name} ({user.id})")
                continue
            ban_record = {
                "id": user.id,
                "name": user.name,
                "bandate": datetime.datetime.utcnow().isoformat(),
                "reason": f"Mac IMPORTEDLIST from Server: {ctx.guild.name}",
                "serverid": ctx.guild.id,
                "servername": ctx.guild.name,
                "bannedby": "Imported"
            }
            global_bans.append(ban_record)
            imported_users.append(f"{user.name} ({user.id})")
            # Zeile für die TXT-Datei
            file_lines.append(f"{user.name} ({user.id}) - Reason: Mac IMPORTEDLIST from Server: {ctx.guild.name}\n")
            await asyncio.sleep(1)  # Kurze Pause, um Rate Limits zu vermeiden

        save_bans(global_bans)
        # Erstelle den Inhalt der TXT-Datei
        file_content = "".join(file_lines)
        from io import BytesIO
        file_bytes = file_content.encode("utf-8")
        file_obj = BytesIO(file_bytes)
        file_obj.seek(0)

        summary_embed = discord.Embed(title="Server Ban List Imported", color=discord.Color.red())
        summary_embed.add_field(name="Imported Users", value=f"{len(imported_users)}", inline=True)
        summary_embed.add_field(name="Skipped (Already Imported)", value=f"{len(skipped_users)}", inline=True)
        summary_embed.set_footer(text="See attached file for details.")

        await ctx.respond(embed=summary_embed, file=discord.File(fp=file_obj, filename="imported_users.txt"))


    @commands.slash_command(name="macunbanallserver", description="Unban all users from this server that were imported via the global ban list.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def macunbanallserver(self, ctx: discord.ApplicationContext):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        await ctx.defer()
        working_embed = discord.Embed(
            title="⏳ Processing Unban All",
            description="Please wait while I unban all users from this server...",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=working_embed)

        global_bans = load_bans()
        server_bans = [ban for ban in global_bans if ban.get("serverid") == ctx.guild.id]
        if not server_bans:
            embed = discord.Embed(
                title="No Server Ban Records",
                description="ℹ️ There are no global ban records for this server.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed)
            return

        unbanned_users = []
        failed_users = []
        for ban in server_bans:
            user_id = ban["id"]
            try:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.unban(user, reason="Mac global unban (unbanallserver)")
                unbanned_users.append(f"{user.name} ({user.id})")
            except Exception as e:
                failed_users.append(f"{ban['name']} ({ban['id']})")
            await asyncio.sleep(1)
        remaining_bans = [ban for ban in global_bans if ban.get("serverid") != ctx.guild.id]
        save_bans(remaining_bans)
        embed = discord.Embed(title="Unban All from Server", color=discord.Color.green())
        embed.add_field(name="Successfully Unbanned", value="\n".join(unbanned_users) if unbanned_users else "None", inline=False)
        embed.add_field(name="Failed to Unban", value="\n".join(failed_users) if failed_users else "None", inline=False)
        await ctx.respond(embed=embed)


    @commands.slash_command(name="maclookupserver", description="Lookup global ban records for a specific server by ID.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def maclookupserver(self, ctx: discord.ApplicationContext, serverid: str):
        if not self.is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.")
            return

        global_bans = load_bans()
        server_bans = [ban for ban in global_bans if str(ban.get("serverid")) == serverid]
        if not server_bans:
            embed = discord.Embed(
                title="🚫 No Ban Records for Server",
                description=f"ℹ️ There are no global ban records for server ID **{serverid}**.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed)
            return

        embed = discord.Embed(title="📜 Global Ban Records for Server", color=discord.Color.red())
        embed.add_field(name="🔍 Server ID", value=serverid, inline=True)
        server_name = server_bans[0].get("servername", "Unknown")
        embed.add_field(name="🏷️ Server Name", value=server_name, inline=True)

        ban_list = ""
        for ban in server_bans:
            ban_list += f"• **{ban['name']}** (ID: `{ban['id']}`) - Banned on **{ban['bandate']}**\n"

        embed.add_field(name="👥 Banned Users", value=trim_field(ban_list) or "No banned users found.", inline=False)
        await ctx.respond(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(MacBan(bot))
