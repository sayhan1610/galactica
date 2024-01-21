import discord
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
    activity_text = " out for /help"
    activity = discord.Activity(type=discord.ActivityType.watching,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(30)  # sleep for 30 seconds

    activity_text = f" over {server.member_count} explorers"
    activity = discord.Activity(type=discord.ActivityType.watching,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(30)  # sleep for 30 seconds

    activity_text = "your confessions"
    activity = discord.Activity(type=discord.ActivityType.listening,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(30)  # sleep for 30 seconds

    activity_text = "Galaxy's Summer Chess Tournament"
    activity = discord.Activity(type=discord.ActivityType.competing,
                                name=activity_text)
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    await asyncio.sleep(30)  # sleep for 30 seconds




# Bard
@bot.tree.command(name="reset", description="Reset chat context")
async def reset(interaction: discord.Interaction):
    await interaction.response.defer()
    global bard
    bard = BardAsync(token=BARD_TOKEN)
    await interaction.followup.send("Chat context successfully reset.")
    return
    
@bot.tree.command(name="ask", description="AI Chatbot Powered by Google's Bard")
async def ask(interaction: discord.Interaction, prompt: str, image: discord.Attachment = None):
    await interaction.response.defer()
    if image is not None:
        if not image.content_type.startswith('image/'):
            await interaction.response.send_message("File must be an image")
            return
        response = await bard.ask_about_image(prompt, await image.read())
        if len(response['content']) > 2000:
            embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(response['content'])
            return
    response = await generate_response(prompt) 
    if len(response['content']) > 2000:
        embed = discord.Embed(title="Response", description=response['content'], color=0xf1c40f)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(response['content'])
    return

async def generate_response(prompt):
    response = await bard.get_answer(prompt)
    if not "Unable to get response." in response["content"]:
        config = read_config()
        if config.getboolean("SETTINGS", "use_images"):
            images = response["images"]
            if images:
                for image in images:
                    response["content"] += f"\n{image}"
        return response
    


    
def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config

def write_config(config):
    with open("config.ini", "w") as configfile:
        config.write(configfile)

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

  

# Shower Thought
@bot.tree.command(
  name="shower_thoughts",
  description="If you love yourself, don't, just don't. I'm being serious!")
async def shower_thoughts(interaction: discord.Interaction):
  thought = [
    "*Go to bed, you'll feel better in the morning\" is the human version of \"Did you turn it off and turn it back on again?*",
    "*Maybe plants are really farming us, giving us oxygen until we eventually expire and turn into mulch which they can consume*",
    "*Theme parks can snap a crystal clear picture of you on a roller coaster at 70 mph, but bank cameras can't get a clear shot of a robber standing still.*",
    "*If your calculator had a history, it would be more embarrassing than your browser history.*",
    "*Lawyers hope you get sued, doctors hope you get sick, cops hope you're criminal, mechanics hope you have car trouble, but only a thief wishes prosperity for you.*",
    "*Tall people are expected to use their reach to help shorter people, but if a tall person were to ask a short person to hand them something they dropped on the floor it'd be insulting.*",
    "*Aliens invaded the Moon on July 20th, 1969.*",
    "*When you say 'Forward' or 'Back', your lips move in those directions.*",
    "*I've woken up over 10,000 times and I'm still not used to it.*",
    "*Tobacco companies kill their best customers and condom companies kill their future customers*",
    "*When a company offers you a better price after you cancel their subscription, they're just admitting they were overcharging you.*",
    "*People who are goodlooking but have terrible personalities are basically real life click baits.*",
    "*When you bake bread, you basically give thousands of yest organisms false hope by feeding them sugar, before ruthlessly baking them to death in an oven and eating their corpses.*",
    "*My dog understand several human words. I don’t understand any dog barks. He may be smarter than me.*",
    "*Nothing is on fire, fire is on things.*",
    "*If Google matched people up by their browsing history, it could be the greatest online dating website of all time.*",
    "*Someone who says \"I'll be there in 6 minutes\" will normally arrive before someone who says \"I will be there in 5 minutes\"*",
    "*If aliens come to earth, we have to explain why we made dozens of movies in which we fight and kill them*",
    "*At age 25 if a friend tells me they're pregnant I don't know whether to say \"oh shit!\" Or \"congratulations!\"*",
    "*I don't know a single person who would want a thinner phone over a few hours of extra battery life.*",
    "*Earth is like a guy who knows exactly where to stand next to a bonfire.*",
    "*We stick kids in classrooms 7 hours a day, give them another few hours of homework, actively discourage them from playing outside, and then wonder why kids today are so out of shape.*",
    "*Cemeteries would be way more interesting if they put the cause of death on the headstone.*",
    "*If cats had wings,they'd still just lay there.*",
    "*Taxes are like a subscription to your Country that you can't cancel, no matter how bad the service gets.*",
    "*When Sweden is playing against Denmark, it is SWE-DEN. The remaining letters, not used, is DEN-MARK*",
    '*An "unlimited minutes per month" phone plan really only gives you 44,640 minutes per month at best*',
    "*Your stomach must think that all potatoes are mashed.*",
    "*I am 100% confident that if I ever hit a kid with my car, it will be because I'm staring at my speedometer in a school zone.*",
    "*When jogging, we put on special clothes so people don't think we are running from or to something.*",
    "*In order to fall asleep, you have to pretend to be asleep.*",
    "*The Japanese flag could actually be a pie chart of how much of Japan is Japan.*",
    "*Imagine how terrifying fire would be if it wasn't a light source...*",
    "*Using solar panels to power an air conditioning unit is like using the Sun's power against itself.*",
    "*Apple has anorexia: it is obsessed with thinness which leads it to remove things people actually need.*",
    "*In normal English, execute and kill are synonyms, but on a computer, they're antonyms.*",
    "*If you hit yourself and get hurt, are you weak or strong?*",
    "*Teenagers drive like they have limited time & old people drive like they have all the time in the world.*",
    "*Just exactly why are there taxis and buses in a movie where everyone is a vehicle themselves?*",
    '*Why do people say "tuna fish" when they don\'t say "beef mammal" or "chicken bird"?*',
    '*Do regular dogs see police dogs & think, "Oh no it\'s a cop?"*',
  ]
  bot_response = random.choice(thought)
  await interaction.response.send_message(bot_response)


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

import re


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

            print(
                f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] - [{interaction.channel}] -  {interaction.user.name} used /dm"
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



# Listen for DMs
@bot.event
async def on_message(message):
  if isinstance(message.channel,
                discord.DMChannel) and message.author != bot.user:
    # Copy the message and sender's name
    sender = message.author
    content = message.content
    channel_name = sender.name + "#" + sender.discriminator
    message_text = f"__`{channel_name}:`__ {content}"

    # DM the copied message to the bot owner
    owner = await bot.fetch_user(676367462270238730)
    await owner.send(message_text)

  await bot.process_commands(message)







  


# Law


@bot.tree.command(name="law",
                  description='Learn a law from the "48 Laws of Power"!')
@app_commands.describe(
  law="Specify the number of Law. If left blank, a random one will be sent!")
async def law(interaction: discord.Interaction, law: Optional[int] = None):
  if law is not None and (law < 1 or law > 48):
    await interaction.response.send_message(
      "That law doesn't exist. Please enter a number between 1-48",
      ephemeral=True)
    return

  responses = {
    1:
    "__**Law 1**__: Never Outshine the Master. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%201)",
    2:
    "__**Law 2**__: Never put too Much Trust in Friends, Learn how to use Enemies. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%202)",
    3:
    "__**Law 3**__: Conceal your Intentions. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%203)",
    4:
    "__**Law 4**__: Always Say Less than Necessary. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%204)",
    5:
    "__**Law 5**__: So Much Depends on Reputation - Guard it with your Life . \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%205)",
    6:
    "__**Law 6**__: Court Attention at all Costs. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%206)",
    7:
    "__**Law 7**__: Get others to do the Work for you, but Always Take the Credit. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%207)",
    8:
    "__**Law 8**__: Make other People come to you - use Bait if Necessary. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%208)",
    9:
    "__**Law 9**__: Win through your Actions, Never through Argument. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%209)",
    10:
    "__**Law 10**__: Infection: Avoid the Unhappy and Unlucky. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2010)",
    11:
    "__**Law 11**__: Learn to Keep People Dependent on You. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2011)",
    12:
    "__**Law 12**__: Use Selective Honesty and Generosity to Disarm your Victim. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2012)",
    13:
    "__**Law 13**__: When Asking for Help, Appeal to People's Self-Interest. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2013)",
    14:
    "__**Law 14**__: Pose as a Friend, Work as a Spy. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2014)",
    15:
    "__**Law 15**__: Crush your Enemy Totally. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2015)",
    16:
    "__**Law 16**__: Use Absence to Increase Respect and Honor. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2016)",
    17:
    "__**Law 17**__: Cultivate an Air of Unpredictability. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2017)",
    18:
    "__**Law 18**__: Be the Master of your own Image. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2018)",
    19:
    "__**Law 19**__: Plan All the Way to the End. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2019)",
    20:
    "__**Law 20**__: The Art of Timing is the Art of Deception. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2020)",
    21:
    "__**Law 21**__: Play a Sucker to Catch a Sucker - Seem Dumber than your Mark. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2021)",
    22:
    "__**Law 22**__: Use the Surrender Tactic: Transform Weakness into Power. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2022)",
    23:
    "__**Law 23**__: Concentrate Your Forces. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2023)",
    24:
    "__**Law 24**__: Play the Perfect Courtier. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2024)",
    25:
    "__**Law 25**__: Re-Create Yourself. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2025)",
    26:
    "__**Law 26**__: Keep Your Hands Clean. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2026)",
    27:
    "__**Law 27**__: Play on People's Need to Believe to Create a Cult-like Following. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2027)",
    28:
    "__**Law 28**__: Enter Action with Boldness. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2028)",
    29:
    "__**Law 29**__: Plan All the Way to the End. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2029)",
    30:
    "__**Law 30**__: Make your Accomplishments Seem Effortless. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2030)",
    31:
    "__**Law 31**__: Control the Options: Get Others to Play with the Cards you Deal. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2031)",
    32:
    "__**Law 32**__: Play to People's Fantasies. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2032)",
    33:
    "__**Law 33**__: Discover Each Man's Thumbscrew. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2033)",
    34:
    "__**Law 34**__: Be Royal in your Own Fashion: Act like a King to be treated like one. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2034)",
    35:
    "__**Law 35**__: Master the Art of Timing. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2035)",
    36:
    "__**Law 36**__: Disdain Things you cannot have: Ignoring them is the best Revenge. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2036)",
    37:
    "__**Law 37**__: Create Compelling Spectacles. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2037)",
    38:
    "__**Law 38**__: Think as you like but Behave like others. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2038)",
    39:
    "__**Law 39**__: Stir up Waters to Catch Fish. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2039)",
    40:
    "__**Law 40**__: Ignore the Conventional Wisdom. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2040)",
    41:
    "__**Law 41**__: Avoid Stepping into a Great Man's Shoes. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2041)",
    42:
    "__**Law 42**__: Strike the Shepherd and the Sheep will Scatter. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2042)",
    43:
    "__**Law 43**__: Work on the Hearts and Minds of Others. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2043)",
    44:
    "__**Law 44**__: Disarm and Infuriate with the Mirror Effect. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2044)",
    45:
    "__**Law 45**__: Preach the Need for Change, but Never Reform too much at Once. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2045)",
    46:
    "__**Law 46**__: Never appear too Perfect. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2046)",
    47:
    "__**Law 47**__: Do not go Past the Mark you Aimed for; In Victory, Learn when to Stop. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2047)",
    48:
    "__**Law 48**__: Assume Formlessness. \n\n[Learn More](https://48laws.alexxsh16.repl.co/#:~:text=Law%2048)"
  }

  if law is None:
    law = random.randint(1, 48)

  response = responses[law]
  colors = [0x071b79, 0xeb1c24, 0xc1833f]
  embed = discord.Embed(
    title="48 Laws of Power",
    url="https://48laws.alexxsh16.repl.co/",
    color=random.choice(colors),
    description=response,
  )

  await interaction.response.send_message(embed=embed)


# say
@bot.tree.command(
  name="say",
  description="The bot won't listen unless you are cool, don't try XD")
@app_commands.describe(
  thing_to_say="Pray, tell me, my lord, what words should I utter?")
async def say(interaction: discord.Interaction, thing_to_say: str):
    # Replace "\n" with newline characters
    thing_to_say = thing_to_say.replace("\\n", "\n")
    
    authorized_user = [
        676367462270238730, 1071057018183499861, 740509592701763604,
        738786980237934613, 769553775941386252, 466263032218124319,
        313739229962436608
    ]
    if interaction.user.id in authorized_user:
        await interaction.channel.send(thing_to_say)
        await interaction.response.send_message("Sent!", ephemeral=True)
        
        log_channel_id = 1152550043333689454
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"__`[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC]`__ - **{interaction.user.name}** used </say:1080898269951049769> in <#{interaction.channel_id}>")
    else:
        await interaction.response.send_message("I only listen to certain people for that command!", ephemeral=True)


# Joke


@bot.tree.command(
  name="joke",
  description=
  "Interact with the bot's broken humor! Dm Alexsh#0903 to add more jokes.")
async def joke(interaction: discord.Interaction):
  random_value = random.randint(1, 9)
  if random_value == 1:
    await interaction.response.send_message(
      f"I told my friend she was drawing her eyebrows too high. She looked surprised."
    )
  elif random_value == 2:
    await interaction.response.send_message(
      f'And the Lord said unto John, "Come forth and you will receive eternal life." But John came fifth, and won a toaster.'
    )
  elif random_value == 3:
    await interaction.response.send_message(
      f"Parallel lines have so much in common. It's a shame they'll never meet."
    )
  elif random_value == 4:
    await interaction.response.send_message(
      f"My grandfather has the heart of a lion and a lifetime ban at the zoo.")
  elif random_value == 5:
    await interaction.response.send_message(
      f"You're not completely useless, you can always serve as a bad example. ||Oh wait, can you?||"
    )
  elif random_value == 6:
    await interaction.response.send_message(
      f"Working in a mirror factory is something I can totally see myself doing."
    )
  elif random_value == 7:
    await interaction.response.send_message(
      f"Why do cows wear bells? ||Because their horns don't work.||")
  elif random_value == 8:
    await interaction.response.send_message(f"I, for one, like Roman numerals."
                                            )
  elif random_value == 9:
    await interaction.response.send_message(
      f"You know what the say about cliffhangers...")


# meme


@bot.tree.command(
  name="meme",
  description="Sends a random meme! Dm Alexsh#0903 to add more memes.")
async def meme(interaction: discord.Interaction):
  random_value = random.randint(1, 42)
  if random_value == 1:
    await interaction.response.send_message(
      f"https://media.discordapp.net/attachments/1086925161116225556/1086925193840181280/336109657_238030565332854_7455901385199707477_n.png?width=663&height=663"
    )
  elif random_value == 2:
    await interaction.response.send_message(
      f"https://media.discordapp.net/attachments/1086925161116225556/1087302391222784040/1cf4ikp1f4ka1.jpg?width=643&height=663"
    )
  elif random_value == 3:
    await interaction.response.send_message(
      f"https://media.discordapp.net/attachments/1086925161116225556/1087302391612846161/2-6.png?width=538&height=663"
    )
  elif random_value == 4:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302392019701770/20th_Century_Fox_3.0.mp4"
    )
  elif random_value == 5:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302392669810780/20th_Century_Fox.mp4"
    )
  elif random_value == 6:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302393382838282/20211230_072505.jpg"
    )
  elif random_value == 7:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302393621925898/332398296_671860591407863_8683502081539978156_n.png"
    )
  elif random_value == 8:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302393936490526/1647891277351_.mp4"
    )
  elif random_value == 9:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302394431426640/cena.mp4"
    )
  elif random_value == 10:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302394842460231/d8lla63o70e81.gif"
    )
  elif random_value == 11:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302395228344320/emo_dam1...mp4"
    )
  elif random_value == 12:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302701328629780/epic.like.bro-20220211_072849-273857229_3440037139549060_3048094692511838497_n..jpg"
    )
  elif random_value == 13:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302701601271828/gbfw79lv22ka1.jpg"
    )
  elif random_value == 14:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302701886488626/h76vr5nholka1.jpg"
    )
  elif random_value == 15:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302703480307772/oca189pvueka1.jpg"
    )
    await interaction.channel.send(f"Wait what? That's not...normal!")
  elif random_value == 16:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302702146531328/haha.jpg"
    )
  elif random_value == 17:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302702373027910/hsbz4ifzztia1.jpg"
    )
  elif random_value == 18:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302702687584276/mp4.mp4"
    )

  elif random_value == 19:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302703039918130/naughty.students-20220210_114915-273721159_1134102974094311_8649981506522016602_n.webp..jpg"
    )

  elif random_value == 20:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302703258025984/nvmaf28mk6ka1.jpg"
    )

  elif random_value == 21:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087302703740366888/emo_dam2...mp4"
    )

  elif random_value == 21:
    await interaction.response.send_message(
      f"https://media.discordapp.net/attachments/1086925161116225556/1087303223481745458/V0ebhhB3PD-LgYdJB1SLqD2qXJcK5wuZKtIvd945OBw.jpeg"
    )

  elif random_value == 22:
    await interaction.response.send_message(
      f"https://media.discordapp.net/attachments/1086925161116225556/1087303223729192990/p1sn0xip6dka1.jpg?width=339&height=661"
    )

  elif random_value == 23:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303224031195216/programmer-coding-jokes-fb52.png"
    )

  elif random_value == 24:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303224349966397/sarcastic_us-20220212_081800-273686855_669108501112394_2688410330413628378_n..jpg"
    )

  elif random_value == 25:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303224568053880/ss.PNG"
    )

  elif random_value == 26:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303224958140506/ss2.PNG"
    )

  elif random_value == 27:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303225243336755/ss3.PNG"
    )

  elif random_value == 28:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303225465647154/ss4.PNG"
    )

  elif random_value == 29:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303225725681674/tbh.jpg"
    )

  elif random_value == 29:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303225956380712/uxizmgw8dbka1.jpg"
    )

  elif random_value == 30:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303415715082270/WhatsApp_Video_2021-12-21_at_2.41.18_PM.mp4"
    )

  elif random_value == 31:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303416063205447/xklka3yipqo81.gif"
    )

  elif random_value == 32:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303416449089588/y2mate.com_-_Ghost_gets_hit_by_folding_chair_on_film_ORIGINAL_480p.mp4"
    )

  elif random_value == 33:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303416998539315/YES.mp4"
    )

  elif random_value == 34:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087303417782870106/yv67hedg4ika1.jpg"
    )

  elif random_value == 35:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087305425797529740/zuikjcfxubka1.gif"
    )

  elif random_value == 36:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087305426204368906/20th_Century_Fox_2.0.mp4"
    )
    await interaction.response.send_message(f"Ouch!")

  elif random_value == 37:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087305426875449474/h8v08nrgwcka1.gif"
    )

  elif random_value == 38:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087305427278118932/just_people_who_know.mp4"
    )

  elif random_value == 39:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087305427768844348/okbfshii62e81.gif"
    )

  elif random_value == 40:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1087305428158906389/q52t1y5bqzd81.gif"
    )

  elif random_value == 41:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1088179028046905484/336797377_975698700479607_1618253988779812968_n.png"
    )

  elif random_value == 42:
    await interaction.response.send_message(
      f"https://cdn.discordapp.com/attachments/1086925161116225556/1090235369720664094/hehehehehehehe.jpg"
    )


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






# Help
@bot.tree.command(name="help",
                  description="Learn about the bot & how to use it.")
async def help(interaction: discord.Interaction):
  embed = discord.Embed(
    title="About Galactica",
    description=
    "Hi there! I'm Galactica, one of the official bots of _Galaxy's Edge_ <a:HyperYay:1003182174129889290>.\n\n__**Try out my  commands:**__\n\n</help:1082383548197109912>: `Views this command`\n\n</meme:1080898269951049771>:`Sends a random meme`\n\n</confess:1080898269951049772>: `Make a confession in` <#1080435136614629436>\n\n</ping:1099752021877346437>: `Get the bot ping in ms`\n\n</chat:1091468756988985345> _(temporarily unavailable)_: `Chat with AI features of the bot. Suggested to use in` <#1080917858583851100>\n\n</joke:1080898269951049770>: `Sends a random joke. Can be harsh sometimes.`\n\n</law:1086637608198754304>: `Learn about a law from the 48 Laws of Power`\n\n</suggest_qotd:1091455610584838266>: `Suggest a question for Question of the Day`\n\n</suggest_sotd:1091462046857560074> `Suggest a song for Song of the Day`\n\n</shower_thoughts:1093458053250162740>: `Intrigue your thoughts. Use at your own risk!`\n\n</akinator:1118151610032472126>: `Play a Game of Akinator (Still Under Development)`",
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    color=random.randint(0, 0xFFFFFF),
    timestamp=datetime.utcnow())
  embed.set_author(
    name="Galactica",
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    icon_url=
    "https://images-ext-1.discordapp.net/external/fTZyDndCJf6TC_1kaTS_gl9gl5A94dr7_85cyz-nWP8/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/803131866139983892/098a3d6f9890152d550488483650620c.png?width=663&height=663"
  )
  embed.set_footer(text=f"Requested by {interaction.user.name}",
                   icon_url=interaction.user.avatar.url)
  await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(token)
