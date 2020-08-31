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

    *stats ou *s *--> affiche les statistiques du joueur*
    *reset ou *r *--> remet les statistiques du joueur à zero*
    *help ou *h *--> affiche ce message*
    """


def roll(content, author, ref_author):
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

    records[ref_author].logit(result)
    return msg


records = {}


class recorder():
    def __init__(self, author):
        self.logs = {}
        self.author = author

    def logit(self, entry):
        if entry in self.logs:
            self.logs[entry] += 1
        else:
            self.logs[entry] = 1

    def listAll(self):
        total = sum([v for v in self.logs.values()])
        msg = f"**Statistiques de jeu pour {self.author.display_name} \
depuis TIME**\n"
        if len(self.logs) == 0:
            return msg+"Aucune pour le moment. \
Allez on met le nez dans l'intrigue !"
        else:
            return msg+"\n".join([f'{row} : {self.logs[row]} \
[{100.0/total*self.logs[row]:.2f}%]' for row in self.logs])

    def reset(self):
        self.logs = {}
        return f"La session de {self.author.display_name} a été remise à zerro"


def initUserSession(author):
    if author not in records:
        records[author] = recorder(author)

    # print(f"records:{records}\n{records[author].listAll():}")


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    ref_author = message.author
    author = message.author.display_name
    msg = ""

    initUserSession(ref_author)

    if message.content.startswith(('*help', '*h')):
        msg = help()

    elif message.content.startswith(('*reset', '*r')):
        msg = records[ref_author].reset()

    elif message.content.startswith(('*stats', '*s')):
        msg = records[ref_author].listAll()

    elif message.content.startswith('*'):
        msg = roll(message.content, author, ref_author)

    if(msg != ""):
        await message.channel.send(msg)


with open("token.txt", 'r') as f:
    token = f.readline()

client.run(token)
