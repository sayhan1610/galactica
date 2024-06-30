import discord
import re
import json
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from akinator import (
    CantGoBackAnyFurther,
    InvalidAnswer,
    Akinator,
    Answer,
    Theme,
)
from bardapi import BardAsync
import configparser 
bot = commands.Bot(command_prefix="g.", intents=discord.Intents.all())
import os
from dotenv import load_dotenv
load_dotenv()

token = os.environ['bot_token']
BARD_TOKEN = os.environ['bard_token']
bard = BardAsync(token=BARD_TOKEN)
start_time = datetime.utcnow()

# Keep Alive
from keepalive import keep_alive

keep_alive()

# game uptime
current_time = datetime.utcnow()
uptime = current_time - start_time

    # Calculate hours and minutes for uptime
hours = uptime // timedelta(hours=1)
minutes = (uptime // timedelta(minutes=1)) % 60

# Bot
@bot.event
async def on_ready():
  server_id = 740830080451739659
  server = bot.get_guild(server_id)
  activity_text = f" over {server.member_count} explorers"
  activity = discord.Activity(type=discord.ActivityType.watching,
                              name=activity_text)
  await bot.change_presence(status=discord.Status.idle, activity=activity)
  print("Bot is up & ready!")
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
  except Exception as e:
    print(e)

  while True:
    sleep_timer = 600
    activity_text = " out for /help"
    activity = discord.Activity(type=discord.ActivityType.watching,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(sleep_timer)  # sleep for x seconds

    activity_text = f" over {server.member_count} explorers"
    activity = discord.Activity(type=discord.ActivityType.watching,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(sleep_timer)  # sleep for x seconds

    activity_text = "your confessions | /confess"
    activity = discord.Activity(type=discord.ActivityType.listening,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(sleep_timer)  # sleep for x seconds
    
    activity_text = f"for {hours} hours and {minutes} minutes"
    activity = discord.Activity(type=discord.ActivityType.playing,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(sleep_timer)  # sleep for x seconds





    

@bot.event
async def on_message(message):
    # DM Listener
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        # Copy the message and sender's name
        sender = message.author
        content = message.content
        channel_name = sender.name + "#" + sender.discriminator
        message_text = f"__`{channel_name}:`__ {content}"

        # DM the copied message to the bot owner
        owner = await bot.fetch_user(676367462270238730)
        await owner.send(message_text)

    await bot.process_commands(message)

# Help
@bot.tree.command(name="help", description="List all commands and their descriptions.")
async def help_command(interaction: discord.Interaction):
    commands_list = bot.tree.get_commands()
    help_text = ""

    for command in commands_list:
        help_text += f"**__/{command.name}__** - `{command.description}`\n"

    await interaction.response.send_message(help_text, ephemeral=True)


# Akinator
with open('akinator_avatar.png', 'rb') as file:
    avatar_bytes = file.read()
  
@bot.tree.command(name="akinator", description="Play the Akinator game. I'll try to guess who/what you are thinking of!")
@app_commands.choices(theme=[
    app_commands.Choice(name="Characters", value="characters"),
    app_commands.Choice(name="Objects", value="objects"),
  app_commands.Choice(name="Animals", value="animals"),
    ])
@app_commands.describe(
  theme="Choose from: Characters, Objects or Animals. (Set to Characters by default)")
async def akinator_game(interaction: discord.Interaction, theme: Optional[str] = "characters"):
    theme = theme.lower()
    
    if theme not in ["characters", "objects", "animals"]:
        await interaction.response.send_message("Invalid theme. Please choose from: Characters, Objects or Animals.", ephemeral=True)
        return
    
    theme = Theme.from_str(theme)
    
    await interaction.response.send_message("The game will begin shortly <a:star3d:1112469398402383992>. Respond with __`yes (y)`__, __`no (n)`__, __`probably`__, __`probably not`__, __`i don't know (idk)`__ or __`back`__.", ephemeral=True)
    aki = Akinator(child_mode=False, theme=theme)
    first_question = aki.start_game()

    def check(message):
        return message.author == interaction.user

    try:
        akchannel_id = interaction.channel_id
        channel = bot.get_channel(akchannel_id)
        webhook = await channel.create_webhook(name="Galactinator", avatar=avatar_bytes)
        await webhook.send(f'{first_question}')

        while aki.progression <= 80:
            answer = await bot.wait_for("message", check=check, timeout=60)
            answer = answer.content.lower()
            if answer == 'back':
                try:
                    aki.back()
                    await webhook.send(f"Went back 1 question! {aki.question}")
                except CantGoBackAnyFurther:
                    await webhook.send("Cannot go back any further!")
            else:
                try:
                    answer = Answer.from_str(answer)
                except InvalidAnswer:
                    await webhook.send("Invalid answer")
                else:
                    aki.answer(answer)
                    await webhook.send(f'{aki.question}')

        first_guess = aki.win()

        if first_guess:
            embed = discord.Embed()
            embed.set_author(name="Akinator Results")
            embed.title = first_guess.name
            embed.description = first_guess.description
            embed.color = random.randint(0, 0xFFFFFF)
            embed.set_thumbnail(url=first_guess.absolute_picture_path)
            await webhook.send(embed=embed)

        await webhook.delete()
    except asyncio.TimeoutError:
        await interaction.followup.send("Timeout: The game has ended.", ephemeral=True)
        await webhook.delete()



# Ping


@bot.tree.command(name="ping", description="Test the bot ping")
async def ping(interaction: discord.Interaction):
  # Send the initial response
  await interaction.response.send_message("Getting The Ping", delete_after=True, ephemeral=True)
  msg = await interaction.channel.send("https://cdn.discordapp.com/attachments/1086925161116225556/1099787877275148298/goku1.gif")

  # Wait for 2 seconds and send the next message
  await asyncio.sleep(2)
  await msg.edit(content="https://cdn.discordapp.com/attachments/1086925161116225556/1099787877564567672/goku2.gif")

  # Wait for 2 seconds and edit the previous message with the next one
  await asyncio.sleep(2)
  await msg.edit(content="https://cdn.discordapp.com/attachments/1086925161116225556/1099787877887516892/goku3.gif")

  # Wait for 2 seconds and edit the previous message with the next one
  await asyncio.sleep(2)
  await msg.edit(content="https://cdn.discordapp.com/attachments/1086925161116225556/1099787878202081403/goku4.gif")

  # Wait for 2 seconds and edit the previous message with the next one
  await asyncio.sleep(2)
  await msg.edit(content="https://cdn.discordapp.com/attachments/1086925161116225556/1099787878520868894/goku5.gif")

  # Measure the bot's ping and send the final message
  latency = bot.latency * 1000  # convert to milliseconds
  await asyncio.sleep(2)
  await msg.edit(
    content=
    f"The current ping is **{latency:.2f}** ms! <:jojos_tom:1071123688201662535>")

# Uptime

@bot.tree.command(name="uptime", description="Check how long the bot has been running for!")
async def uptime(interaction: discord.Interaction):
    current_time = datetime.utcnow()
    uptime = current_time - start_time

    # Calculate hours and minutes for uptime
    hours = uptime // timedelta(hours=1)
    minutes = (uptime // timedelta(minutes=1)) % 60

    # Format the bot start time as a Unix timestamp
    start_timestamp = int(start_time.timestamp())
    formatted_start_time = f"<t:{start_timestamp}>"

    await interaction.response.send_message(f"Bot has been up for {hours} h {minutes} m.\nBot started on {formatted_start_time}", ephemeral=True)

  


# Suggest QOTD
@bot.tree.command(name="suggest_qotd", description="Suggest a QOTD!")
async def suggest_qotd(interaction: discord.Interaction, question: str):
  channel = bot.get_channel(1095350025556594719)
  embed = discord.Embed(title="QOTD Suggestion",
                        description=f"**Question:** \n{question}")
  embed.set_footer(
    text=
    f"Suggested by {interaction.user.name}")
  embed.color = random.randint(0, 0xFFFFFF)
  await channel.send(embed=embed)
  await interaction.response.send_message(f"Suggestion sent to our staff!",
                                          ephemeral=True)


# Suggest SOTD
@bot.tree.command(name="suggest_sotd", description="Suggest SOTD!")
@app_commands.describe(
  song_name="The name of the song",
  artist_name="Name of the Artist(s)",
  link_1="Spotify/YouTube link to make navigation easier",
  link_2="An additional link to make navigation even easier (optional)",
  comment="Add a comment if you wish to (optional)")
async def suggest_sotd(interaction: discord.Interaction,
                       song_name: str,
                       artist_name: str,
                       link_1: str,
                       link_2: str = "",
                       comment: str = ""):
  # Check if link_1 and link_2 are valid links
  link_regex = re.compile(r'https?://\S+')
  if not link_regex.match(link_1):
    return await interaction.response.send_message(
      "Invalid link provided for Link 1. Mind using a real Spotify/YouTube link please?",
      ephemeral=True)
  if link_2 and not link_regex.match(link_2):
    return await interaction.response.send_message(
      "Invalid link provided for Link 2. Mind using a real Spotify/YouTube link please?",
      ephemeral=True)

  channel = bot.get_channel(800642003364347954)
  embed = discord.Embed(title="SOTD Suggestion")
  embed.add_field(name="Song Name", value=song_name, inline=True)
  embed.add_field(name="Artist(s) Name", value=artist_name, inline=True)
  embed.add_field(name="Link 1", value=link_1, inline=False)
  if link_2:
    embed.add_field(name="Link 2", value=link_2, inline=False)
  if comment:
    embed.add_field(name="Comment", value=comment, inline=False)
  embed.set_footer(
    text=
    f"Suggested by {interaction.user.name}")
  embed.color = random.randint(0, 0xFFFFFF)
  await channel.send(embed=embed)
  await interaction.response.send_message(f"Suggestion sent to our staff!",
                                          ephemeral=True)


# DM
@bot.tree.command(
    name="dm",
    description="Send a direct message to a mentioned user with a custom message"
)
@commands.is_owner()
@app_commands.describe(user="The user to send a message to",
                       message="The message to send to the user")
async def dm(interaction: discord.Interaction, user: discord.Member,
             message: str):
    authorized_user = [
        676367462270238730, 1071057018183499861, 738786980237934613,
        740509592701763604
    ]
    if interaction.user.id in authorized_user:
        try:
            # Replace "\\n" with "\n" in the message
            message = message.replace("\\n", "\n")

            # Logging the command usage
            log_channel_id = 1152550043333689454
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(
                    f"__`[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC]`__ - **{interaction.user.name}** used `/dm` in <#{interaction.channel_id}> to send a message to **{user.display_name}**\n__**Message:**__ {message}"
                )

            await user.send(message)
            await interaction.response.send_message(
                f"Sent a message to {user.display_name}! __**The following was sent**__: {message}",
                ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message(
                f"I couldn't send a message to {user.display_name}, they may have blocked me or disabled DMs",
                ephemeral=True)
    else:
        await interaction.response.send_message(
            f"I only listen to certain peeps for that command!", ephemeral=True)



# Say
@bot.tree.command(
  name="say",
  description="The bot won't listen unless you are cool, don't try XD")
@app_commands.describe(
  thing_to_say="Pray, tell me, my lord, what words should I utter?")
async def say(interaction: discord.Interaction, thing_to_say: str):
    # Replace "\n" with newline characters
    thing_to_say = thing_to_say.replace("\\n", "\n")
    
    await interaction.channel.send(thing_to_say)
    await interaction.response.send_message("Sent!", ephemeral=True)
    
    log_channel_id = 1152550043333689454
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        await log_channel.send(f"__`[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC]`__ - **{interaction.user.name}** used </say:1080898269951049769> in <#{interaction.channel_id}>")




# Shower thoughts
@bot.tree.command(
  name="shower_thoughts",
  description="If you love yourself, don't, just don't. I'm being serious!")
async def shower_thoughts(interaction: discord.Interaction):
    with open("shower_thoughts.json", "r") as file:
        shower_thoughts_data = json.load(file)
    
    bot_response = random.choice(shower_thoughts_data["quotes"])
    await interaction.response.send_message(bot_response)
    
    
# confess


@bot.tree.command(
    name="confess",
    description="Make an anonymous confession in #confessions. DMs are supported!"
)
@app_commands.describe(
    anonymous="You can opt to have your name appear in the confession if set to false. (True by default)"
)
@app_commands.describe(
    image="You can opt to add an image file. Videos and other formats are not supported."
)
async def confess(
    interaction: discord.Interaction,
    confession: str,
    image: discord.Attachment = None,  # Make the attachment optional by setting a default value of None
    anonymous: bool = True,  # Added an optional boolean input with a default value of True
):
    # Replace "\n" with newline characters
    confession = confession.replace("\\n", "\n")

    channel = bot.get_channel(1080435136614629436)

    if anonymous:
        embed = discord.Embed(title="Confession by Anonymous User", description=confession)
    else:
        user = interaction.user  # Get the user who initiated the command
        embed = discord.Embed(title=f"Confession by {user.display_name}", description=confession)

    embed.set_footer(
        text=f"Date and Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    embed.color = random.randint(0, 0xFFFFFF)

    # Check if an attachment was provided
    if image:
        embed.set_image(url=image.url)  # Add the attachment as an image to the embed

    await channel.send(embed=embed)
    await interaction.response.send_message(f"Sent to {channel.name}!", ephemeral=True)


bot.run(token)
