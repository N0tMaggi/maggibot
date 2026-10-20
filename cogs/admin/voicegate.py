# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import asyncio

from handlers.debug import LogDebug, LogError
from handlers.config import loadvoicegateconfig
from utils.embed_helpers import create_embed
from utils.colors import EmbedColors


class VoiceGateAcceptView(discord.ui.View):
    def __init__(self, member_id: int):
        super().__init__(timeout=45)
        self.member_id = member_id
        self.accepted = False

    @discord.ui.button(label="Regeln akzeptieren & Freischalten", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.member_id:
            await interaction.response.send_message("Diese Interaktion ist nicht für dich bestimmt.", ephemeral=True)
            return
        self.accepted = True
        button.disabled = True
        button.label = "Akzeptiert"
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

            rules_text = config_data.get("rules_text", "Keine spezifischen Regeln angegeben.")
            embed_rules = create_embed(
                title=f"🔊 {member.guild.name} • Voice Gate Regeln",
                description=rules_text,
                color=EmbedColors.INFO,
                footer_text="Klicke auf den Button innerhalb von 45 Sekunden."
            )

            view = VoiceGateAcceptView(member_id=member.id)
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
                        await member.send("Zielkanal nicht gefunden. Bitte kontaktiere einen Administrator.")
                    except Exception:
                        pass
                    return

                try:
                    await member.move_to(final_channel)
                    await member.edit(mute=False)
                    await member.send(f"✅ Du wurdest in **{final_channel.name}** verschoben. Viel Spaß!")
                except Exception as move_e:
                    LogError(f"[VOICEGATE] Error moving member {member.id}: {move_e}")
            else:
                try:
                    await member.move_to(None)
                    await member.send("⏳ Zeit abgelaufen. Bitte trete erneut bei und akzeptiere die Regeln.")
                except Exception as dm_e:
                    LogError(f"[VOICEGATE] Failed timeout kick/dm for member {member.id}: {dm_e}")
        finally:
            self.pending_verifications.discard(member.id)


def setup(bot: commands.Bot):
    bot.add_cog(VoiceGate(bot))
