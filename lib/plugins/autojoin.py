# -*- coding: utf-8 -*-

# Autojoin plugin for t2jrbot.
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

class _AutojoinPlugin(object):

    def __init__(self, bot, channel):
        self.__bot = bot
        self.__channel = channel

        self.__bot.add_irc_callback(self.__irc_001, command="001")

    def __irc_001(self, prefix, this_command, params):
        # Update the nick after successful connection because
        # the server might have truncated or otherwise modified
        # the nick we requested.
        self.__bot.nick = params[0]
        self.__bot.irc.send_join(self.__channel)

def check_conf(conf):
    t2jrbot.conf.check_keys(conf, ["channel"])

    t2jrbot.conf.check_value(conf, "channel",
                             lambda v: isinstance(v, str))

def load(bot, conf):
    check_conf(conf)

    channel = conf["channel"]

    return _AutojoinPlugin(bot, channel)
