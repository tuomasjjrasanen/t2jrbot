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

class CommandPlugin(object):

    def __init__(self, bot):
        self.bot = bot
        self.__command_handlers = {}
        self.__command_descriptions = {}

        self.bot.add_irc_callback(self.irc_privmsg, irccmd="PRIVMSG")
        self.register_command("!help", self.command_help,
                              "Since you got this far, "
                              "you already know what this command does.")

    def command_help(self, nick, host, channel, this_command, argstr):
        command = argstr.strip()
        if not command:
            commands = sorted(self.command_descriptions.keys())
            self.bot.irc.send_privmsg(channel,
                                      "%s: Commands: %s"
                                      % (nick, ", ".join(commands)))
            self.bot.irc.send_privmsg(channel,
                                      "%s: To get detailed help on a command, "
                                      "use %s COMMAND, e.g. %s %s"
                                      % (nick, this_command, this_command, this_command))
        else:
            try:
                descr = self.command_descriptions[command]
            except KeyError:
                self.bot.irc.send_privmsg(channel,
                                          "%s: command '%s' not found" % (nick, command))
            else:
                self.bot.irc.send_privmsg(channel, "%s: %s - %s"
                                          % (nick, command, descr))

    @property
    def command_descriptions(self):
        return dict(self.__command_descriptions)

    def register_command(self, command, handler, description=""):
        if command in self.__command_handlers:
            raise Error("command '%s' is already registered" % command)
        self.__command_handlers[command] = handler
        self.__command_descriptions[command] = description

    def unregister_command(self, command):
        try:
            del self.__command_handlers[command]
        except KeyError:
            raise Error("command '%s' is not registered" % command)
        del self.__command_descriptions[command]

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

        self.eval_command(nick, host, channel, command, argstr)

    def eval_command(self, nick, host, channel, command, argstr):
        try:
            command_handler = self.__command_handlers[command]
        except KeyError:
            # Silently ignore all input except registered commands.
            return

        try:
            command_handler(nick, host, channel, command, argstr)
        except Exception, e:
            self.irc.send_privmsg(channel,
                                  "%s: error: %s" % (nick, e.message))


def load(bot, conf):
    return CommandPlugin(bot)
