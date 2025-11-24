import discord
from discord.ext import commands
import json
import os
import asyncio
from handlers.debug import LogDebug, LogError
from handlers.config import loadvoicegateconfig, savevoicegateconfig



class VoiceGate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pending_verifications = set()  
        self.voicegateconfig = loadvoicegateconfig()


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
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

            rules_text = config_data.get("rules_text", "No rules provided.")
            embed_rules = discord.Embed(
                title="Voice Gate Rules",
                description=rules_text,
                color=0x3498DB
            )
            embed_rules.set_footer(text="React with ✅ within 30 seconds to accept the rules.")

            try:
                dm_channel = await member.create_dm()
                rules_message = await dm_channel.send(embed=embed_rules)
                await rules_message.add_reaction("✅")
            except Exception as e:
                LogError(f"[VOICEGATE] Failed to send DM to member {member.id}: {e}")
                return

            def reaction_check(reaction, user):
                return (
                    user.id == member.id
                    and str(reaction.emoji) == "✅"
                    and reaction.message.id == rules_message.id
                )

            try:
                await self.bot.wait_for("reaction_add", timeout=30, check=reaction_check)
                final_channel = member.guild.get_channel(config_data.get("final_channel_id"))
                if final_channel is None:
                    try:
                        await member.send("Final channel not found. Please contact an administrator.")
                    except discord.Forbidden:
                        LogDebug(f"Could not send DM to {member.id} about missing final channel")
                    except Exception as e:
                        LogError(f"Failed to send channel missing DM to {member.id}: {str(e)}")
                    return
                await member.move_to(final_channel)
                await member.edit(mute=False)
                try:
                    await member.send("You have been moved to the final channel. Enjoy!")
                except discord.Forbidden:
                    LogDebug(f"Could not send success DM to {member.id} - DMs disabled")
                except Exception as e:
                    LogError(f"Failed to send success DM to {member.id}: {str(e)}")
            except asyncio.TimeoutError:
                try:
                    await member.move_to(None)
                    await member.send("You did not accept the rules in time. Please rejoin the voice channel to try again.")
                except Exception as dm_e:
                    LogError(f"[VOICEGATE] Failed to send DM after timeout to member {member.id}: {dm_e}")
        finally:
            self.pending_verifications.discard(member.id)

def setup(bot: commands.Bot):
    bot.add_cog(VoiceGate(bot))
