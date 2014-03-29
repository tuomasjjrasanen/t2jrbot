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

CRLF = "\r\n"

class Error(Exception):
    pass

class IRC(object):

    MAX_MSG_LEN = 510

    def __init__(self):
        self.__recvbuf = ""
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, server, port):
        self.__sock.connect((server, port))

    def fileno(self):
        return self.__sock.fileno()

    def __recv(self, msg):
        prefix = ""

        if msg.startswith(":"):
            prefix, sep, msg = msg.partition(" ")
            prefix = prefix[1:]
            if sep != " ":
                raise Error("received message has malformed prefix", sep)

        command, _, paramstr = msg.partition(" ")

        params = []
        while paramstr:
            if paramstr.startswith(":"):
                param = paramstr[1:]
                paramstr = ""
            else:
                param, _, paramstr = paramstr.partition(" ")
            params.append(param)

        return prefix, command, params

    def recv(self):
        retval = []

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

            retval.append(self.__recv(msg))

        return retval

    def send(self, msg):
        if len(msg) > IRC.MAX_MSG_LEN:
            raise Error("message is too long to send", len(msg))
        self.__log("=>IRC", msg)
        self.__sock.sendall("%s%s" % (msg, CRLF))

    def send_join(self, channel):
        self.send("JOIN %s" % channel)

    def send_nick(self, nick):
        self.send("NICK %s" % nick)

    def send_pong(self, nick):
        self.send("PONG %s" % nick)

    def send_privmsg(self, target, text):
        head = "PRIVMSG %s :" % target
        max_tail_len = IRC.MAX_MSG_LEN - len(head)

        i = 0
        while i < len(text):
            tail = text[i:i+max_tail_len]
            self.send("%s%s" % (head, tail))
            i += len(tail)

    def send_quit(self, reason):
        quit_msg = "QUIT"
        if reason:
            quit_msg += " :%s" % reason
        self.send(quit_msg)

    def send_user(self, user, realname):
        self.send("USER %s 0 * :%s" % (user, realname))

    def shutdown(self):
        self.__sock.shutdown(socket.SHUT_RDWR)

    def __log(self, name, msg):
        timestamp = datetime.datetime.utcnow().isoformat()
        print(timestamp, name, msg)

class Bot(object):

    def __init__(self, server, port, nick):
        self.__server = server
        self.__port = port
        self.irc = IRC()
        self.nick = nick
        self.__admins = set()
        self.__command_handlers = {}
        self.__command_descriptions = {}
        self.__admin_commands = set()
        self.__quit_reason = ""
        self.__is_stopping = False
        self.__plugins = {}
        self.__plugin_dirs = set()

        self.__irc_callbacks_index_map = {}
        self.__irc_callbacks = []

    @property
    def admins(self):
        return set(self.__admins)

    @property
    def command_descriptions(self):
        return dict(self.__command_descriptions)

    def add_admin(self, nick, host):
        self.__admins.add((nick, host))

    def remove_admin(self, nick, host):
        self.__admins.discard((nick, host))

    def quit(self, reason=""):
        # The actual quit is postponed until the main loop has finished.
        self.__quit_reason = reason
        self.__is_stopping = True

    def add_irc_callback(self, callback, prefix=None, irccmd=None):
        """Add a callable to the list of IRC RX callbacks.

        The callback `callback` will be called whenever an IRC message
        matching given `prefix` and `irccmd` has been received. If
        `prefix` and/or `irccmd` is None, they are treated as wildcards
        matching any value.

        Callbacks are called in the order they added to the list.

        """
        i = len(self.__irc_callbacks)
        self.__irc_callbacks.append(callback)
        key = (prefix, irccmd)
        indices = self.__irc_callbacks_index_map.setdefault(key, [])
        indices.append(i)

    def register_command(self, command, handler, description="", require_admin=True):
        if command in self.__command_handlers:
            raise Error("command '%s' is already registered" % command)
        self.__command_handlers[command] = handler
        self.__command_descriptions[command] = description
        if require_admin:
            self.__admin_commands.add(command)

    def unregister_command(self, command):
        try:
            del self.__command_handlers[command]
        except KeyError:
            raise Error("command '%s' is not registered" % command)
        del self.__command_descriptions[command]
        self.__admin_commands.discard(command)

    def run(self):
        self.irc.connect(self.__server, self.__port)

        try:
            # Register connection.
            self.irc.send_nick(self.nick)
            self.irc.send_user(self.nick, self.nick)

            while not self.__is_stopping:
                rs, _, _ = select.select([self.irc], [], [])

                # Read socket buffer, parse messages and handle them.
                messages = self.irc.recv()

                for prefix, irccmd, params in messages:
                    callback_indices = set()

                    callback_indices.update(
                        self.__irc_callbacks_index_map.get((None, None), set()),
                        self.__irc_callbacks_index_map.get((prefix, None), set()),
                        self.__irc_callbacks_index_map.get((None, irccmd), set()),
                        self.__irc_callbacks_index_map.get((prefix, irccmd), set()))

                    for callback_index in sorted(callback_indices):
                        callback = self.__irc_callbacks[callback_index]
                        callback(self, prefix, irccmd, params)

            self.irc.send_quit(self.__quit_reason)
        finally:
            self.irc.shutdown()

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

    def eval_command(self, nick, host, channel, command, argstr):
        try:
            command_handler = self.__command_handlers[command]
        except KeyError:
            # Silently ignore all input except registered commands.
            return

        if not self.admin_check(nick, host, command):
            self.irc.send_privmsg(channel,
                                  "%s: only admins are allowed to %s"
                                  % (nick, command))
            return

        try:
            command_handler(self, nick, host, channel, command, argstr)
        except Exception, e:
            self.irc.send_privmsg(channel,
                                  "%s: error: %s" % (nick, e.message))

    def admin_check(self, nick, host, command):
        if command not in self.__admin_commands:
            return True

        return (nick, host) in self.__admins
