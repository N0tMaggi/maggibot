import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import random

class Button(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        
    @slash_command(description="THE FORBIDDEN BUTTON")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def theforbiddenbutton(self, ctx):
        await ctx.respond("⚠️ **DO NOT PRESS THIS BUTTON! SOMETHING BAD WILL HAPPEN!!** ⚠️", view=TheForbiddenButton())
    
    @slash_command(description="Press the Good Boy button")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def goodboybutton(self, ctx):
        await ctx.respond("🌟 Press the button below to prove you're a good boy!", view=GoodBoyButton())
    
    @slash_command(description="Click here to see if you're a Top, Switch or Bottom. (or sub or dom)")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def topbottomswitch(self, ctx):
        await ctx.respond("🔮 **Click the button below to find out if you're a Top, Switch, or Bottom or Sub or Dom!** 🔮", view=TopBottomSwitchButton())

    @slash_command(description="Ollie")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def ollie(self, ctx):
        await ctx.respond("🛹 Click to ollie. <3", view=OllieButton())

    @slash_command(description="Thats Inter")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def inter(self, ctx):
        await ctx.respond("🔥 Click here to see Inters Secrets 🔥", view=InterButton())

    @slash_command(description="nom nom")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def nom(self, ctx):
        await ctx.respond(view=NomNomButton())

def setup(bot: discord.Bot):
    bot.add_cog(Button(bot))

class TheForbiddenButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.button(label="DO NOT PRESS!", style=discord.ButtonStyle.danger)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        user = interaction.user
        await interaction.followup.send(f"🚨 {user.mention} **JUST PRESSED THE FORBIDDEN BUTTON!** 🚨", ephemeral=False)

        if interaction.guild and interaction.guild.me.guild_permissions.moderate_members:
            try:
                await user.timeout(
                    until=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                    reason="Pressed the forbidden button!"
                )
                await interaction.followup.send(
                    f"⏳ {user.mention} has been **timed out for 1 hour**! Actions have consequences! 😈",
                    ephemeral=False
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ I couldn't timeout this user! Do they have higher permissions than me?",
                    ephemeral=False
                )
        else:
            await interaction.followup.send("❌ I don't have permission to timeout users!", ephemeral=True)

class GoodBoyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.pressed = False

    @discord.ui.button(label="Good Boy", style=discord.ButtonStyle.success)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.pressed:
            await interaction.response.send_message(
                f"⏳ {interaction.user.mention}, you're too late! The button can only be pressed once.",
                ephemeral=True
            )
            return

        self.pressed = True
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        if random.choice(["good", "bad"]) == "good":
            await interaction.edit_original_response(content=f"🌟 {interaction.user.mention} is a good boy! 🌟")
            await interaction.followup.send(
                f"🎉 {interaction.user.mention}, you redeemed yourself! You're a good boy now!",
                ephemeral=False
            )
        else:
            await interaction.edit_original_response(content=f"😈 {interaction.user.mention} was a bad boy! 😈")
            await interaction.followup.send(
                f"😢 {interaction.user.mention}, you were a bad boy!",
                ephemeral=False
            )

class TopBottomSwitchButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        roles = ["Top", "Bottom", "Switch", "DOM", "SUB"]
        await interaction.response.send_message(
            f"🎲 {interaction.user.mention}, you were assigned as a **{random.choice(roles)}**! 🌟",
            ephemeral=False
        )

class OllieButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Ollie", style=discord.ButtonStyle.primary)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        
        try:
            timeout_duration = datetime.timedelta(days=28)
            await interaction.user.timeout(
                until=datetime.datetime.utcnow() + timeout_duration,
                reason="Ollie Madness!"
            )
            await interaction.followup.send(
                f"🛹 {interaction.user.mention} **OLLIE'D STRAIGHT TO THE SHADOW REALM!** 🛹\n"
                f"⏳ Timed out for **28 days**!",
                ephemeral=False
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Couldn't timeout this absolute madlad! "
                "Do they have admin powers?",
                ephemeral=False
            )


class InterButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="EXPOSE", style=discord.ButtonStyle.primary)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if random.choice([True, False]):
            await interaction.response.send_message(
                f"🔥 {interaction.user.mention} ... **Inter HAS BEEN EXPOSED!** 🔥\n"
                "[Here](https://ag7-dev.de/fun/nsfw)",
                ephemeral=False
            )
        else:
            try:
                await interaction.user.timeout(
                    until=datetime.datetime.utcnow() + datetime.timedelta(hours=3),
                    reason="Exposed"
                )
                await interaction.response.send_message(
                    f"⏳ {interaction.user.mention} has been **timed out for 3 hours**! 😈\n"
                    "Just get the f out.",
                    ephemeral=False
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ I couldn't timeout this user! Do they have higher permissions than me?",
                    ephemeral=False
                )

class NomNomButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="nom", style=discord.ButtonStyle.primary)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("🍪 nom nom", ephemeral=False)