#! /usr/bin/env python3
# coding: utf-8

"""
Neobot is a rolling die Discord bot for the Neon city overdrive tabletop RPG

It's system requires to roll both white and black die so the black ones can
cancel successes from the white ones. Then we use the max remaining value
in order to determine the result:
    - 1, 2, 3 --> Failure
    - 4,5 --> Partial success
    - 6 --> Success
    - x times 6 --> Critical success with x-1 bonus
    - 0 remaining die --> Fumble


** CLASSES **

class: recorder
    method: __init__(self, author)
    method: logit(self, entry)
    method: listAll(self)
    method: reset(self)


** GLOBAL METHODS **

    method: sendEmail(message, author)

    method: parseResult(remain)

    method: help()

    method: roll(content, author, ref_author)

    method: initUserSession(author)

** EVENT METHODS **

    client.event: async def on_ready()
    client.event: async def on_message(message)
    client.event: async def on_raw_message_delete(message)

** GLOBAL VARIABLES **

    variable: clients
    variable: records
    variable: global_logs

"""

import random
import datetime
import re

from smtplib import SMTP
from email.message import EmailMessage

import discord

client = discord.Client()
records = {}
global_logs = {}


def sendEmail(message, author):
    """
    Sends an email to the admin with the associated message and author name

    Args:
        message(str): the message to send to the admin
        author(str): the current name of the message author

    Returns:
        str: a message confirming that the email was send
    """

    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = f"Neoroll suggest from {author.name}"
        msg['From'] = 'naaokth@free.fr'
        msg['To'] = 'naaokth@free.fr'

        smtp = SMTP('localhost')
        # smtp.connect('smtp.free.fr', 465)
        smtp.send_message(msg)
        smtp.quit()
    except:
        return "L'email de suggestion n'a pas pu être envoyé"
    else:
        return "L'email de suggestion a été enregistré, merci"


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
    """
    Returns a text message to display when the *help command is called.

    Returns:
        str: a message containing  all the informations about the bot commands.
    """

    return """**Liste des commandes**:
    *5/3 *--> lance 5 dés blancs et 3 dés noirs*
    *2 *--> lance 2 dés blancs*
    *3/4 # Commentaire *--> lance les dés et ajoute un commentaire\
 près du résultat (le # est optionnel)*

    *stats ou *s *--> affiche les statistiques du joueur*
    *reset ou *r *--> remet les statistiques du joueur à zero*

    *help ou *h *--> affiche ce message*

    *suggest Suggestion *--> envoie un email avec la suggestion*

    **Si vous effacez votre commande, Neoroll effacera sa réponse**
    """


def roll(content, author):
    """
    Parses the message sent by the author in order to get the rolling command,
    then execute this command and returns the appropriate answer.

    Args:
        content(str): A text message to parse to get the command.
        author(str): The author of the command.

    Returns:
        str: a message with the result generated with the parsed command.

    Raises:
        SyntaxError: An error occured because of a wrong command call.
    """

    display_name = author.display_name

    reg_split = re.search(r'\*([0-9]+)\/*([0-9]*)\s*#*\s*(.*)', content)

    # Verify is the command is valid
    if reg_split is None:
        raise SyntaxError

    # Collect groups
    reg_groups = reg_split.groups()
    white_die = int(reg_groups[0])
    black_die = int(reg_groups[1]) if reg_groups[1] != "" else 0
    comment = reg_groups[2]

    # Roll die
    p = ['s' if x > 1 else '' for x in [white_die, black_die]]
    white = [random.randint(1, 6) for x in range(white_die)]

    if black_die == 0:
        # Roll only white die
        result = parseResult(white)
        msg = f"**{display_name}** *lance {white_die} dé{p[0]} blanc{p[0]} \
{sorted(white)}* \n**{result}**"

    else:
        # Roll black and white die
        black = [random.randint(1, 6) for x in range(black_die)]

        remain = sorted(white[:])
        for x in black:
            try:
                remain.remove(x)
            except ValueError:
                pass

        result = parseResult(remain)
        msg = f"**{display_name}** *lance {white_die} dé{p[0]} blanc{p[0]} \
{sorted(white)} et {black_die} dé{p[1]} noir{p[1]} {sorted(black)} avec pour \
résultat {str(remain)}* \n**{result}**"

    if comment != "":
        msg += f" # *{comment}*"

    records[author].logit(result)
    return msg


class recorder():
    def __init__(self, author):
        self.author = author
        self.reset()

    def logit(self, entry):
        if entry in self.logs:
            self.logs[entry] += 1
        else:
            self.logs[entry] = 1

    def listAll(self):
        total = sum([v for v in self.logs.values()])
        msg = f"**Statistiques de jeu pour {self.author.display_name} \
depuis le {self.datetime.strftime('%d/%m à %H:%M')}**\n"
        if len(self.logs) == 0:
            return msg+"Aucune pour le moment. \
Allez on met le nez dans l'intrigue !"
        else:
            sorted_logs = sorted(self.logs.items(), key=lambda v: v[1], reverse=True)
            return msg+"\n".join([f'{row[1]} x {row[0]} \
[{100.0/total*row[1]:.2f}%]' for row in sorted_logs])

    def reset(self):
        self.logs = {}
        self.datetime = datetime.datetime.now()
        return f"La session de {self.author.display_name} a été remise à zero"


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

    if message.content.startswith('*'):

        ref_author = message.author
        msg = ""

        initUserSession(ref_author)

        if message.content.startswith(('*suggest')):
            msg = sendEmail(message.content, ref_author)

        elif message.content.startswith(('*help', '*h')):
            msg = help()

        elif message.content.startswith(('*reset', '*r')):
            msg = records[ref_author].reset()

        elif message.content.startswith(('*stats', '*s')):
            msg = records[ref_author].listAll()

        elif message.content.startswith('*'):
            try:
                msg = roll(message.content, ref_author)
            except SyntaxError:
                print(f"SyntaxError:{message.content} from {author}")

        if(msg != ""):
            sent = await message.channel.send(msg)
            global_logs[message.id] = (message, sent)

    # print(f"---> message:{message}")


@client.event
async def on_raw_message_delete(message):
    id = message.message_id
    if id in global_logs:
        await global_logs[id][1].delete()
        del global_logs[id]
        print(f"The global_logs size is {len(global_logs)}")


with open("token.txt", 'r') as f:
    token = f.readline()

client.run(token)
