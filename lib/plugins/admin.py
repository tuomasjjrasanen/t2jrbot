# -*- coding: utf-8 -*-

# Admin plugin for t2jrbot.
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

import t2jrbot

class _AdminPlugin(object):

    def __init__(self, bot, admins, command_whitelist):
        self.__bot = bot

        self.__admins = set([self.__parse_admin_arg(a) for a in admins])
        self.__command_whitelist = set(command_whitelist)

        command_plugin = self.__bot.plugins["t2jrbot.plugins.command"]

        command_plugin.add_pre_eval_hook(self.__check_auth)

        command_plugin.register_command("!admin_list",
                                        self.__command_admin_list,
                                        "List bot admins. Usage: !admin_list")

        command_plugin.register_command("!admin_add",
                                        self.__command_admin_add,
                                        "Add a bot admin. "
                                        "Usage: !admin_add NICK!USER@HOST, "
                                        "e.g. !admin_add fanatic!fan.atic@example.org")

        command_plugin.register_command("!admin_remove",
                                        self.__command_admin_remove,
                                        "Remove a bot admin. "
                                        "Usage: !admin_remove NICK!USER@HOST, "
                                        "e.g. !admin_remove fanatic!fan.atic@example.org")

    def __check_auth(self, nick, host, channel, command, argstr):
        if ((command in self.__command_whitelist)
            or
            ((nick, host) in self.__admins)):
            return True

        self.__bot.irc.send_privmsg(channel,
                                    "%s: only admins are allowed to %s" % (nick, command))

        return False

    def __command_admin_list(self, nick, host, channel, this_command, argstr):
        admins = ["%s!%s" % (nick, host) for nick, host in self.__admins]
        self.__bot.irc.send_privmsg(channel, "%s: %s" % (nick, " ".join(admins)))

    def __command_admin_add(self, nick, host, channel, this_command, argstr):
        admin_nick, admin_host = self.__parse_admin_arg(argstr)
        self.__admins.add((admin_nick, admin_host))

    def __command_admin_remove(self, nick, host, channel, this_command, argstr):
        admin_nick, admin_host = self.__parse_admin_arg(argstr)
        self.__admins.discard((admin_nick, admin_host))

    def __parse_admin_arg(self, admin):
        admin_nick, sep, admin_host = admin.partition("!")
        admin_nick = admin_nick.strip()
        admin_host = admin_host.strip()
        if not admin_nick or not sep or not admin_host:
            raise ValueError("malformed admin identifier, should "
                             "be of form 'nick!user@example.org'")
        return admin_nick, admin_host

def validate_conf(conf):
    unknown_keys = set(conf.keys()) - set(["admins", "command_whitelist"])
    if unknown_keys:
        raise t2jrbot.ConfError("unknown keys: %s" %
                                ", ".join([repr(s) for s in unknown_keys]))

    try:
        admins = conf["admins"]
    except KeyError:
        pass # Ok, optional key.
    else:
        if not isinstance(admins, list):
            raise t2jrbot.ConfError("invalid 'admins' key, expected list")
        for admin in admins:
            if not isinstance(admin, str):
                raise t2jrbot.ConfError("invalid admin '%s', "
                                        "expected string" % admin)

    try:
        command_whitelist = conf["command_whitelist"]
    except KeyError:
        pass # Ok, optional key.
    else:
        if not isinstance(command_whitelist, list):
            raise t2jrbot.ConfError("invalid 'command_whitelist' key, expected list")
        for command in command_whitelist:
            if not isinstance(command, str):
                raise t2jrbot.ConfError("invalid command '%s', "
                                        "expected string" % command)


def load(bot, conf):
    validate_conf(conf)

    admins = conf.get("admins", [])
    command_whitelist = conf.get("command_whitelist", [])

    return _AdminPlugin(bot, admins, command_whitelist)
