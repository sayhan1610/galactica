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
import requests

token = os.environ['bot_token']
BARD_TOKEN = os.environ['bard_token']
bard = BardAsync(token=BARD_TOKEN)
start_time = datetime.utcnow()

# Keep Alive
from keepalive import keep_alive

keep_alive()

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
    # game uptime
    current_time = datetime.utcnow()
    uptime = current_time - start_time

    # Calculate hours and minutes for uptime
    hours = uptime // timedelta(hours=1)
    minutes = (uptime // timedelta(minutes=1)) % 60
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

# MatchMyTaste
BASE_URL = "https://matchmytaste.onrender.com"

@bot.tree.command(name="matchmytaste", description="Find artists/tracks similar to one provided by you or get the top 20 tracks on Spotify for this month")
@app_commands.describe(artist="The artist name", track="The track name")
async def matchmytaste(interaction: discord.Interaction, artist: str = None, track: str = None):
    try:
        if artist:
            results = search_artist(artist)
            result_type = "Artists"
        elif track:
            results = search_track(track)
            result_type = "Tracks"
        else:
            results = top_tracks_of_month()
            result_type = "Top Tracks of the Month"

        # Randomly pick 10 results if there are more than 10
        if len(results) > 10:
            results = random.sample(results, 10)

        embed = discord.Embed(title=f"{result_type} Similar to Your Input", color=random.randint(0, 0xFFFFFF))
        for result in results:
            if result_type == "Artists":
                embed.add_field(name=result['name'], value=f"[Link]({result['url']})", inline=False)
            else:
                embed.add_field(name=result['name'], value=f"{result['artists']} - [Link]({result['url']})", inline=False)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

def search_artist(query):
    url = f"{BASE_URL}/search_artist"
    payload = {"query": query}
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def search_track(query):
    url = f"{BASE_URL}/search_track"
    payload = {"query": query}
    headers = {"accept": "application/json", "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def top_tracks_of_month():
    url = f"{BASE_URL}/top_tracks_of_month"
    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    return response.json()









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
