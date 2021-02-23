import os

import discord
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


from Tournament import *


async def isPrivateMessage( ctx, send: bool = True ) -> bool:
    digest = (str(ctx.message.channel.type) == 'private')
    if digest and send:
        await ctx.send( f'In general, you are not allowed to send commands via DM. Each tournament is tied to a server. Please send this message from the appropriate server.' )
    return digest

async def isTournamentAdmin( ctx, send: bool = True ) -> bool:
    digest = False
    adminMention = getTournamentAdminMention( ctx.message.guild )
    for role in ctx.message.author.roles:
        digest |= str(role).lower() == "tournament admin"
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, you do not admin permissions for tournaments on this server. Please do not do this again or {adminMention} may intervene.' )
    return digest

async def checkTournExists( tourn, ctx, send: bool = True ) -> bool:
    digest = ( tourn in tournaments )
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
    return digest

async def correctGuild( tourn, ctx, send: bool = True ) -> bool:
    digest = ( tournaments[tourn].hostGuildName == ctx.message.guild.name )
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server. Please send this command from the correct server.' )
    return digest

async def isTournDead( tourn, ctx, send: bool = True ) -> bool:
    adminMetnion = getTournamentAdminMention( ctx.message.guild )
    digest = tournaments[tourn].isDead( )
    if digest and send:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
    return digest

async def isTournRunning( tourn, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].isActive and not await isTournDead( tourn, ctx, send )
    if send and not tournaments[tourn].isActive:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has not been started yet.' )
    return digest

async def isRegOpen( tourn, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].regOpen
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, registration for {tourn} is closed. Please contact tournament staff if you think this is an error.' )
    return digest

async def hasRegistered( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = plyr in tournaments[tourn].players
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, you are not registered for {tourn}. Please register before trying to access the tournament.' )
    return digest
        
async def isActivePlayer( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].players[plyr].isActive( )
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, you registered for {tourn} but have been dropped. Talk to tournament admin if you think this is an error.' )
    return digest
    
async def hasOpenMatch( tourn, plyr, ctx, send: bool = True ) -> bool:
    digest = tournaments[tourn].players[plyr].hasOpenMatch( )
    if send and not digest:
        await ctx.send( f'{ctx.message.author.mention}, you are not an active player in any match, so you do not need to do anything.' )
    return digest

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
            break
    return adminMention

def currentGuildTournaments( a_guildName: str ):
    tourns = {}
    for tourn in tournaments:
        if not tournaments[tourn].isDead() and tournaments[tourn].hostGuildName == a_guildName:
            tourns[tourn] = tournaments[tourn]
    return tourns

def hasStartedTournament( a_guildName ) -> bool:
    for tourn in tournaments:
        if tournaments[tourn].tournStarted and tournaments[tourn].hostGuildName == a_guildName:
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
        if f'<@!{member.id}>' == a_memberName:
            return member
        if f'<@{member.id}>' == a_memberName:
            return member
    return ""

def splitMessage( msg: str, limit: int = 2000, delim: str = "\n" ) -> List[str]:
    if len(msg) <= limit:
        return [ msg ]
    msg = msg.split( delim )
    digest = [ "" ]
    for submsg in msg:
        if len(digest[-1]) + len(submsg) <= limit:
            digest[-1] += delim + submsg
        else:
            digest.append( submsg )
    return digest
    


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

tournaments = {}
playersToBeDropped = []

savedTournaments = [ f'currentTournaments/{d}' for d in os.listdir( "currentTournaments" ) if os.path.isdir( f'currentTournaments/{d}' ) ]


# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    await bot.wait_until_ready( )
    print(f'{bot.user.name} has connected to Discord!\n')
    for guild in bot.guilds:
        print( f'This bot is connected to {guild.name} which has {len(guild.members)}!' )    
    print( "" )
    for tourn in savedTournaments:
        newTourn = tournament( "", "" )
        newTourn.loop = bot.loop
        newTourn.loadTournament( tourn )
        if newTourn.tournName != "":
            tournaments[newTourn.tournName] = newTourn
    for tourn in tournaments:
        guild = bot.get_guild( tournaments[tourn].guildID )
        if type( guild ) != None:
            tournaments[tourn].assignGuild( guild )
            tournaments[tourn].loop = bot.loop


def message_to_xml( msg: discord.Message, indent: str = "" ) -> str:
    digest  = f'{indent}<message author="{msg.author}" time="{msg.created_at}">\n'
    digest += f'{indent*2}<text>{msg.content}</text>\n'
    digest += f'{indent}</message>\n'
    return digest


@bot.command(name='test')
async def test( ctx, *args ):
    if len(args) == 0:
        games = 6
    else:
        games = int(args[0])
    
    limit = 1024
    
    if len(args) > 3:
        points = [ float(args[1]), float(args[2]), float(args[3]) ]
    else:
        points = [ 3, 1, 0 ]
    
    results = []
    
    for g in range(3,games+1):
        for win in range(3,g+1):
            draw = 0
            while draw < 3 and draw + win <= g:
                loss = (g - win) - draw
                results.append((win,draw,loss,win*points[0] + draw*points[1] + loss*points[2],100*win/g))
                draw += 1
    
    results.sort( key=lambda x: x[0]+x[1]+x[2], reverse=True )
    results.sort( key=lambda x: x[4], reverse=True )
    results.sort( key=lambda x: x[3], reverse=True )
    bed = discord.Embed( )
    f_1 = ""
    f_2 = ""
    f_3 = ""
    for r in results:
        tmp = f'{r[0]}-{r[1]}-{r[2]}\n'
        if len(f_1) + len(tmp) > limit:
            break
        f_1 += tmp
        f_2 += f'{r[3]}\n'
        f_3 += f'{trunk(r[4])}\n'
    
    bed.add_field( name="Match Result", value=f_1 )
    bed.add_field( name="Match Points", value=f_2 )
    bed.add_field( name="Win Percent ", value=f_3 )
    
    await ctx.send( content="This is an example set of standings. The invisible breaker here is the number of games played.", embed=bed )
    
    
    
@bot.command(name='embed')
async def embedTest( ctx, *args ):
    #members = ctx.message.channel.members
    members = ctx.message.guild.members
    limit = 1024

    bed = discord.Embed()
    
    names  = [ "Name:", "Points & Win Percent:", "Opp. WP" ]
    values = [ "", "", "" ]
    
    lengths = [ len(s) for s in names ]
    count = 1
    for mem in members:
        line = [ f'{count}) {mem.display_name}\n', f'0,\t00.0000%\n', f'00.0000%\n' ]
        line_lengths = [ len(s) for s in line ]
        if (lengths[0] + line_lengths[0] <= limit) and (lengths[1] + line_lengths[1] <= limit) and (lengths[2] + line_lengths[2] <= limit):
            values  = [ values[i] + line[i] for i in range(len(values)) ]
            lengths = [ lengths[i] + line_lengths[i] for i in range(len(lengths)) ]
        else:
            break
        count += 1
        
    for i in range(len(names)):
        bed.add_field( name=names[i], value=values[i] )
    
    print( len(bed), lengths )
    
    await ctx.send( embed=bed )
    

@bot.command(name='scrape')
async def adminPlayerProfile( ctx ):
    messages = await ctx.message.channel.history( limit=100000, oldest_first=True ).flatten( )
    with open( "scrapTest.xml", "w" ) as f:
        f.write( "<history>\n" )
        for msg in messages:
            f.write( message_to_xml( msg, "\t" ) )
        f.write( "</history>" )
    print( f'A total of {len(messages)} messages were scrapped.' )






