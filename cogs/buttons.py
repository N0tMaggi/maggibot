import discord
from discord.ext import commands
from discord.commands import slash_command
import datetime
import random

class Button(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        
    @slash_command(description="THE FORBIDDEN BUTTON")
    async def theforbiddenbutton(self, ctx):
        await ctx.respond("⚠️ **DO NOT PRESS THIS BUTTON! SOMETHING BAD WILL HAPPEN!!** ⚠️", view=TheForbiddenButton())
    
    @slash_command(description="Press the Good Boy button")
    async def goodboybutton(self, ctx):
        """Sendet den Good Boy Button."""
        await ctx.respond("🌟 Press the button below to prove you're a good boy!", view=GoodBoyButton())
    
    @slash_command(description="Click here to see if you're a Top, Switch or Bottom.")
    async def topbottomswitch(self, ctx):
        """Sendet den Button, der die Rolle (Top, Bottom oder Switch) zuweist."""
        await ctx.respond("🔮 **Click the button below to find out if you're a Top, Switch, or Bottom!** 🔮", view=TopBottomSwitchButton())

        
def setup(bot: discord.Bot):
    bot.add_cog(Button(bot))

# **The Forbidden Button** - Timeout Mechanism
class TheForbiddenButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="DO NOT PRESS!", style=discord.ButtonStyle.danger)
    async def button1(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        await interaction.response.send_message(f"🚨 {user.mention} **JUST PRESSED THE FORBIDDEN BUTTON!** 🚨", ephemeral=False)

        if not guild.me.guild_permissions.moderate_members:
            await interaction.followup.send("❌ I don't have permission to timeout users!", ephemeral=True)
            return

        try:
            # Timeout für 1 Stunde erstellen
            timeout_until = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            await user.timeout(until=timeout_until, reason="Pressed the forbidden button!")
            await interaction.followup.send(f"⏳ {user.mention} has been **timed out for 1 hour**! Actions have consequences! 😈", ephemeral=False)
        except discord.Forbidden:
            await interaction.followup.send("❌ I couldn't timeout this user! Do they have higher permissions than me?", ephemeral=False)

# **Good Boy Button** - Prove You're a Good Boy
class GoodBoyButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.has_been_pressed = False  # Flag, um zu überwachen, ob der Button bereits gedrückt wurde

    @discord.ui.button(label="Good Boy", style=discord.ButtonStyle.success)
    async def button2(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user
        
        if self.has_been_pressed:
            # Wenn der Button bereits gedrückt wurde, zeige eine Nachricht an, dass es zu spät ist
            await interaction.response.send_message(f"⏳ {user.mention}, you're too late! The button can only be pressed once.", ephemeral=True)
        else:
            # Button wird deaktiviert, nachdem er gedrückt wurde
            self.has_been_pressed = True
            await interaction.response.edit_message(content=f"🌟 {user.mention} is a good boy! 🌟", view=self)

            # Nachricht, die nach dem Drücken des Buttons gesendet wird
            await interaction.followup.send(f"🎉 {user.mention}, you redeemed yourself! You're a good boy now!", ephemeral=False)

# **Top, Bottom, Switch Role Assignment Button**
class TopBottomSwitchButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary)
    async def button1(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user
        
        # Zufällig eine Rolle auswählen
        roles = ["Top", "Bottom", "Switch", "DOM", "SUB"]
        assigned_role = random.choice(roles)
        
        # Antwort senden
        await interaction.response.send_message(f"🎲 {user.mention}, you were assigned as a **{assigned_role}**! 🌟", ephemeral=False)