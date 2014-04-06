# -*- coding: utf-8 -*-

# Topic logger plugin for t2jrbot.
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

class EssentialPlugin(object):

    def __init__(self, bot):
        self.bot = bot

        self.bot.add_irc_callback(self.irc_error, irccmd="ERROR")
        self.bot.add_irc_callback(self.irc_privmsg, irccmd="PRIVMSG")

    def irc_error(self, prefix, this_irccmd, params):
        sys.exit(1)

    def irc_privmsg(self, prefix, this_irccmd, params):
        nick, sep, host = prefix.partition("!")

        target, text = params

        if target == self.bot.nick:
            # User-private messages are not supported and are silently
            # ignored.
            return

        channel = target

        # Ignore all leading whitespaces.
        text = text.lstrip()

        if not text.startswith("%s:" % self.bot.nick):
            # The message is not designated to me, ignore.
            return

        # Strip my nick from the beginning of the text.
        commandstr = text[len("%s:" % self.bot.nick):].lstrip()

        command, _, argstr = commandstr.partition(' ')

        self.bot.eval_command(nick, host, channel, command, argstr)

def load(bot, conf):
    return EssentialPlugin(bot)
