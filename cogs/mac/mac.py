import discord
from discord.ext import commands
import datetime
import asyncio
import os
from handlers.env import get_mac_channel
from handlers.config import mac_load_bans, mac_save_bans
from extensions.macextension import trim_field, is_authorized, create_mac_embed

NOTIFY_CHANNEL_ID = int(get_mac_channel())

class MacBan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        bans = mac_load_bans()
        ban_record = bans.get(str(member.id))
        if not ban_record:
            return

        attempted_server = member.guild.name
        try:
            dm_embed = create_mac_embed(
                title="🚫 Global Ban Notification",
                description="You are **globally banned** by MAC™ and cannot join any protected servers. Your account has been restricted from participating in MAC™ protected servers.",
                color=discord.Color.red()
            )
            dm_embed.add_field(name="▫️ Attempted Server", value=f"`{attempted_server}`", inline=True)
            dm_embed.add_field(name="▫️ Ban Date", value=f"`{ban_record.get('bandate', 'Unknown')}`", inline=True)
            dm_embed.add_field(name="▫️ Reason", value=f"```{trim_field(ban_record.get('reason', 'No reason provided'))}```", inline=False)
            dm_embed.add_field(name="Need Help?", value="> Contact support: [discord.ag7-dev.de](https://discord.ag7-dev.de)", inline=False)
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        try:
            await member.kick(reason="Globally banned user attempted to join")
        except Exception as e:
            pass

        channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
        if channel:
            notify_embed = create_mac_embed(
                title="🚨 Security Alert - Banned User Detected",
                description=f"**{member.mention}** attempted to join `{attempted_server}`",
                color=discord.Color.red()
            )
            notify_embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
            notify_embed.add_field(name="Ban Origin", value=f"`{ban_record.get('servername', 'Unknown')}`", inline=True)
            notify_embed.add_field(name="Ban Reason", value=f"```{trim_field(ban_record.get('reason', 'No reason provided'))}```", inline=False)
            await channel.send(embed=notify_embed)

    @commands.slash_command(name="mac-ban", description="Globally ban a user")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def macban(self, ctx: discord.ApplicationContext, user: discord.User, reason: str = "No reason provided"):
        if not is_authorized(ctx):
            return await ctx.respond("❌ Unauthorized access", ephemeral=True)

        bans = mac_load_bans()
        if str(user.id) in bans:
            embed = create_mac_embed(
                title="⚠️ Existing Ban Record",
                description=f"**{user.mention}** is already globally banned",
                color=discord.Color.orange()
            )
            embed.add_field(name="Current Reason", value=f"```{trim_field(bans[str(user.id)]['reason'])}```", inline=False)
            return await ctx.respond(embed=embed)

        ban_record = {
            "name": user.name,
            "bandate": datetime.datetime.utcnow().isoformat(),
            "reason": reason,
            "serverid": ctx.guild.id if ctx.guild else None,
            "servername": ctx.guild.name if ctx.guild else None,
            "bannedby": f"{ctx.author.name} ({ctx.author.id})"
        }
        bans[str(user.id)] = ban_record
        mac_save_bans(bans)

        embed = create_mac_embed(
            title="🔨 Global Ban Issued",
            description=f"**{user.mention}** has been added to the global ban list",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Ban Date", value=f"<t:{int(datetime.datetime.fromisoformat(ban_record['bandate']).timestamp())}:F>", inline=True)
        await ctx.respond(embed=embed)

        try:
            user_embed = create_mac_embed(
                title="🚫 Global Ban Notification",
                description="Your account has been restricted from participating in MAC™ protected servers.",
                color=discord.Color.red()
            )
            user_embed.add_field(name="Appeal Information", value="> Contact support: [discord.ag7-dev.de](https://discord.ag7-dev.de)", inline=False)
            await user.send(embed=user_embed)
        except discord.Forbidden:
            pass

    @commands.slash_command(name="mac-unban", description="Remove a global ban for a user.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def macunban(self, ctx: discord.ApplicationContext, user: discord.User):
        if not is_authorized(ctx):
            return await ctx.respond("❌ Unauthorized access", ephemeral=True)

        bans = mac_load_bans()
        if str(user.id) not in bans:
            embed = create_mac_embed(
                title="⚠️ No Global Ban Found",
                description=f"**{user.mention}** is not globally banned.",
                color=discord.Color.orange()
            )
            return await ctx.respond(embed=embed)

        del bans[str(user.id)]
        mac_save_bans(bans)

        embed = create_mac_embed(
            title="✅ Global Ban Removed",
            description=f"**{user.mention}** has been removed from the global ban list.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

        try:
            user_embed = create_mac_embed(
                title="Global Ban Removed",
                description="You have been removed from the global ban list by MAC™.",
                color=discord.Color.green()
            )
            await user.send(embed=user_embed)
        except discord.Forbidden:
            dm_error_embed = create_mac_embed(
                title="User DM Error",
                description="The user has their DMs closed.",
                color=discord.Color.red()
            )
            await ctx.send(embed=dm_error_embed)

        channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
        if channel:
            notify_embed = create_mac_embed(
                title="🚨 Security Alert - Global Ban Removed",
                description=f"**{user.mention}** has been removed from the global ban list.",
                color=discord.Color.green()
            )
            notify_embed.add_field(name="User ID", value=f"`{user.id}`", inline=True)
            await channel.send(embed=notify_embed)

    @commands.slash_command(name="mac-info", description="Display overall info about the global ban list.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def macinfo(self, ctx: discord.ApplicationContext):
        if not is_authorized(ctx):
            await ctx.respond("❌ Unauthorized access", ephemeral=True)
            return

        bans = mac_load_bans()
        embed = create_mac_embed(
            title="🌍 Global Ban List Info",
            description="Here is the overall information about the global ban list.",
            color=discord.Color.blue()
        )
        embed.add_field(name="📊 Total Global Bans", value=str(len(bans)), inline=False)

        if bans:
            ban_list = ""
            for user_id, ban in list(bans.items())[:5]:  
                ban_list += f"• **{ban['name']}** (ID: `{user_id}`) - Banned on **{ban['bandate']}**\n"
            embed.add_field(name="📰 Recent Bans", value=trim_field(ban_list), inline=False)
        else:
            embed.add_field(name="🚫 No Bans", value="The global ban list is empty.", inline=False)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="mac-showbanlist", description="Export this server's MAC ban records as a file.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def macshowbanlist(self, ctx: discord.ApplicationContext):
        if not is_authorized(ctx):
            await ctx.respond("❌ Unauthorized access", ephemeral=True)
            return

        bans = mac_load_bans()
        server_bans = [ban for ban in bans.values() if str(ban.get("serverid")) == str(ctx.guild.id)]

        if not server_bans:
            embed = create_mac_embed(
                title="No Ban Records",
                description="ℹ️ There are no global ban records for this server.",
                color=discord.Color.green(),
            )
            await ctx.respond(embed=embed)
            return

        filename = f"mac_banlist_{ctx.guild.id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for ban in server_bans:
                line = f"{ban['id']} | {ban['name']} | {ban['reason']} | {ban['bandate']}\n"
                f.write(line)

        embed = create_mac_embed(
            title="📄 Ban List Exported",
            description=f"Exported {len(server_bans)} entries.",
            color=discord.Color.blue(),
        )
        await ctx.respond(embed=embed, file=discord.File(filename))
        os.remove(filename)



    @commands.slash_command(name="mac-lookup", description="Lookup detailed ban info for a user.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def maclookup(self, ctx: discord.ApplicationContext, user: discord.User):
        if not is_authorized(ctx):
            return await ctx.respond("❌ Unauthorized access", ephemeral=True)

        bans = mac_load_bans()
        for ban in bans.values():
            if ban["id"] == user.id:
                embed = create_mac_embed(
                    title="Global Ban Record Found",
                    description=f"Here is the detailed ban info for **{ban['name']}** (ID: {ban['id']}).",
                    color=discord.Color.red()
                )
                embed.add_field(name="Ban Date", value=ban["bandate"], inline=True)
                embed.add_field(name="Reason", value=trim_field(ban["reason"]), inline=True)
                embed.add_field(name="Server", value=f"{ban['servername']} (ID: {ban['serverid']})", inline=False)
                embed.add_field(name="Banned By", value=ban["bannedby"], inline=True)
                await ctx.respond(embed=embed)
                return

        embed = create_mac_embed(
            title="No Ban Record",
            description=f"ℹ️ {user.mention} is not globally banned.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)


    @commands.slash_command(name="mac-check", description="Check if a user is globally banned.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def maccheck(self, ctx: discord.ApplicationContext, user: discord.User):
        if not is_authorized(ctx):
            return await ctx.respond("❌ Unauthorized access", ephemeral=True)

        bans = mac_load_bans()
        for ban in bans.values():
            if ban["id"] == user.id:
                embed = create_mac_embed(
                    title="User is Globally Banned",
                    description=f"🔨 {user.mention} is globally banned.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Reason", value=trim_field(ban["reason"]), inline=False)
                await ctx.respond(embed=embed)
                return

        embed = create_mac_embed(
            title="User is Not Globally Banned",
            description=f"✅ {user.mention} is not globally banned.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)


    @commands.slash_command(name="mac-banall", description="Ban all users from the global ban list in this server.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def macbanall(self, ctx: discord.ApplicationContext):
        if not is_authorized(ctx):
            await ctx.respond("❌ Unauthorized access", ephemeral=True)
            return

        await ctx.defer()
        working_embed = create_mac_embed(
            title="⏳ Processing Global Ban All",
            description="Please wait while I ban all users from the global ban list...",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=working_embed)

        bans = mac_load_bans()
        if not bans:
            embed = create_mac_embed(
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

        embed = create_mac_embed(
            title="Global Ban All Executed",
            color=discord.Color.red()
        )
        embed.add_field(name="Successfully Banned", value="\n".join(banned_members) if banned_members else "None", inline=False)
        embed.add_field(name="Failed to Ban", value="\n".join(failed_members) if failed_members else "None", inline=False)
        await ctx.respond(embed=embed)


    @commands.slash_command(name="mac-unbanallserver", description="Unban all users from this server that were imported via the global ban list.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def macunbanallserver(self, ctx: discord.ApplicationContext):
        if not is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.", ephemeral=True)
            return

        await ctx.defer()
        working_embed = create_mac_embed(
            title="⏳ Processing Unban All",
            description="Please wait while I unban all users from this server...",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=working_embed)

        global_bans = mac_load_bans()
        server_bans = [ban for ban in global_bans if ban.get("serverid") == ctx.guild.id]
        if not server_bans:
            embed = create_mac_embed(
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
        mac_save_bans(remaining_bans)

        embed = create_mac_embed(
            title="Unban All from Server",
            color=discord.Color.green()
        )
        embed.add_field(name="Successfully Unbanned", value="\n".join(unbanned_users) if unbanned_users else "None", inline=False)
        embed.add_field(name="Failed to Unban", value="\n".join(failed_users) if failed_users else "None", inline=False)
        await ctx.respond(embed=embed)



    @commands.slash_command(name="mac-lookupserver", description="Lookup global ban records for a specific server by ID.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def maclookupserver(self, ctx: discord.ApplicationContext, serverid: str):
        if not is_authorized(ctx):
            await ctx.respond("❌ You are not authorized to use this command.", ephemeral=True)
            return

        global_bans = mac_load_bans()
        server_bans = [ban for ban in global_bans if str(ban.get("serverid")) == serverid]
        if not server_bans:
            embed = create_mac_embed(
                title="🚫 No Ban Records for Server",
                description=f"ℹ️ There are no global ban records for server ID **{serverid}**.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed)
            return

        embed = create_mac_embed(
            title="📜 Global Ban Records for Server",
            color=discord.Color.red()
        )
        embed.add_field(name="🔍 Server ID", value=serverid, inline=True)
        server_name = server_bans[0].get("servername", "Unknown")
        embed.add_field(name="🏷️ Server Name", value=server_name, inline=True)

        ban_list = ""
        for ban in server_bans:
            ban_list += f"• **{ban['name']}** (ID: `{ban['id']}`) - Banned on **{ban['bandate']}**\n"

        embed.add_field(name="👥 Banned Users", value=trim_field(ban_list) or "No banned users found.", inline=False)
        await ctx.respond(embed=embed)


    @commands.slash_command(name="mac-scanserver", description="Scans if any user on the server is globally banned.")
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def macscanserver(self, ctx: discord.ApplicationContext):

        loading_embed = create_mac_embed(
            title="🔄 Scanning for Banned Users...",
            description="Please wait while I scan the server for globally banned users. This may take a moment.",
            color=discord.Color.blue()
        )
        loading_embed.set_footer(text="Loading... Please be patient.")
        loading_message = await ctx.respond(embed=loading_embed)

        global_bans = mac_load_bans()
        banned_users = []

        for member in ctx.guild.members:
            for ban in global_bans:
                if str(ban.get("serverid")) == str(ctx.guild.id) and str(ban.get("id")) == str(member.id):
                    banned_users.append(ban)
                    break

        if not banned_users:
            embed = create_mac_embed(
                title="🚫 No Banned Users Found",
                description="There are no users in this server who are currently banned globally.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Global Ban Scan completed.")
            await loading_message.edit(embed=embed)
            return

        embed = create_mac_embed(
            title="🚫 Banned Users Found",
            description="The following users are globally banned and are currently on this server:",
            color=discord.Color.red()
        )

        banned_user_details = []
        for ban in banned_users:
            member = ctx.guild.get_member(ban["id"])
            if member:
                banned_user_details.append(f"{member.mention} - ID: {ban['id']}")
                embed.add_field(
                    name=f"{member.name} (ID: {ban['id']})",
                    value=f"**Ban Date**: {ban['bandate']}\n"
                           f"**Reason**: {trim_field(ban['reason'])}\n"
                           f"**Server**: {ban['servername']} (ID: {ban['serverid']})\n"
                           f"**Banned By**: {ban['bannedby']}",
                    inline=False
                )

        embed.add_field(
            name="Banned Users List",
            value="\n".join(banned_user_details),
            inline=False
        )
        embed.set_footer(text="Global Ban Scan completed.")
        await loading_message.edit(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(MacBan(bot))
