# -*- coding: utf-8 -*-

# Topic plugin for t2jrbot.
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

import t2jrbot.conf

class _TopicPlugin(object):

    def __init__(self, bot, log_length):
        self.__bot = bot
        self.__topic_logs = {} # Maps channels to lists of topics.
        self.__log_length = log_length

        self.__bot.add_irc_callback(self.__irc_topic_callback, command="TOPIC")

        command_plugin = self.__bot.plugins["t2jrbot.plugins.command"]
        command_plugin.register_command("!topic_log", self.__command_topic_log,
                                        "Show the topic log. Usage: !topic_log")
        command_plugin.register_command("!topic_reset", self.__command_topic_reset,
                                        "Reset the current topic to the topic "
                                        "of the specified log entry. "
                                        "Usage: !topic_reset NUMBER")

    def release(self):
        pass

    def __irc_topic_callback(self, prefix, cmd, params):
        nick, sep, host = prefix.partition("!")
        if nick == self.__bot.nick:
            # Do not log topics set by the bot, because it would
            # unnecessarily overwrite real entries. All topics set by
            # the bot are already in the log. 
            #
            # NOTE: This might change if other topic setting commands
            # gets implemented.
            return
        channel, topic = params
        topic_log = self.__topic_logs.setdefault(channel, [])
        topic_log.insert(0, topic)
        del topic_log[self.__log_length:]

    def __command_topic_log(self, nick, host, channel, command, argstr):
        try:
            topic_log = self.__topic_logs[channel]
        except KeyError:
            self.__bot.irc.send_privmsg(channel, "%s: Topic log is empty." % nick)
            return
        for i, topic in enumerate(topic_log, 1):
            self.__bot.irc.send_privmsg(channel, "%s: %d: %s" % (nick, i, topic))

    def __command_topic_reset(self, nick, host, channel, command, argstr):
        try:
            topic_log = self.__topic_logs[channel]
        except KeyError:
            self.__bot.irc.send_privmsg(channel, "%s: Topic log is empty." % nick)
            return

        try:
            number = int(argstr)
        except ValueError:
            self.__bot.irc.send_privmsg(channel,
                                        "%s: Invalid log entry number." % nick)
            return

        if not 0 < number <= len(topic_log):
            self.__bot.irc.send_privmsg(channel,
                                        "%s: Invalid log entry number." % nick)
            return

        i = number - 1
        topic = topic_log[i]
        self.__bot.irc.send_topic(channel, topic)

def check_conf(conf):
    t2jrbot.conf.check_keys(conf, ["log_length"])

    t2jrbot.conf.check_value(conf, "log_length",
                             lambda v: isinstance(v, int) and v >= 0)

def load(bot, conf):
    check_conf(conf)

    log_length = conf.get("log_length", 3)

    return _TopicPlugin(bot, log_length)
