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

import datetime
import importlib
import select
import socket
import sys

MAX_MSG_LEN = 510
CRLF = "\r\n"

class Error(Exception):
    pass

class Bot(object):

    def __init__(self, server, port, nick, channel):
        self.__server = server
        self.__port = port
        self.__nick = nick
        self.__channel = channel
        self.__admins = set()
        self.__recvbuf = ""
        self.__sock = None
        self.__botcmd_handlers = {}
        self.__botcmd_descriptions = {}
        self.__admin_botcmds = set()
        self.__quit_reason = ""
        self.__is_stopping = False
        self.__plugins = {}
        self.__plugin_dirs = set()

        self.__recv_ircmsg_cbs_index_map = {}
        self.__recv_ircmsg_cbs = []

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.add_ircmsg_rx_cb(self.__recv_ircmsg_error, irccmd="ERROR")
        self.add_ircmsg_rx_cb(self.__recv_ircmsg_ping, irccmd="PING")
        self.add_ircmsg_rx_cb(self.__recv_ircmsg_privmsg, irccmd="PRIVMSG")
        self.add_ircmsg_rx_cb(self.__recv_ircmsg_001, irccmd="001")

    @property
    def admins(self):
        return set(self.__admins)

    @property
    def botcmd_descriptions(self):
        return dict(self.__botcmd_descriptions)

    def add_admin(self, nick, host):
        self.__admins.add((nick, host))

    def remove_admin(self, nick, host):
        self.__admins.discard((nick, host))

    def quit(self, reason=""):
        # The actual quit is postponed until the main loop has finished.
        self.__quit_reason = reason
        self.__is_stopping = True

    def add_ircmsg_rx_cb(self, cb, prefix=None, irccmd=None):
        """Add a callable to the list of IRC RX callbacks.

        The callback `cb` will be called whenever an IRC message
        matching given `prefix` and `irccmd` has been received. If
        `prefix` and/or `irccmd` is None, they are treated as wildcards
        matching any value.

        Callbacks are called in the order they added to the list.

        """
        i = len(self.__recv_ircmsg_cbs)
        self.__recv_ircmsg_cbs.append(cb)
        key = (prefix, irccmd)
        indices = self.__recv_ircmsg_cbs_index_map.setdefault(key, [])
        indices.append(i)

    def register_botcmd(self, botcmd, handler, description="", require_admin=True):
        if botcmd in self.__botcmd_handlers:
            raise Error("command '%s' is already registered" % botcmd)
        self.__botcmd_handlers[botcmd] = handler
        self.__botcmd_descriptions[botcmd] = description
        if require_admin:
            self.__admin_botcmds.add(botcmd)

    def unregister_botcmd(self, botcmd):
        try:
            del self.__botcmd_handlers[botcmd]
        except KeyError:
            raise Error("command '%s' is not registered" % botcmd)
        del self.__botcmd_descriptions[botcmd]
        self.__admin_botcmds.discard(botcmd)

    def run(self):
        self.__sock.connect((self.__server, self.__port))
        try:
            # Register connection.
            self.send_ircmsg("NICK %s" % self.__nick)
            self.send_ircmsg("USER %s 0 * :%s" % (self.__nick, self.__nick))

            while not self.__is_stopping:
                rs, _, _ = select.select([self.__sock], [], [])

                # Read socket buffer, parse messages and handle them.
                self.__recv_ircmsgs()

            quit_msg = "QUIT"
            if self.__quit_reason:
                quit_msg += " :%s" % self.__quit_reason
            self.send_ircmsg(quit_msg)

        finally:
            self.__sock.shutdown(socket.SHUT_RDWR)

    def send_ircmsg_privmsg(self, target, text):
        head = "PRIVMSG %s :" % target
        max_tail_len = MAX_MSG_LEN - len(head)

        i = 0
        while i < len(text):
            tail = text[i:i+max_tail_len]
            self.send_ircmsg("%s%s" % (head, tail))
            i += len(tail)

    def add_plugin_dir(self, plugin_dir):
        self.__plugin_dirs.add(plugin_dir)

    def load_plugin(self, plugin_name):
        if plugin_name in self.__plugins:
            return False

        orig_sys_path = list(sys.path)
        try:
            sys.path.extend(self.__plugin_dirs)
            plugin = importlib.import_module(plugin_name)
            del sys.modules[plugin_name]

            plugin.load(self)

            self.__plugins[plugin_name] = plugin
        finally:
            sys.path = orig_sys_path

        return True

    def send_ircmsg(self, msg):
        if len(msg) > MAX_MSG_LEN:
            raise Error("message is too long to send", len(msg))
        self.__log("=>IRC", msg)
        self.__sock.sendall("%s%s" % (msg, CRLF))

    def __recv_ircmsgs(self):
        recvbuf = self.__sock.recv(4096)
        if not recvbuf:
            raise Error("receive failed, connection reset by peer")

        # Concatenate old and new bufs.
        self.__recvbuf += recvbuf

        while True:
            msg, sep, self.__recvbuf = self.__recvbuf.partition(CRLF)
            if sep != CRLF:
                # Save the incomplete msg for later concatenation.
                self.__recvbuf = msg
                break
            self.__log("<=IRC", msg)

            self.__recv_ircmsg(msg)

    def __recv_ircmsg(self, msg):
        prefix = ""

        if msg.startswith(":"):
            prefix, sep, msg = msg.partition(" ")
            prefix = prefix[1:]
            if sep != " ":
                raise Error("received message has malformed prefix", sep)

        irccmd, _, paramstr = msg.partition(" ")

        params = []
        while paramstr:
            if paramstr.startswith(":"):
                param = paramstr[1:]
                paramstr = ""
            else:
                param, _, paramstr = paramstr.partition(" ")
            params.append(param)

        cb_indices = set()

        cb_indices.update(self.__recv_ircmsg_cbs_index_map.get((None, None), set()),
                          self.__recv_ircmsg_cbs_index_map.get((prefix, None), set()),
                          self.__recv_ircmsg_cbs_index_map.get((None, irccmd), set()),
                          self.__recv_ircmsg_cbs_index_map.get((prefix, irccmd), set()))

        for cb_index in sorted(cb_indices):
            cb = self.__recv_ircmsg_cbs[cb_index]
            cb(self, prefix, irccmd, params)

    def __recv_ircmsg_privmsg(self, prefix, target, text):
        nick, sep, host = prefix.partition("!")

        if target == self.__nick:
            # User-private messages are not supported and are silently
            # ignored.
            return

        channel = target

        # Ignore all leading whitespaces.
        text = text.lstrip()

        if not text.startswith("%s:" % self.__nick):
            # The message is not designated to me, ignore.
            return

        # Strip my nick from the beginning of the text.
        botcmdstr = text[len("%s:" % self.__nick):].lstrip()

        botcmd, _, argstr = botcmdstr.partition(' ')
        try:
            botcmd_handler = self.__botcmd_handlers[botcmd]
        except KeyError:
            # Silently ignore all but commands.
            return

        if not self.__admin_check(nick, host, botcmd):
            self.send_ircmsg_privmsg(channel,
                                     "%s: only admins are allowed to %s"
                                     % (nick, botcmd))
            return

        try:
            botcmd_handler(self, nick, host, channel, botcmd, argstr)
        except Exception, e:
            self.send_ircmsg_privmsg(channel,
                                     "%s: error: %s" % (nick, e.message))

    def __recv_ircmsg_error(self, prefix, this_irccmd, params):
        raise Error("received ERROR from the server", params)

    def __recv_ircmsg_ping(self, prefix, this_irccmd, params):
        self.send_ircmsg("PONG %s" % self.__nick)

    def __recv_ircmsg_001(self, prefix, this_irccmd, params):
        # Update the nick after successful connection because
        # the server might have truncated or otherwise modified
        # the nick we requested.
        self.__nick = params[0]
        self.send_ircmsg("JOIN %s" % self.__channel)

    def __admin_check(self, nick, host, botcmd):
        if botcmd not in self.__admin_botcmds:
            return True

        return (nick, host) in self.__admins

    def __log(self, name, msg):
        timestamp = datetime.datetime.utcnow().isoformat()
        print(timestamp, name, msg)

    def __del__(self):
        self.__sock.close()
