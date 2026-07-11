import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import Button, button, channel_select
import handlers.config as config
from handlers.debug import LogDebug
from extensions.protectionextension import create_protection_status_embed
from utils.components import build_view

class ProtectionChannelRow(discord.ui.ActionRow):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.channel_select_menu = discord.ui.ChannelSelect(
            placeholder="Select log channel",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )
        self.channel_select_menu.callback = self.select_callback
        self.add_item(self.channel_select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        new_channel_id = self.channel_select_menu.values[0].id
        guild_config = self.parent_view.config.setdefault(str(self.parent_view.guild_id), {})
        guild_config["logchannel"] = new_channel_id
        config.saveserverconfig(self.parent_view.config)
        self.parent_view.current_log_channel = new_channel_id
        container = await create_protection_status_embed(
            interaction,
            self.parent_view.current_protection,
            self.parent_view.current_log_channel,
        )
        self.parent_view.set_container(container)
        await interaction.response.edit_message(view=self.parent_view)
        LogDebug(f"Log channel set to {new_channel_id} by {interaction.user.id}")


class ProtectionButtonsRow(discord.ui.ActionRow):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

        self.enable_button = discord.ui.Button(label="Enable Protection", style=discord.ButtonStyle.green)
        self.disable_button = discord.ui.Button(label="Disable Protection", style=discord.ButtonStyle.red)

        self.enable_button.callback = self.enable_callback
        self.disable_button.callback = self.disable_callback

        self.add_item(self.enable_button)
        self.add_item(self.disable_button)

    async def enable_callback(self, interaction: discord.Interaction):
        await self.parent_view.update_protection(interaction, True)

    async def disable_callback(self, interaction: discord.Interaction):
        await self.parent_view.update_protection(interaction, False)


class ProtectionConfigView(discord.ui.DesignerView):
    def __init__(self, bot, guild_id, container):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.config = config.loadserverconfig()  # [[5]]
        self.current_protection = self.config.get(str(guild_id), {}).get("protection", False)
        self.current_log_channel = self.config.get(str(guild_id), {}).get("logchannel", None)
        self.message = None

        self.channel_row = ProtectionChannelRow(self)
        self.buttons_row = ProtectionButtonsRow(self)
        self.container_item = None
        self.set_container(container)
        self.add_item(self.channel_row)
        self.add_item(self.buttons_row)

    def set_container(self, container):
        if self.container_item is not None:
            self.remove_item(self.container_item)
        self.container_item = container
        self.add_item(container)

    async def update_protection(self, interaction, new_state):
        guild_config = self.config.setdefault(str(self.guild_id), {})
        guild_config["protection"] = new_state
        config.saveserverconfig(self.config)  # [[5]]
        self.current_protection = new_state
        container = await create_protection_status_embed(
            interaction,
            self.current_protection,
            self.current_log_channel,
        )
        self.set_container(container)
        await interaction.response.edit_message(view=self)
        LogDebug(f"Protection set to {new_state} by {interaction.user.id}")

    async def on_timeout(self):
        for item in self.channel_row.children:
            item.disabled = True
        for item in self.buttons_row.children:
            item.disabled = True
        try:
            await self.message.edit_original_response(view=self)
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

        container = await create_protection_status_embed(
            ctx,
            current_protection,
            current_log_channel,
        )

        view = ProtectionConfigView(self.bot, ctx.guild.id, container)
        view.message = await ctx.respond(view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(ProtectionSettings(bot))
