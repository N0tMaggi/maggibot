import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
from extensions.modextensions import create_mod_embed
from handlers.debug import LogDebug, LogError


RULES = [
    {
        "name": "🤖 - (Maggi) Bot-Token Filter",
        "trigger_type": discord.AutoModTriggerType.keyword,
        "metadata": discord.AutoModTriggerMetadata(
            regex_patterns=[r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,}"]
        ),
        "actions": [discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata())],
    },
    {
        "name": "👤 - (Maggi) Private Details Filter (Telefonnummer)",
        "trigger_type": discord.AutoModTriggerType.keyword,
        "metadata": discord.AutoModTriggerMetadata(
            regex_patterns=[r"^[\+]?[(]?[0-9]{3}[)]?[-\s\. ]?[0-9]{3}[-\s\. ]?[0-9]{4,6}$"]
        ),
        "actions": [discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata())],
    },
    {
        "name": "🌎 - (Maggi) Discord Werbung Filter",
        "trigger_type": discord.AutoModTriggerType.keyword,
        "metadata": discord.AutoModTriggerMetadata(
            regex_patterns=[r"(?:(?:https?://)?(?:www)?discord(?:app)?\.(?:(?:com|gg)/invite/[a-z0-9-_]+)|(?:https?://)?(?:www)?discord\.gg/[a-z0-9-_]+)"]
        ),
        "actions": [
            discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata()),
            discord.AutoModAction(
                discord.AutoModActionType.timeout,
                discord.AutoModActionMetadata(timeout_duration=datetime.timedelta(minutes=10))
            )
        ],
    },
    {
        "name": "🔗 - (Maggi) Link-Filter (mit IP)",
        "trigger_type": discord.AutoModTriggerType.keyword,
        "metadata": discord.AutoModTriggerMetadata(
            regex_patterns=[
                r"(?:https?:\/\/)?[a-z0-9_\-\.]{2,}\.(com|de|net|org|info|io|tv|tk|dev|xyz)\b",
                r"^((25[0-5]|2[0-4]|1\d|[1-9]|\d)\.?\b){4}$"
            ],
            allow_list=[
                "amazon.com", "amazon.de", "bl4cklist.de", "cdn.discordapp.com",
                "clank.dev", "codenames.game", "discord-join.xyz", "discord.com",
                "discord.com/channels", "discord.ext", "discord.gg",
                "discord.gg/bl4cklist", "discord.js", "discord.js.org", "discord.new",
                "discord.py", "gamepro.de", "gamestar.de", "garticphone.com",
                "github.com", "guess-the-price.de", "guesstheprice.de",
                "guesstherank.org", "gutefrage.net", "higherlowergame.com",
                "imgur.com", "instagram.com", "kahoot.it", "kick.com", "lenovo.com",
                "media.discordapp.net", "paint.net", "readthedocs.io", "skribbl.io",
                "songtrivia2.io", "soundcloud.com", "spotify.com", "stackoverflow.com",
                "stadtlandfluss.cool", "tagesschau.de", "telefonseelsorge.de",
                "tenor.com", "tiktok.com", "twitch.tv", "twitter.com",
                "w3schools.com", "wheelofnames.com", "wikipedia.org",
                "wikispeedruns.com", "youtu.be", "youtube.com"
            ]
        ),
        "actions": [discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata())],
    },
    {
        "name": "👿 - (Maggi) Unsere Beleidigungsliste",
        "trigger_type": discord.AutoModTriggerType.keyword,
        "metadata": discord.AutoModTriggerMetadata(
            keyword_filter=[
                "*/adverts*", "*/hbf*", "*/hood*", "*/jugendtreff*", "*/zmdc*",
                "*bastard*", "*crypto market*", "*daddy*", "ddns.net", "die fresse",
                "diktatur", "*drogen*", "*fehlgeburt*", "*fettsack*", "*fick*",
                "*fotze*", "hanf", "hdf", "*hitler*", "hoe", "*horensohn*",
                "*huan*", "*huansohn*", "*hundesohn*", "hure", "huren", "*hurensohn*",
                "*hurens\u00f6hn*", "*huso*", "*kanacke*", "*kanake*", "*kiffe*", "*knecht*",
                "*misgeburt*", "*missgeburt*", "*mistgeburt*", "*muschi*", "*nazi*",
                "*neger*", "*negger*", "*newcoverresellingv2*", "niga", "niger*",
                "*nigga*", "*nigger*", "*nutte*", "*nuttensohn*", "opfer*", "*pädo*",
                "*pedo*", "*penis*", "*pussy*", "*retard*", "ritzen", "*schlampe*",
                "*schwanz*", "*schwuchtel*", "*shadowleaks*", "spast*", "stfu",
                "*wichs*", "*wix*"
            ]
        ),
        "actions": [discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata())],
    },
    {
        "name": "😡 - (Maggi) Discord's Beleidigungsliste",
        "trigger_type": discord.AutoModTriggerType.keyword_preset,
        "metadata": discord.AutoModTriggerMetadata(
            presets=[
                discord.AutoModKeywordPresetType.profanity,
                discord.AutoModKeywordPresetType.sexual_content,
                discord.AutoModKeywordPresetType.slurs
            ]
        ),
        "actions": [discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata())],
    },
    {
        "name": "💬 - (Maggi) Spam-Inhalt blockieren",
        "trigger_type": discord.AutoModTriggerType.spam,
        "metadata": discord.AutoModTriggerMetadata(),
        "actions": [discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata())],
    },
    {
        "name": "(Maggi) Block Mention Spam",
        "trigger_type": discord.AutoModTriggerType.mention_spam,
        "metadata": discord.AutoModTriggerMetadata(mention_total_limit=20),
        "actions": [discord.AutoModAction(discord.AutoModActionType.block_message, discord.AutoModActionMetadata())],
    }
]


class Automod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command(name="setup-automod", description="Setup Maggi automod rules")
    @commands.has_permissions(administrator=True)
    async def setup_automod(self, ctx: discord.ApplicationContext):
        class AutomodSetupView(discord.ui.View):
            def __init__(self, author):
                super().__init__(timeout=60)
                self.author = author
                self.value = None

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user == self.author

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)

            @discord.ui.button(label="Start", style=discord.ButtonStyle.success)
            async def start_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = True
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
            async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.value = False
                self.stop()

        view = AutomodSetupView(ctx.author)
        embed = create_mod_embed(
            "🛡️ Automod Setup Confirmation",
            "Are you sure you want to set up the automod rules?",
            'info',
            ctx.author
        )
        message = await ctx.respond(embed=embed, view=view, ephemeral=True)
        view.message = message

        await view.wait()

        if view.value is None:
            await message.edit_original_response(content="Timed out.", view=None)
            return
        if not view.value:
            await message.edit_original_response(content="Cancelled.", view=None)
            return

        for item in view.children:
            item.disabled = True
        await message.edit_original_response(view=view)

        working_embed = create_mod_embed(
            "🛡️ Automod Setup",
            "Working on it...",
            'info',
            ctx.author
        )
        await message.edit_original_response(embed=working_embed)

        guild = ctx.guild
        created = []
        skipped = []
        try:
            existing_rules = await guild.fetch_auto_moderation_rules()
            existing_names = [r.name for r in existing_rules]

            for rule in RULES:
                if rule["name"] in existing_names:
                    skipped.append(rule["name"])
                    continue
                try:
                    await guild.create_auto_moderation_rule(
                        name=rule["name"],
                        event_type=discord.AutoModEventType.message_send,
                        trigger_type=rule["trigger_type"],
                        trigger_metadata=rule["metadata"],
                        actions=rule["actions"],
                        exempt_roles=rule.get("exempt_roles"),
                        exempt_channels=rule.get("exempt_channels"),
                        enabled=True
                    )
                    created.append(rule["name"])
                except Exception as e:
                    LogError(f"Failed to create rule {rule['name']}: {e}")
                    skipped.append(rule["name"])

            description_parts = []
            if created:
                description_parts.append("**Created Rules:**\n" + "\n".join(f"• {n}" for n in created))
            if skipped:
                description_parts.append("**Skipped Rules:**\n" + "\n".join(f"• {n}" for n in skipped))
            if not description_parts:
                description_parts.append("No changes were made.")

            embed = create_mod_embed(
                "🛡️ Automod Setup",
                "\n\n".join(description_parts),
                'success' if created else 'info',
                ctx.author
            )
            await message.edit_original_response(embed=embed)
            LogDebug(f"Automod setup finished in guild {guild.id}")
        except Exception as e:
            LogError(f"Automod setup error: {e}")
            error_embed = create_mod_embed(
                "❌ Automod Setup Failed",
                f"An error occurred while creating automod rules: {e}",
                'error',
                ctx.author
            )
            await message.edit_original_response(embed=error_embed)


def setup(bot: commands.Bot):
    bot.add_cog(Automod(bot))
