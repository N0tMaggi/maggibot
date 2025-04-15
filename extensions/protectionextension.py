import discord
import datetime
import handlers.config as cfg
from handlers.debug import LogDebug, LogError, LogModeration


async def create_antibot_protection_embed(self, ctx, member, inviter, is_verified=True, action_taken=True):
    color = discord.Color.green() if is_verified else discord.Color.red()
    status = "Verified" if is_verified else "Unverified"
    action = "Allowed" if is_verified else "Kicked" if action_taken else "Not Kicked"
    emoji = "✅" if is_verified else "🛑" if action_taken else "⚠️"
    
    embed = discord.Embed(
        title=f"{emoji} {status} Bot Detection",
        color=color,
        timestamp=datetime.datetime.utcnow()
    )
    
    embed.add_field(name="Bot Account", value=f"{member.mention}\n{member.name}#{member.discriminator}", inline=False)
    embed.add_field(name="Bot ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
    
    if inviter:
        embed.add_field(name="Invited By", value=f"{inviter.mention}\n({inviter.name}#{inviter.discriminator})", inline=False)
    
    embed.set_author(name=member.guild.name, icon_url=member.guild.icon.url)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    if is_verified:
        embed.description = f"A **verified bot** was added to the server and has been allowed."
    else:
        if action_taken:
            embed.description = f"An **unverified bot** was detected and immediately kicked."
        else:
            embed.description = f"⚠️ Failed to kick unverified bot! Please check permissions."
    
    embed.set_footer(text=f"Protection System • Action: {action}", icon_url=self.bot.user.display_avatar.url)
    
    return embed

async def create_alert_embed(self, message, mention_count):
    embed = discord.Embed(
        title=f"🚨 Mass Mention Detected ({mention_count} mentions)",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    
    embed.set_author(name=str(message.author), 
                     icon_url=message.author.display_avatar.url)
    embed.add_field(name="👤 User", 
                   value=f"{message.author.mention}\n{message.author.id}", 
                   inline=True)
    embed.add_field(name="📅 Account Created", 
                   value=f"<t:{int(message.author.created_at.timestamp())}:R>", 
                   inline=True)
    
    content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content
    embed.add_field(name="📝 Message Content", 
                   value=f"```{content}```" if content else "*No text content*", 
                   inline=False)
    embed.add_field(name="📌 Message ID", 
                   value=f"`{message.id}`", 
                   inline=True)
    embed.add_field(name="🔗 Channel", 
                   value=f"{message.channel.mention}\n({message.channel.id})", 
                   inline=True)
    
    embed.set_footer(text=f"{message.guild.name} • Anti-Spam Protection", 
                    icon_url=message.guild.icon.url)
    
    return embed



async def create_protection_config_embed(self, ctx, title, description, color, fields=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.utcnow()
    )
    
    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    
    embed.add_field(name="🛡️ Action Performed By", 
                   value=f"{ctx.author.mention}\n{ctx.author.name}#{ctx.author.discriminator}",
                   inline=True)
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    embed.set_footer(text=f"Server ID: {ctx.guild.id} | Protection System")
    
    return embed