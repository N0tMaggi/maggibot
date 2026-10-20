import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Button, button, channel_select, role_select
from discord import ui
import handlers.config as config
from handlers.debug import LogDebug
from utils.embed_helpers import (
    create_embed,
    create_mod_embed,
    create_security_embed,
    create_success_embed,
    create_error_embed,
    create_warning_embed,
)

async def create_protection_status_embed(ctx_or_interaction, enabled: bool, log_channel_id: int | None) -> discord.Embed:
    guild = getattr(ctx_or_interaction, "guild", None)
    user = getattr(ctx_or_interaction, "user", None) or getattr(ctx_or_interaction, "author", None)
    
    if user:
        name = user.name
        discriminator = getattr(user, "discriminator", None)
        tag = f"{name}#{discriminator}" if discriminator and discriminator != "0" else name
        user_label = f"{user.mention}\n{tag}"
    else:
        user_label = "Unknown"

    status = "Enabled ✅" if enabled else "Disabled ❌"
    log_channel_value = f"<#{log_channel_id}>" if log_channel_id else "Not set"

    fields = [
        ("Action Performed By", user_label, True),
        ("Protection Status", status, False),
        ("Log Channel", log_channel_value, False),
    ]

    embed = create_security_embed(
        title="Protection Configuration",
        description="Current server protection settings.",
        color='success' if enabled else 'error',
        footer_text=f"Server ID: {guild.id} • Protection System" if guild else "Protection System",
        fields=fields
    )

    if guild and guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)

    return embed

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
        self.current_log_channel = new_channel_id
        embed = await create_protection_status_embed(
            interaction,
            self.current_protection,
            self.current_log_channel,
        )
        await interaction.response.edit_message(embed=embed, view=self)
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
        self.current_protection = new_state
        embed = await create_protection_status_embed(
            interaction,
            self.current_protection,
            self.current_log_channel,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        LogDebug(f"Protection set to {new_state} by {interaction.user.id}")

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.NotFound:
            LogDebug("Protection setup message no longer exists on timeout")

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

        embed = await create_protection_status_embed(
            ctx,
            current_protection,
            current_log_channel,
        )

        view = ProtectionConfigView(self.bot, ctx.guild.id)
        view.message = await ctx.respond(embed=embed, view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(ProtectionSettings(bot))
