import os


import discord
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


from Tournament import *


def isPrivateMessage( a_message ) -> bool:
    return str(a_message.channel.type) == 'private'
    
def isTournamentAdmin( a_author ) -> bool:
    retValue = False
    for role in a_author.roles:
        retValue |= str(role).lower() == "tournament admin"
    return retValue

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
            break
    return adminMention

def currentGuildTournaments( a_guildName: str ):
    tourns = {}
    for tourn in currentTournaments:
        if not currentTournaments[tourn].isDead() and currentTournaments[tourn].hostGuildName == a_guildName:
            tourns[tourn] = currentTournaments[tourn]
    return tourns

def hasStartedTournament( a_guildName ) -> bool:
    for tourn in currentTournaments:
        if currentTournaments[tourn].tournStarted and currentTournaments[tourn].hostGuildName == a_guildName:
            return True
    return False

def findGuildMember( a_guild: discord.Guild, a_memberName: str ):
    for member in a_guild.members:
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
    return ""
    
def findPlayer( a_guild: discord.Guild, a_tourn: str, a_memberName: str ):
    role = discord.utils.get( a_guild.roles, name=f'{a_tourn} Player' )
    if type( role ) != discord.Role:
        return ""
    for member in role.members:
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
    return ""


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

currentTournaments = {}
closedTournaments = []
playersToBeDropped = []

# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    await bot.wait_until_ready( )
    print(f'{bot.user.name} has connected to Discord!')
    for tourn in currentTournaments:
        print( f'{tourn} has a guild ID of "{currentTournaments[tourn].guildID}".' )
        guild = bot.get_guild( currentTournaments[tourn].guildID )
        if type( guild ) != None:
            currentTournaments[tourn].assignGuild( guild )


def message_to_xml( msg: discord.Message, indent: str = "" ) -> str:
    digest  = f'{indent}<message author="{msg.author}" time="{msg.created_at}">\n'
    digest += f'{indent*2}<text>{msg.content}</text>\n'
    digest += f'{indent}</message>\n'
    return digest

@bot.command(name='scrap')
async def adminPlayerProfile( ctx ):
    messages = await ctx.message.channel.history( limit=100000, oldest_first=True ).flatten( )
    with open( "scrapTest.xml", "w" ) as f:
        f.write( "<history>\n" )
        for msg in messages:
            f.write( message_to_xml( msg, "\t" ) )
        f.write( "</history>" )
    print( f'A total of {len(messages)} messages were scrapped.' )























