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

class _TopicPlugin(object):

    def __init__(self, bot, max_topic_log_len):
        self.__bot = bot
        self.__topic_logs = {} # Maps channels to lists of topics.
        self.__max_topic_log_len = max_topic_log_len

        self.__bot.add_irc_callback(self.__irc_topic_callback, command="TOPIC")

        command_plugin = self.__bot.plugins["t2jrbot.plugins.command"]
        command_plugin.register_command("!topic_log", self.__command_topic_log,
                                        "Show the topic log. Usage: !topic_log")

    def __irc_topic_callback(self, prefix, cmd, params):
        channel, topic = params
        nick, sep, host = prefix.partition("!")
        topic_log = self.__topic_logs.setdefault(channel, [])
        topic_log.insert(0, topic)
        del topic_log[self.__max_topic_log_len:]

    def __command_topic_log(self, nick, host, channel, command, argstr):
        try:
            topic_log = self.__topic_logs[channel]
        except KeyError:
            self.__bot.irc.send_privmsg(channel, "%s: Topic log is empty." % nick)
            return
        for i, topic in enumerate(topic_log):
            self.__bot.irc.send_privmsg(channel, "%s: %d: %s" % (nick, i, topic))

def load(bot, conf):
    max_topic_log_len = conf.get("max_topic_log_len", 3)
    return _TopicPlugin(bot, max_topic_log_len)
