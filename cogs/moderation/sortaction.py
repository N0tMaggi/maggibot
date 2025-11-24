import discord
from discord import utils
from discord.ext import commands
from discord.commands import slash_command
import os
import asyncio
from utils.embed_helpers import create_embed as utils_create_embed

class SortedAction(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    def create_embed(self, title, description, color=None):
        """Helper function to create uniform embeds."""
        if color is None:
            color = discord.Color.blue()
        embed = utils_create_embed(
            title=title,
            description=description,
            color=color,
            bot_user=self.bot.user
        )
        embed.set_footer(text="Moderation Action | Bot")
        return embed

    @slash_command(name="sortedaction", description="Perform actions (ban/kick) on users with a specific role.")
    async def sortedaction(self, ctx: discord.ApplicationContext, 
                           role: discord.Role, 
                           export: bool, 
                           action: discord.Option(str, "Action to perform (ban/kick)", choices=["ban", "kick"], default=None)):
        
        # Prüfung: Hat der Nutzer die Berechtigung?
        if action == "ban" and not ctx.author.guild_permissions.ban_members:
            embed = self.create_embed("🚫 Permission Denied", "You do not have the `ban_members` permission.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return
        elif action == "kick" and not ctx.author.guild_permissions.kick_members:
            embed = self.create_embed("🚫 Permission Denied", "You do not have the `kick_members` permission.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        role_obj = discord.utils.get(ctx.guild.roles, name=role.name)
        if not role_obj:
            embed = self.create_embed("❌ Error", f"Role '{role}' not found.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        members_with_role = [member for member in ctx.guild.members if role_obj in member.roles]
        total_users = len(members_with_role)

        if not total_users:
            embed = self.create_embed("🔍 No Users Found", f"No users found with the role '{role}'.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return
        
        # Export-Bereich
        if export:
            with open("exported_users.txt", "w", encoding="utf-8") as f:
                for member in members_with_role:
                    join_date = member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{member.id} | {str(member)} | Joined: {join_date}\n")
            
            embed = self.create_embed(
                "📤 Export Successful", 
                f"User IDs and join dates have been exported. **{total_users} user(s)** found.", 
                color=discord.Color.green()
            )
            embed.add_field(
                name="📄 File Details", 
                value="Format: `ID | Username | Joined`\nFile will be deleted after sending."
            )
            await ctx.respond(embed=embed, file=discord.File("exported_users.txt"))
            os.remove("exported_users.txt")  # Datei löschen

        if action is None:
            embed = self.create_embed("ℹ️ No Action Performed", "Only export was requested. No ban/kick action was executed.", color=discord.Color.orange())
            await ctx.respond(embed=embed)
            return

        # Prüfung: Hat der Bot die Berechtigung?
        if action == "ban" and not ctx.guild.me.guild_permissions.ban_members:
            embed = self.create_embed("⚠️ Permission Missing", "I do not have the `ban_members` permission.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return
        elif action == "kick" and not ctx.guild.me.guild_permissions.kick_members:
            embed = self.create_embed("⚠️ Permission Missing", "I do not have the `kick_members` permission.", color=discord.Color.red())
            await ctx.respond(embed=embed)
            return

        # Initialer Progress-Embed
        progress_embed = self.create_embed(
            "🔄 Action Started", 
            f"Starting `{action}` for {total_users} users.", 
            color=discord.Color.yellow()
        )
        progress_embed.add_field(
            name="📊 Progress", 
            value="**Processed: 0/0**\n**Success: 0 | Failed: 0**"
        )
        progress_message = await ctx.respond(embed=progress_embed)

        # Aktion durchführen
        success_count = 0
        failed_count = 0
        for idx, member in enumerate(members_with_role, 1):
            try:
                # Selbstschutz
                if member.id == ctx.guild.me.id:
                    raise Exception("Bot cannot act on itself")
                # Serverinhaber-Schutz
                if member.id == ctx.guild.owner_id:
                    raise Exception("Cannot act on server owner")
                # Rollen-Rangfolge
                if member.top_role >= ctx.guild.me.top_role:
                    raise Exception("Member has higher or equal role")

                if action == "ban":
                    await member.ban(reason=f"Performed by {ctx.author} via /sortedaction", delete_message_days=7)
                elif action == "kick":
                    await member.kick(reason=f"Performed by {ctx.author} via /sortedaction")
                success_count += 1

            except Exception as e:
                failed_count += 1

            # Aktualisiere Progress-Embed
            progress_embed.set_field_at(
                index=0,
                name="📊 Progress",
                value=f"**Processed: {idx}/{total_users}**\n**Success: {success_count} | Failed: {failed_count}**"
            )
            await progress_message.edit(embed=progress_embed)
            await asyncio.sleep(0.5)  # Rate Limit Schutz 

        # Abschlussmeldung
        final_embed = self.create_embed(
            "✅ Action Completed", 
            f"Successfully {action}ed **{success_count}/{total_users}** users.", 
            color=discord.Color.green()
        )
        final_embed.add_field(name="📈 Summary", value=f"Success: {success_count}\nFailed: {failed_count}")
        await progress_message.edit(embed=final_embed)

def setup(bot: discord.Bot):
    bot.add_cog(SortedAction(bot))