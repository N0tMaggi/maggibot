# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import asyncio

from handlers.debug import LogDebug, LogError
from handlers.config import loadvoicegateconfig
from handlers.locale import t
from utils.embed_helpers import create_embed
from utils.colors import EmbedColors


class VoiceGateAcceptView(discord.ui.View):
    def __init__(self, member_id: int, guild_id: int):
        super().__init__(timeout=45)
        self.member_id = member_id
        self.guild_id = guild_id
        self.accepted = False
        self.accept_button.label = t("voicegate.accept_button", guild_id=guild_id)

    @discord.ui.button(label="Accept Rules & Unlock", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.member_id:
            await interaction.response.send_message(t("voicegate.wrong_user", guild_id=self.guild_id), ephemeral=True)
            return
        self.accepted = True
        button.disabled = True
        button.label = t("voicegate.accepted", guild_id=self.guild_id)
        await interaction.response.edit_message(view=self)
        self.stop()


class VoiceGate(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.pending_verifications = set()
        self.voicegateconfig = loadvoicegateconfig()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        self.voicegateconfig = loadvoicegateconfig()
        config_data = self.voicegateconfig.get(str(member.guild.id))
        if not config_data:
            return

        gate_channel_id = config_data.get("gate_channel_id")

        if before.channel and before.channel.id == gate_channel_id:
            if not after.channel or after.channel.id != gate_channel_id:
                try:
                    await member.edit(mute=False)
                except Exception as e:
                    LogError(f"[VOICEGATE] Failed to unmute member {member.id} after leaving gate channel: {e}")
                self.pending_verifications.discard(member.id)
                return

        if not after.channel or (before.channel and before.channel.id == after.channel.id):
            return

        if after.channel.id != gate_channel_id:
            return

        if member.id in self.pending_verifications:
            return

        self.pending_verifications.add(member.id)

        try:
            try:
                await member.edit(mute=True)
            except Exception as e:
                LogError(f"[VOICEGATE] Failed to mute member {member.id}: {e}")

            rules_text = config_data.get("rules_text") or t("general.no_description", guild_id=member.guild.id)
            embed_rules = create_embed(
                title=f"🔊 {t('voicegate.embed_title', guild_id=member.guild.id, guild_name=member.guild.name)}",
                description=rules_text,
                color=EmbedColors.INFO,
                footer_text=t("voicegate.footer", guild_id=member.guild.id)
            )

            view = VoiceGateAcceptView(member_id=member.id, guild_id=member.guild.id)
            try:
                dm_channel = await member.create_dm()
                rules_message = await dm_channel.send(embed=embed_rules, view=view)
            except Exception as e:
                LogError(f"[VOICEGATE] Failed to send DM to member {member.id}: {e}")
                return

            await view.wait()

            if view.accepted:
                final_channel_id = config_data.get("final_channel_id")
                final_channel = member.guild.get_channel(final_channel_id)
                if final_channel is None:
                    try:
                        await member.send(t("voicegate.no_target", guild_id=member.guild.id))
                    except Exception:
                        pass
                    return

                try:
                    await member.move_to(final_channel)
                    await member.edit(mute=False)
                    await member.send(t("voicegate.moved", guild_id=member.guild.id, channel=final_channel.name))
                except Exception as move_e:
                    LogError(f"[VOICEGATE] Error moving member {member.id}: {move_e}")
            else:
                try:
                    await member.move_to(None)
                    await member.send(t("voicegate.timeout", guild_id=member.guild.id))
                except Exception as dm_e:
                    LogError(f"[VOICEGATE] Failed timeout kick/dm for member {member.id}: {dm_e}")
        finally:
            self.pending_verifications.discard(member.id)


def setup(bot: commands.Bot):
    bot.add_cog(VoiceGate(bot))
