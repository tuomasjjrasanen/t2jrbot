# -*- coding: utf-8 -*-

# Command helper plugin for t2jrbot.
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

class HelpPlugin(object):

    def __init__(self, bot):
        self.bot = bot

        self.bot.register_command("!help", self.command_help,
                                  "Since you got this far, "
                                  "you already know what this command does.")

    def command_help(self, nick, host, channel, this_command, argstr):
        command = argstr.strip()
        if not command:
            commands = sorted(self.bot.command_descriptions.keys())
            self.bot.irc.send_privmsg(channel,
                                      "%s: Commands: %s"
                                      % (nick, ", ".join(commands)))
            self.bot.irc.send_privmsg(channel,
                                      "%s: To get detailed help on a command, "
                                      "use %s COMMAND, e.g. %s %s"
                                      % (nick, this_command, this_command, this_command))
        else:
            try:
                descr = self.bot.command_descriptions[command]
            except KeyError:
                self.bot.irc.send_privmsg(channel,
                                          "%s: command '%s' not found" % (nick, command))
            else:
                self.bot.irc.send_privmsg(channel, "%s: %s - %s"
                                          % (nick, command, descr))

def load(bot, conf):
    return HelpPlugin(bot)
