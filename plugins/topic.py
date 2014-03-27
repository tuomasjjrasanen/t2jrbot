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

MAX_TOPIC_LOG_LEN = 3
topic_logs = {}

def recv_ircmsg_topic(bot, prefix, cmd, params):
    channel, topic = params
    nick, sep, host = prefix.partition("!")
    topic_log = topic_logs.setdefault(channel, [])
    topic_log.insert(0, topic)
    if len(topic_log) > MAX_TOPIC_LOG_LEN:
        oldest_topic = topic_log.pop()

def topic_log(bot, nick, host, channel, command, argstr):
    try:
        topic_log = topic_logs[channel]
    except KeyError:
        bot.irc.send_privmsg(channel, "%s: Topic log is empty." % nick)
        return
    for i, topic in enumerate(topic_log):
        bot.irc.send_privmsg(channel, "%s: %d: %s" % (nick, i, topic))

def load(bot):
    bot.add_ircmsg_rx_cb(recv_ircmsg_topic, irccmd="TOPIC")
    bot.register_botcmd("!topic_log", topic_log,
                        "Show the topic log. Usage: !topic_log", False)
