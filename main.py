import os
import datetime
import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests

# Put your variables here
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

DISCORD_CHANNEL_ID = 1442353889373589584
WELCOME_CHANNEL_ID = 1474271892692271268
suggestion_channel_id = 1502808778461024468
CREATOR_ROLE_ID = 1442353888639324217
STAFF_ROLE_ID = 1442353888639324211
VERIFY_ROLE_ID = 1528949759602331708
VERIFY_CHANNEL_ID = 1528938325400879125

last_video_id = None

intents=discord.Intents.default()
intents.message_content=True
intents.members=True
intents.presences=True

bot=commands.Bot(command_prefix="SF!",intents=intents)


@bot.event
async def on_ready():
    print("Bot is online")

    await bot.tree.sync()

    bot.add_view(VerifyButton())

    channel = bot.get_channel(1528938325400879125)

    if channel:
        embed = discord.Embed(
            title="✅ Verification",
            description="Press the button below to verify and become a verified member.",
            color=discord.Color.green()
        )

        await channel.send(
            embed=embed,
            view=VerifyButton()
        )


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    role = discord.utils.get(member.guild.roles,
    name="Subscriber")
    await member.add_roles(role)

    if channel:
        member_count = member.guild.member_count

        embed = discord.Embed(
            title="👋 Welcome to Spider Fire's Society!",
            description=(
                f"Welcome {member.mention}!\n\n"
                f"👥 You are member **#{member_count}** of the Society!"
            ),
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)

@bot.tree.command(name="announce", description="Send an announcement (Creator Only)")
async def announce(interaction: discord.Interaction, message: str):

    role = interaction.guild.get_role(CREATOR_ROLE_ID)

    if role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ You do not have permission to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    await interaction.channel.send(
        f"📢 **Spider Fire Announcement**\n\n{message}"
    )

    await interaction.followup.send(
        "✅ Announcement sent!",
        ephemeral=True
    )
   
@bot.tree.command(name="collab", description="Announce an upcoming collaboration video (Creator Only)")
async def collab(
    interaction: discord.Interaction,
    creator: str,
    video: str,
    date: str
):

    role = interaction.guild.get_role(CREATOR_ROLE_ID)

    if role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ You do not have permission to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="🎬 Upcoming Collaboration!",
        description=(
            f"Spider Fire is teaming up with **{creator}**!\n\n"
            f"🎥 **Video:** {video}\n"
            f"📅 **Release Date:** {date}\n\n"
            "Make sure to stay tuned!"
        ),
        color=discord.Color.red()
    )

    embed.set_footer(text="Spider Fire | YouTube")

    await interaction.channel.send(embed=embed)

    await interaction.followup.send(
        "✅ Collaboration announcement posted!",
        ephemeral=True
    )
@bot.tree.command(name="kick", description="Kick a member")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):

    await member.kick(reason=reason)

    await interaction.response.send_message(
        f"👢 {member.mention} has been kicked.\n**Reason:** {reason}"
    )


@bot.tree.command(name="ban", description="Ban a member")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):

    await member.ban(reason=reason)

    await interaction.response.send_message(
        f"🔨 {member.mention} has been banned.\n**Reason:** {reason}"
    )


@bot.tree.command(name="unban", description="Unban a member")
async def unban(interaction: discord.Interaction, user_id: str):

    user = await bot.fetch_user(int(user_id))

    await interaction.guild.unban(user)

    await interaction.response.send_message(
        f"✅ {user} has been unbanned."
    )



@bot.tree.command(name="purge", description="Delete messages")
async def purge(interaction: discord.Interaction, amount: int):

    await interaction.response.defer(ephemeral=True)

    deleted = await interaction.channel.purge(limit=amount)

    await interaction.followup.send(
        f"🧹 Deleted {len(deleted)} messages.",
        ephemeral=True
    )


@bot.tree.command(name="lock", description="Lock the current channel")
async def lock(interaction: discord.Interaction):

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        send_messages=False
    )

    await interaction.response.send_message(
        "🔒 Channel locked."
    )


@bot.tree.command(name="unlock", description="Unlock the current channel")
async def unlock(interaction: discord.Interaction):

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        send_messages=True
    )

    await interaction.response.send_message(
        "🔓 Channel unlocked."
    )


@bot.tree.command(name="slowmode", description="Set channel slowmode")
async def slowmode(interaction: discord.Interaction, seconds: int):

    await interaction.channel.edit(
        slowmode_delay=seconds
    )

    await interaction.response.send_message(
        f"🐌 Slowmode set to {seconds} seconds."
    )
warnings = {}

@bot.tree.command(name="warn", description="Warn a member")
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str
):

    user_id = member.id

    if user_id not in warnings:
        warnings[user_id] = []

    warnings[user_id].append({
        "reason": reason,
        "staff": interaction.user.name
    })

    await interaction.response.send_message(
        f"⚠️ {member.mention} has been warned.\n"
        f"**Reason:** {reason}\n"
        f"**Moderator:** {interaction.user.mention}"
    )
@bot.tree.command(name="say", description="Make the bot say a message")
@app_commands.describe(message="The message you want the bot to send")
async def say(interaction: discord.Interaction, message: str):

    staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

    # Check if user has staff role
    if staff_role not in interaction.user.roles:
        await interaction.response.send_message(
            "❌ You do not have permission to use this command.",
            ephemeral=True
        )
        return

    # Confirm to staff member privately
    await interaction.response.send_message(
        "✅ Message sent.",
        ephemeral=True
    )

    # Send the message publicly
    await interaction.channel.send(message)

@bot.tree.command(name="videoidea", description="Suggest a video idea for the YouTube channel")
async def videoidea(interaction: discord.Interaction, idea: str):
    
    
    channel = bot.get_channel(suggestion_channel_id)

    embed = discord.Embed(
        title="🎥 New Video Idea Suggestion",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Idea",
        value=idea,
        inline=False
    )
    embed.add_field(
        name="Suggested By",
        value=interaction.user.mention,
        inline=False
    )
    embed.set_footer(text="Spider Fire Video Ideas")

    await channel.send(embed=embed)

    await interaction.response.send_message(
        "✅ Your video idea has been submitted!",
        ephemeral=True
    )


class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.green,
        custom_id="verify_button"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(VERIFY_ROLE_ID)

        if role is None:
            await interaction.response.send_message(
                "❌ Verification role not found.",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "✅ You are already verified!",
                ephemeral=True
            )
            return

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            "✅ You have been verified!",
            ephemeral=True
        )
bot.run(DISCORD_TOKEN)
