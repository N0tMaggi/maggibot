import discord
from discord.ext import commands
import json
import os
import handlers.debug as DH

voicegateconfigfile = "config/voicegateconfig.json"

def loadvoicegateconfig():
    if not os.path.exists(voicegateconfigfile):
        try:
            os.makedirs(os.path.dirname(voicegateconfigfile), exist_ok=True)
        except Exception as e:
            raise Exception(f"Error creating config directory: {e}")
        try:
            with open(voicegateconfigfile, 'w') as f:
                json.dump({}, f, indent=4)
        except Exception as e:
            raise Exception(f"Error creating config file: {e}")
    try:
        with open(voicegateconfigfile, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise Exception(f"Error loading voice gate config: {e}")

def savevoicegateconfig(config):
    if not os.path.exists(voicegateconfigfile):
        try:
            os.makedirs(os.path.dirname(voicegateconfigfile), exist_ok=True)
        except Exception as e:
            raise Exception(f"Error creating config directory: {e}")
    try:
        with open(voicegateconfigfile, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        raise Exception(f"An error occurred while saving voice gate config: {e}")

async def safe_respond(ctx: discord.ApplicationContext, embed: discord.Embed):
    try:
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception:
        await ctx.followup.send(embed=embed, ephemeral=True)

class VoiceGate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pending_verifications = set()  
        try:
            self.config = loadvoicegateconfig()
        except Exception as e:
            DH.LogError(f"Error initializing voice gate config: {e}")
            self.config = {}

    @commands.slash_command(name="setup-voicegate", description="Set up a voice gate channel for this server")
    @commands.has_permissions(administrator=True)
    async def setup_voicegate(
        self, 
        ctx: discord.ApplicationContext, 
        gate_channel: discord.VoiceChannel, 
        final_channel: discord.VoiceChannel, 
        need_accept_rules: bool
    ):
        try:
            rules_text = ""
            if need_accept_rules:
                embed_prompt = discord.Embed(
                    title="Voice Gate Setup",
                    description="Please enter the rules text within 30 seconds.",
                    color=0x3498DB
                )
                await safe_respond(ctx, embed_prompt)

                def check(message: discord.Message):
                    return message.author == ctx.author and message.channel == ctx.channel

                try:
                    msg = await self.bot.wait_for('message', timeout=30, check=check)
                    rules_text = msg.content
                except Exception:
                    raise Exception("Timeout: You did not provide the required text in time.")

            self.config[str(ctx.guild.id)] = {
                "gate_channel_id": gate_channel.id,
                "final_channel_id": final_channel.id,
                "need_accept_rules": need_accept_rules,
                "rules_text": rules_text
            }
            savevoicegateconfig(self.config)

            embed_success = discord.Embed(
                title="Success",
                description="Voice gate has been successfully set up.",
                color=0x2ECC71
            )
            await safe_respond(ctx, embed_success)

        except Exception as e:
            raise Exception(f"Error in setup_voicegate command: {e}")

    @commands.slash_command(name="setup-showvoicegatesettings", description="Show the current voice gate settings for this server")
    @commands.has_permissions(administrator=True)
    async def setup_showvoicegatesettings(self, ctx: discord.ApplicationContext):
        try:
            if str(ctx.guild.id) not in self.config:
                raise Exception("No voice gate configuration found for this server.")
            config_data = self.config[str(ctx.guild.id)]
            embed_settings = discord.Embed(
                title="Voice Gate Settings",
                color=0x3498DB
            )
            for key, value in config_data.items():
                embed_settings.add_field(name=key, value=str(value), inline=False)
            await safe_respond(ctx, embed_settings)
        except Exception as e:
            raise Exception(f"Error in setup-showvoicegatesettings command: {e}")

    @commands.slash_command(name="setup-deletevoicegate", description="Delete the voice gate configuration for the given voice channel")
    @commands.has_permissions(administrator=True)
    async def setup_deletevoicegate(self, ctx: discord.ApplicationContext, gate_channel: discord.VoiceChannel):
        try:
            if str(ctx.guild.id) not in self.config:
                raise Exception("No voice gate configuration found for this server.")
            config_data = self.config[str(ctx.guild.id)]
            if config_data.get("gate_channel_id") != gate_channel.id:
                raise Exception("The provided voice channel does not match the stored configuration.")
            del self.config[str(ctx.guild.id)]
            savevoicegateconfig(self.config)
            embed_success = discord.Embed(
                title="Success",
                description="Voice gate configuration has been deleted.",
                color=0x2ECC71
            )
            await safe_respond(ctx, embed_success)
        except Exception as e:
            raise Exception(f"[VOICEGATE] Error in setup-deletevoicegate command: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        config_data = self.config.get(str(member.guild.id))
        if not config_data:
            return

        gate_channel_id = config_data.get("gate_channel_id")

        if before.channel and before.channel.id == gate_channel_id:
            if not after.channel or after.channel.id != gate_channel_id:
                try:
                    await member.edit(mute=False)
                except Exception as e:
                    DH.LogError(f"[VOICEGATE] Failed to unmute member {member.id} after leaving gate channel: {e}")
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
                DH.LogError(f"[VOICEGATE] Failed to mute member {member.id}: {e}")

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
                DH.LogError(f"[VOICEGATE] Failed to send DM to member {member.id}: {e}")
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
                    except Exception:
                        pass
                    return
                await member.move_to(final_channel)
                await member.edit(mute=False)
                try:
                    await member.send("You have been moved to the final channel. Enjoy!")
                except Exception:
                    pass
            except Exception:
                try:
                    await member.move_to(None)
                    await member.send("You did not accept the rules in time. Please rejoin the voice channel to try again.")
                except Exception as dm_e:
                    DH.LogError(f"[VOICEGATE] Failed to send DM after timeout to member {member.id}: {dm_e}")
        finally:
            self.pending_verifications.discard(member.id)

def setup(bot: commands.Bot):
    bot.add_cog(VoiceGate(bot))
