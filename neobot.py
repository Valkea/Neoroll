import discord
import random

client = discord.Client()


def parseResult(remain):

    if len(remain) == 0:
        return "Fumble"
    else:
        maxValue = max(remain)
        if maxValue <= 3:
            return "Echec"
        elif maxValue <= 5:
            return "Réussite partielle"
        elif maxValue == 6:
            c = remain.count(6)
            if c > 1:
                return f"Réussite critique et {c-1} bonus"
            return "Réussite"


def help():
    return """**Liste des commandes**:
    *5/3 *--> lance 5 dés blancs et 3 dés noirs*
    *2 *--> lance 2 dés blancs*
    *3/4 # Commentaire *--> lance les dés et ajoute un commentaire\
 près du résultat*
    """


def roll(content, author):
    """
    Roll die
    """

    comment = ""
    withComment = "#" in content

    if withComment:
        splitComment = content.split("#")
        content = splitComment[0].strip()
        comment = splitComment[1].strip()

    die = content[1:].split("/")
    p = ['s' if int(x) > 1 else '' for x in die]
    white = [random.randint(1, 6) for x in range(int(die[0]))]

    if len(die) == 1:
        # Roll only white die
        result = parseResult(white)
        msg = f"**{author}** *lance {die[0]} dé{p[0]} blanc{p[0]} \
{sorted(white)}* \n**{result}**"

    else:
        # Roll black and white die
        black = [random.randint(1, 6) for x in range(int(die[1]))]

        remain = sorted(white[:])
        for x in black:
            try:
                remain.remove(x)
            except ValueError:
                pass

        result = parseResult(remain)
        msg = f"**{author}** *lance {die[0]} dé{p[0]} blanc{p[0]} \
{sorted(white)} et {die[1]} dé{p[1]} noir{p[1]} {sorted(black)} avec pour \
résultat {str(remain)}* \n**{result}**"

    if withComment:
        msg += f" # *{comment}*"

    return msg


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    author = message.author.display_name
    msg = ""

    if message.content.startswith('*help'):
        msg = help()

    elif message.content.startswith('*'):
        msg = roll(message.content, author)

    if(msg != ""):
        await message.channel.send(msg)


with open("token.txt", 'r') as f:
    token = f.readline()

client.run(token)
