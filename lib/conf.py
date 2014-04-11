# -*- coding: utf-8 -*-

# t2jrbot - simple but elegant IRC bot
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

def check_keys(conf, valid_keys):
    unknown_keys = set(conf.keys()) - set(valid_keys)
    if unknown_keys:
        raise t2jrbot.ConfError("unknown keys: %s" %
                                ", ".join([repr(s) for s in unknown_keys]))

def check_value(conf, key, valid_value, required=True):
    try:
        value = conf[key]
    except KeyError:
        if required:
            raise t2jrbot.ConfError("required key '%s' is missing" % key)
    else:
        if not valid_value(value):
            raise t2jrbot.ConfError("key '%s' has invalid value" % key)
