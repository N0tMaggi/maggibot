import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Button, button, channel_select, role_select
from discord import ui
import datetime
import handlers.config as config
from handlers.debug import LogDebug

class ProtectionConfigView(View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.config = config.loadserverconfig()  # [[5]]
        self.current_protection = self.config.get(str(guild_id), {}).get("protection", False)
        self.current_log_channel = self.config.get(str(guild_id), {}).get("logchannel", None)

    @channel_select(
        placeholder="Select log channel",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1
    )
    async def log_channel_select(self, select: channel_select, interaction: discord.Interaction):
        new_channel_id = select.values[0].id
        guild_config = self.config.setdefault(str(self.guild_id), {})
        guild_config["logchannel"] = new_channel_id
        config.saveserverconfig(self.config)  # [[5]]
        
        embed = interaction.message.embeds[0]
        embed.description = (
            f"Protection: {'Enabled' if self.current_protection else 'Disabled'}\n"
            f"Log Channel: {select.values[0].mention}"
        )
        await interaction.response.edit_message(embed=embed)
        LogDebug(f"Log channel set to {new_channel_id} by {interaction.user.id}")

    @button(label="Enable Protection", style=discord.ButtonStyle.green)
    async def enable_button(self, button: Button, interaction: discord.Interaction):
        await self.update_protection(interaction, True)

    @button(label="Disable Protection", style=discord.ButtonStyle.red)
    async def disable_button(self, button: Button, interaction: discord.Interaction):
        await self.update_protection(interaction, False)

    async def update_protection(self, interaction, new_state):
        guild_config = self.config.setdefault(str(self.guild_id), {})
        guild_config["protection"] = new_state
        config.saveserverconfig(self.config)  # [[5]]
        
        embed = interaction.message.embeds[0]
        embed.description = (
            f"Protection: {'Enabled' if new_state else 'Disabled'}\n"
            f"Log Channel: <#{self.current_log_channel}>" if self.current_log_channel else "No log channel set"
        )
        await interaction.response.edit_message(embed=embed)
        LogDebug(f"Protection set to {new_state} by {interaction.user.id}")

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

class ProtectionSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name="setup-protection",
        description="Configure server protection and logging"
    )
    @commands.has_permissions(administrator=True)
    async def setup_protection(self, ctx: discord.ApplicationContext):
        guild_id = str(ctx.guild.id)
        config_data = config.loadserverconfig().get(guild_id, {})
        
        current_protection = config_data.get("protection", False)
        current_log_channel = config_data.get("logchannel", None)

        embed = discord.Embed(
            title="🛡️ Protection Configuration",
            description=(
                f"Protection: {'Enabled' if current_protection else 'Disabled'}\n"
                f"Log Channel: <#{current_log_channel}>" if current_log_channel else "No log channel set"
            ),
            color=0x2ECC71 if current_protection else 0xE74C3C,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Protection affects security features like anti-spam and moderation")

        view = ProtectionConfigView(self.bot, ctx.guild.id)
        view.message = await ctx.respond(embed=embed, view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(ProtectionSettings(bot))