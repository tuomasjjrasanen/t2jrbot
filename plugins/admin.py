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

import types

def admin_eval_command(bot, nick, host, channel, command, argstr):
    admin_plugin = bot.plugins["admin"]

    if ((command in admin_plugin.command_whitelist)
        or
        ((nick, host) in admin_plugin.admins)):
        return admin_plugin._orig_eval_command(nick, host, channel, command, argstr)

    bot.send_irc_privmsg(channel,
                         "%s: only admins are allowed to %s" % (nick, command))

    return

class AdminPlugin(object):

    def __init__(self, bot, admins, command_whitelist):
        self.bot = bot

        self.admins = set([self.parse_admin_arg(a) for a in admins])
        self.command_whitelist = set(command_whitelist)

        # We are going to replace the original eval_command() with our own
        # which first checks whether the given command is is restricted only
        # to admins and if so is it given by an admin. We store the original
        # method so that we can use it for actually evaluating the command
        # once it has passed our checks.
        self._orig_eval_command = self.bot.eval_command
        self.bot.eval_command = types.MethodType(admin_eval_command, bot)

        self.bot.register_command("!admin_list",
                                  self.command_admin_list,
                                  "List bot admins. Usage: !admin_list")

        self.bot.register_command("!admin_add",
                                  self.command_admin_add,
                                  "Add a bot admin. "
                                  "Usage: !admin_add NICK!USER@HOST, "
                                  "e.g. !admin_add fanatic!fan.atic@example.org")

        self.bot.register_command("!admin_remove",
                                  self.command_admin_remove,
                                  "Remove a bot admin. "
                                  "Usage: !admin_remove NICK!USER@HOST, "
                                  "e.g. !admin_remove fanatic!fan.atic@example.org")

    def command_admin_list(self, nick, host, channel, this_command, argstr):
        admins = ["%s!%s" % (nick, host) for nick, host in self.admins]
        self.bot.send_irc_privmsg(channel, "%s: %s" % (nick, " ".join(admins)))

    def command_admin_add(self, nick, host, channel, this_command, argstr):
        admin_nick, admin_host = self.parse_admin_arg(argstr)
        self.admins.add((admin_nick, admin_host))

    def command_admin_remove(self, nick, host, channel, this_command, argstr):
        admin_nick, admin_host = self.parse_admin_arg(argstr)
        self.admins.discard((admin_nick, admin_host))

    def parse_admin_arg(self, admin):
        admin_nick, sep, admin_host = admin.partition("!")
        admin_nick = admin_nick.strip()
        admin_host = admin_host.strip()
        if not admin_nick or not sep or not admin_host:
            raise ValueError("malformed admin identifier, should "
                             "be of form 'nick!user@example.org'")
        return admin_nick, admin_host

def load(bot, conf):
    admins = conf.get("admins", "").splitlines()
    command_whitelist = conf.get("command_whitelist", "").splitlines()

    return AdminPlugin(bot, admins, command_whitelist)
