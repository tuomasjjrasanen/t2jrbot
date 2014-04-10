# -*- coding: utf-8 -*-

# Pong plugin for t2jrbot.
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

class _PongPlugin(object):

    def __init__(self, bot):
        self.__bot = bot

        self.__bot.add_irc_callback(self.__irc_ping, command="PING")

    def __irc_ping(self, prefix, this_command, params):
        self.__bot.irc.send_pong(self.__bot.nick)

def validate_conf(conf):
    t2jrbot.conf.validate_keys(conf, ())

def load(bot, conf):
    validate_conf(conf)

    return _PongPlugin(bot)
