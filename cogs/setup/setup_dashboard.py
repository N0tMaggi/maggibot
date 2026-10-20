# -*- coding: utf-8 -*-
"""
MaggiBot Unified Interactive Setup Dashboard (Interactions v2)
Centralized interactive control center replacing fragmented setup commands.
Uses Discord Buttons, ChannelSelect, RoleSelect, StringSelect, and Modals.
"""

import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Button, Select, Modal, InputText

from utils.embed_helpers import create_embed
from utils.colors import EmbedColors
import handlers.config as config
from handlers.debug import LogDebug, LogError


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# VoiceGate Rules Modal
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
class VoiceGateRulesModal(Modal):
    def __init__(self, parent_view: "DashboardView"):
        super().__init__(title="VoiceGate Regeln festlegen")
        self.parent_view = parent_view
        current_rules = self.parent_view.voicegate_config.get(
            str(parent_view.guild.id), {}
        ).get("rules_text", "")
        self.rules_input = InputText(
            label="Regeltext für VoiceGate",
            placeholder="Schreibe hier die Serverregeln für den VoiceGate...",
            style=discord.InputTextStyle.long,
            default=current_rules if current_rules else None,
            max_length=1500,
            required=True
        )
        self.add_item(self.rules_input)

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(self.parent_view.guild.id)
        if guild_id not in self.parent_view.voicegate_config:
            self.parent_view.voicegate_config[guild_id] = {}
        self.parent_view.voicegate_config[guild_id]["rules_text"] = self.rules_input.value
        self.parent_view.voicegate_config[guild_id]["need_accept_rules"] = True
        config.savevoicegateconfig(self.parent_view.voicegate_config)

        await self.parent_view.refresh_state()
        embed = self.parent_view.build_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Main Interactive Dashboard View
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
class DashboardView(View):
    def __init__(self, bot: discord.Bot, guild: discord.Guild, author: discord.Member):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild = guild
        self.author = author
        self.current_category = "overview"

        # Load states
        self.server_config = {}
        self.voicegate_config = {}
        self.onlyimages = {}
        self.admin_feedback = {}
        self.lockdown = False
        self._load_configs()
        self._build_components()

    def _load_configs(self):
        all_cfg = config.loadserverconfig()
        self.server_config = all_cfg.setdefault(str(self.guild.id), {})
        self.voicegate_config = config.loadvoicegateconfig()
        self.onlyimages = config.load_onlyimages()
        self.admin_feedback = config.load_admin_feedback()
        self.lockdown = config.load_lockdown_config().get("lockdown", False)

    async def refresh_state(self):
        self._load_configs()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Nur der Administrator, der dieses Dashboard geöffnet hat, kann interagieren.",
                ephemeral=True
            )
            return False
        return True

    def build_embed(self) -> discord.Embed:
        guild_id_str = str(self.guild.id)
        vg = self.voicegate_config.get(guild_id_str, {})
        af = self.admin_feedback.get("configs", {}).get(guild_id_str, {})

        embed = create_embed(
            title=f"⚙️ {self.guild.name} • Server Control Center",
            description=(
                "Willkommen im interaktiven MaggiBot Konfigurations-Dashboard.\n"
                "Verwende das Auswahlmenü und die Schaltflächen darunter, um Module "
                "in Echtzeit zu verwalten."
            ),
            color=EmbedColors.INFO,
            bot_user=self.bot.user,
            thumbnail=self.guild.icon.url if self.guild.icon else None
        )

        # 1. Protection & Automod
        prot_active = self.server_config.get("protection", False)
        antispam = self.server_config.get("antispam", False)
        antiraid = self.server_config.get("antiraid", False)
        antighost = self.server_config.get("antighostping", False)
        antiwebhook = self.server_config.get("antiwebhook", False)
        lockdown_str = "🔒 AKTIV" if self.lockdown else "🔓 Inaktiv"

        prot_status = (
            f"• Hauptschutz: {'🟢 AN' if prot_active else '🔴 AUS'}\n"
            f"• Anti-Spam: {'🟢' if antispam else '⚪'} | "
            f"Anti-Raid: {'🟢' if antiraid else '⚪'} | "
            f"Anti-GhostPing: {'🟢' if antighost else '⚪'}\n"
            f"• Anti-Webhook: {'🟢' if antiwebhook else '⚪'} | "
            f"Server-Lockdown: `{lockdown_str}`"
        )
        embed.add_field(name="🛡️ Schutz & Sicherheit", value=prot_status, inline=False)

        # 2. Logging
        log_channel_id = self.server_config.get("logchannel")
        log_forum_id = self.server_config.get("logging_forum")
        log_desc = []
        if log_forum_id:
            log_desc.append(f"• Log-Forum: <#{log_forum_id}>")
        if log_channel_id:
            log_desc.append(f"• Text-Logchannel: <#{log_channel_id}>")
        if not log_desc:
            log_desc.append("• Keine Logging-Channels konfiguriert")
        embed.add_field(name="📋 Audit & Logging", value="\n".join(log_desc), inline=False)

        # 3. Roles & Access
        autorole_id = self.server_config.get("autoroleid")
        vg_gate = vg.get("gate_channel_id")
        vg_final = vg.get("final_channel_id")
        vr_give = self.server_config.get("role_to_give")

        roles_desc = [
            f"• AutoRole: {f'<@&{autorole_id}>' if autorole_id else 'Nicht gesetzt'}",
            f"• VoiceGate: {f'<#{vg_gate}> ➔ <#{vg_final}>' if (vg_gate and vg_final) else 'Nicht aktiv'}",
            f"• Verify-Rolle: {f'<@&{vr_give}>' if vr_give else 'Nicht gesetzt'}"
        ]
        embed.add_field(name="👥 Rollen & Zugang", value="\n".join(roles_desc), inline=False)

        # 4. Media & Specials
        onlyimg_count = sum(1 for cid in self.onlyimages.keys() if self.guild.get_channel(int(cid)) is not None)
        tiktok_active = self.server_config.get("tiktok_auto_embed", True)
        media_desc = [
            f"• Only-Images Kanäle: `{onlyimg_count}` aktiv",
            f"• TikTok Auto-Download: {'🟢 AN' if tiktok_active else '🔴 AUS'}"
        ]
        embed.add_field(name="🖼️ Medien & Spezial-Kanäle", value="\n".join(media_desc), inline=True)

        # 5. Feedback
        team_role_id = af.get("team_role")
        embed.add_field(
            name="💬 Admin-Feedback",
            value=f"• Team-Rolle: {f'<@&{team_role_id}>' if team_role_id else 'Nicht gesetzt'}",
            inline=True
        )

        return embed

    def _build_components(self):
        self.clear_items()

        # Category Select (Always visible on row 0)
        category_options = [
            discord.SelectOption(
                label="Übersicht (Dashboard)",
                value="overview",
                emoji="📊",
                default=(self.current_category == "overview")
            ),
            discord.SelectOption(
                label="Schutz & Automod",
                value="protection",
                emoji="🛡️",
                default=(self.current_category == "protection")
            ),
            discord.SelectOption(
                label="Audit & Logging",
                value="logging",
                emoji="📋",
                default=(self.current_category == "logging")
            ),
            discord.SelectOption(
                label="Rollen & VoiceGate",
                value="roles",
                emoji="👥",
                default=(self.current_category == "roles")
            ),
            discord.SelectOption(
                label="Medien & Spezial",
                value="media",
                emoji="🖼️",
                default=(self.current_category == "media")
            ),
        ]

        cat_select = Select(
            placeholder="Kategorie zur Konfiguration wählen...",
            options=category_options,
            row=0
        )
        cat_select.callback = self._on_category_select
        self.add_item(cat_select)

        # Category-specific items
        if self.current_category == "protection":
            self._add_protection_items()
        elif self.current_category == "logging":
            self._add_logging_items()
        elif self.current_category == "roles":
            self._add_roles_items()
        elif self.current_category == "media":
            self._add_media_items()
        else:
            self._add_overview_items()

    def _add_overview_items(self):
        refresh_btn = Button(label="Aktualisieren", emoji="🔄", style=discord.ButtonStyle.secondary, row=1)
        refresh_btn.callback = self._on_refresh
        self.add_item(refresh_btn)

        close_btn = Button(label="Schließen", emoji="✖️", style=discord.ButtonStyle.danger, row=1)
        close_btn.callback = self._on_close
        self.add_item(close_btn)

    def _add_protection_items(self):
        prot_active = self.server_config.get("protection", False)
        antispam = self.server_config.get("antispam", False)
        antiraid = self.server_config.get("antiraid", False)
        antighost = self.server_config.get("antighostping", False)
        antiwebhook = self.server_config.get("antiwebhook", False)

        btn_main = Button(
            label=f"Hauptschutz: {'AN' if prot_active else 'AUS'}",
            style=discord.ButtonStyle.success if prot_active else discord.ButtonStyle.secondary,
            emoji="🛡️",
            row=1
        )
        btn_main.callback = lambda i: self._toggle_setting(i, "protection")
        self.add_item(btn_main)

        btn_spam = Button(
            label=f"Anti-Spam: {'AN' if antispam else 'AUS'}",
            style=discord.ButtonStyle.success if antispam else discord.ButtonStyle.secondary,
            emoji="🚫",
            row=1
        )
        btn_spam.callback = lambda i: self._toggle_setting(i, "antispam")
        self.add_item(btn_spam)

        btn_raid = Button(
            label=f"Anti-Raid: {'AN' if antiraid else 'AUS'}",
            style=discord.ButtonStyle.success if antiraid else discord.ButtonStyle.secondary,
            emoji="⚔️",
            row=1
        )
        btn_raid.callback = lambda i: self._toggle_setting(i, "antiraid")
        self.add_item(btn_raid)

        btn_ghost = Button(
            label=f"Anti-GhostPing: {'AN' if antighost else 'AUS'}",
            style=discord.ButtonStyle.success if antighost else discord.ButtonStyle.secondary,
            emoji="👻",
            row=2
        )
        btn_ghost.callback = lambda i: self._toggle_setting(i, "antighostping")
        self.add_item(btn_ghost)

        btn_webhook = Button(
            label=f"Anti-Webhook: {'AN' if antiwebhook else 'AUS'}",
            style=discord.ButtonStyle.success if antiwebhook else discord.ButtonStyle.secondary,
            emoji="🔗",
            row=2
        )
        btn_webhook.callback = lambda i: self._toggle_setting(i, "antiwebhook")
        self.add_item(btn_webhook)

        btn_lockdown = Button(
            label=f"Lockdown: {'AKTIV' if self.lockdown else 'INAKTIV'}",
            style=discord.ButtonStyle.danger if self.lockdown else discord.ButtonStyle.secondary,
            emoji="🔒",
            row=2
        )
        btn_lockdown.callback = self._toggle_lockdown
        self.add_item(btn_lockdown)

        back_btn = Button(label="« Übersicht", style=discord.ButtonStyle.primary, row=3)
        back_btn.callback = self._back_to_overview
        self.add_item(back_btn)

    def _add_logging_items(self):
        chan_select = discord.ui.ChannelSelect(
            placeholder="Text- oder Forum-Channel für Logs auswählen...",
            channel_types=[discord.ChannelType.text, discord.ChannelType.forum],
            min_values=1,
            max_values=1,
            row=1
        )
        chan_select.callback = self._on_log_channel_select
        self.add_item(chan_select)

        clear_btn = Button(label="Logchannel entfernen", emoji="🗑️", style=discord.ButtonStyle.danger, row=2)
        clear_btn.callback = self._clear_log_channel
        self.add_item(clear_btn)

        back_btn = Button(label="« Übersicht", style=discord.ButtonStyle.primary, row=2)
        back_btn.callback = self._back_to_overview
        self.add_item(back_btn)

    def _add_roles_items(self):
        role_select = discord.ui.RoleSelect(
            placeholder="AutoRole auswählen (wird neuen Mitgliedern gegeben)...",
            min_values=1,
            max_values=1,
            row=1
        )
        role_select.callback = self._on_autorole_select
        self.add_item(role_select)

        del_autorole_btn = Button(label="AutoRole entfernen", emoji="🗑️", style=discord.ButtonStyle.secondary, row=2)
        del_autorole_btn.callback = self._clear_autorole
        self.add_item(del_autorole_btn)

        rules_modal_btn = Button(label="VoiceGate Regeln bearbeiten", emoji="📝", style=discord.ButtonStyle.primary, row=2)
        rules_modal_btn.callback = self._open_voicegate_modal
        self.add_item(rules_modal_btn)

        back_btn = Button(label="« Übersicht", style=discord.ButtonStyle.primary, row=2)
        back_btn.callback = self._back_to_overview
        self.add_item(back_btn)

    def _add_media_items(self):
        chan_select = discord.ui.ChannelSelect(
            placeholder="Only-Images Kanal hinzufügen oder entfernen...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=1
        )
        chan_select.callback = self._on_onlyimages_select
        self.add_item(chan_select)

        tiktok_active = self.server_config.get("tiktok_auto_embed", True)
        btn_tiktok = Button(
            label=f"TikTok Auto-Download: {'AN' if tiktok_active else 'AUS'}",
            style=discord.ButtonStyle.success if tiktok_active else discord.ButtonStyle.secondary,
            emoji="📥",
            row=2
        )
        btn_tiktok.callback = lambda i: self._toggle_setting(i, "tiktok_auto_embed")
        self.add_item(btn_tiktok)

        back_btn = Button(label="« Übersicht", style=discord.ButtonStyle.primary, row=2)
        back_btn.callback = self._back_to_overview
        self.add_item(back_btn)

    # Callbacks
    async def _on_category_select(self, interaction: discord.Interaction):
        self.current_category = interaction.data["values"][0]
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _back_to_overview(self, interaction: discord.Interaction):
        self.current_category = "overview"
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _on_refresh(self, interaction: discord.Interaction):
        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _on_close(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            pass
        self.stop()

    async def _toggle_setting(self, interaction: discord.Interaction, key: str):
        current = self.server_config.get(key, False)
        self.server_config[key] = not current
        all_cfg = config.loadserverconfig()
        all_cfg[str(self.guild.id)] = self.server_config
        config.saveserverconfig(all_cfg)

        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _toggle_lockdown(self, interaction: discord.Interaction):
        self.lockdown = not self.lockdown
        config.save_lockdown_config(self.lockdown)
        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _on_log_channel_select(self, interaction: discord.Interaction):
        channel = interaction.data["values"][0]
        chan_obj = self.guild.get_channel(int(channel))
        if chan_obj and chan_obj.type == discord.ChannelType.forum:
            self.server_config["logging_forum"] = chan_obj.id
            self.server_config["logchannel"] = chan_obj.id
        else:
            self.server_config["logchannel"] = int(channel)

        all_cfg = config.loadserverconfig()
        all_cfg[str(self.guild.id)] = self.server_config
        config.saveserverconfig(all_cfg)

        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _clear_log_channel(self, interaction: discord.Interaction):
        self.server_config.pop("logchannel", None)
        self.server_config.pop("logging_forum", None)
        all_cfg = config.loadserverconfig()
        all_cfg[str(self.guild.id)] = self.server_config
        config.saveserverconfig(all_cfg)

        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _on_autorole_select(self, interaction: discord.Interaction):
        role_id = int(interaction.data["values"][0])
        self.server_config["autoroleid"] = role_id
        all_cfg = config.loadserverconfig()
        all_cfg[str(self.guild.id)] = self.server_config
        config.saveserverconfig(all_cfg)

        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _clear_autorole(self, interaction: discord.Interaction):
        self.server_config.pop("autoroleid", None)
        all_cfg = config.loadserverconfig()
        all_cfg[str(self.guild.id)] = self.server_config
        config.saveserverconfig(all_cfg)

        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def _open_voicegate_modal(self, interaction: discord.Interaction):
        modal = VoiceGateRulesModal(parent_view=self)
        await interaction.response.send_modal(modal)

    async def _on_onlyimages_select(self, interaction: discord.Interaction):
        channel_id_str = str(interaction.data["values"][0])
        if channel_id_str in self.onlyimages:
            del self.onlyimages[channel_id_str]
        else:
            self.onlyimages[channel_id_str] = True
        config.save_onlyimages(self.onlyimages)

        await self.refresh_state()
        self._build_components()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Cog Registration
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
class SetupDashboard(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @slash_command(
        name="setup",
        description="Öffnet das interaktive Server-Setup Dashboard",
        guild_only=True,
        default_member_permissions=discord.Permissions(administrator=True)
    )
    @commands.has_permissions(administrator=True)
    async def setup_command(self, ctx: discord.ApplicationContext):
        view = DashboardView(self.bot, ctx.guild, ctx.author)
        embed = view.build_embed()
        await ctx.respond(embed=embed, view=view, ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(SetupDashboard(bot))
