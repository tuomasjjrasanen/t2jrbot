# -*- coding: utf-8 -*-

# Quit command plugin for t2jrbot.
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

class QuitPlugin(object):

    def __init__(self, bot):
        self.bot = bot

        self.bot.plugins["command"].register_command("!quit", self.command_quit, "Quits the bot, "
                                                     "optionally with a message. "
                                                     "Usage: !quit [MESSAGE], "
                                                     "e.g. !quit So Long, and Thanks for All the Fish!")

    def command_quit(self, nick, host, channel, this_command, argstr):
        self.bot.stop()
        self.bot.irc.send_quit(argstr)

def load(bot, conf):
    return QuitPlugin(bot)
