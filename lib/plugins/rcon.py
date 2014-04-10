# -*- coding: utf-8 -*-

# Rcon plugin for t2jrbot.
# Copyright © 2014 Tuomas Räsänen <tuomasjjrasanen@tjjr.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import subprocess

import t2jrbot.conf

class _RconPlugin(object):

    def __init__(self, bot, server, port, password):
        self.__bot = bot
        self.__server = server
        self.__port = port
        self.__password = password

        command_plugin = self.__bot.plugins["t2jrbot.plugins.command"]
        command_plugin.register_command("!rcon_status", self.__command_rcon_status,
                                        "Show game status. Usage: !rcon_status")

        command_plugin.register_command("!rcon_say", self.__command_rcon_say,
                                        "Say something in the game. "
                                        "Usage: !rcon_say Pizzas are here!")

    def __crcon(self, rcon_cmd):
        args = ["crcon"]
        if self.__password:
            args.append("-p")
            args.append(self.__password)
        args.append("-P")
        args.append(self.__port)
        args.append(self.__server)
        args.append(rcon_cmd)

        out = subprocess.check_output(args)

        if not out.strip():
            return False, out

        return True, out.lstrip("\xff ") # Remove preceding garbage.

    def __command_rcon_status(self, nick, host, channel, this_command, argstr):
        ok, out = self.__crcon("status")
        if not ok:
            self.__bot.irc.send_privmsg(channel,
                                        "%s: There is not any game running at the moment." % nick)
            return

        gamemap = ""
        players = []
        is_playerlist_reached = False
        for line in out.splitlines():
            if not is_playerlist_reached and line.startswith("map:"):
                gamemap = line.split(":")[1].strip()
                continue
            if not is_playerlist_reached and line.startswith("---"):
                is_playerlist_reached = True
                continue
            if is_playerlist_reached:
                parts = line.split()
                if parts:
                    players.append(parts[3])

        self.__bot.irc.send_privmsg(channel, "Map: %s / %d players: %s"
                                    % (gamemap, len(players),
                                       ", ".join(players)))

    def __command_rcon_say(self, nick, host, channel, this_command, argstr):
        ok, out = self.__crcon("say %s" % argstr)
        if not ok:
            self.__bot.irc.send_privmsg(channel,
                                        "%s: There is not any game running at the moment." % nick)
            return

def validate_conf(conf):
    t2jrbot.conf.validate_keys(conf, ["server", "port", "password"])

    t2jrbot.conf.validate_value(conf, "server",
                                lambda v: isinstance(v, str),
                                required=False)

    t2jrbot.conf.validate_value(conf, "port",
                                lambda v: isinstance(v, int) and 0 < v < 65536,
                                required=False)

    t2jrbot.conf.validate_value(conf, "password",
                                lambda v: isinstance(v, str),
                                required=False)

def load(bot, conf):
    validate_conf(conf)

    server = conf.get("server", "localhost")
    port = conf.get("port", 27960)
    password = conf.get("password", None)

    return _RconPlugin(bot, server, port, password)
