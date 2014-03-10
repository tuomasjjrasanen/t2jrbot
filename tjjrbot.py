#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tjjrbot - simple but elegant IRC bot
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

from __future__ import print_function

import datetime
import select
import socket
import sys

MAX_MSG_LEN = 510
CRLF = "\r\n"

class Error(Exception):
    pass

class Bot(object):

    def __init__(self, server, port, nick, channel, logfile=sys.stdout):
        self.__server = server
        self.__port = port
        self.__nick = nick
        self.__channel = channel
        self.__logfile = logfile
        self.__admins = set()
        self.__recvbuf = ""
        self.__sock = None
        self.__botcmd_handlers = {}
        self.__botcmd_descriptions = {}
        self.__admin_botcmds = set()

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @property
    def admins(self):
        return set(self.__admins)

    @property
    def command_descriptions(self):
        return dict(self.__botcmd_descriptions)

    def add_admin(self, nick, host):
        self.__admins.add((nick, host))

    def register_command(self, cmd, handler, description="", require_admin=True):
        if cmd in self.__botcmd_handlers:
            raise Error("command is already registered")
        self.__botcmd_handlers[cmd] = handler
        self.__botcmd_descriptions[cmd] = description
        if require_admin:
            self.__admin_botcmds.add(cmd)

    def run(self):
        self.__sock.connect((self.__server, self.__port))
        try:
            # Register connection.
            self.__send_ircmsg("NICK %s" % self.__nick)
            self.__send_ircmsg("USER %s 0 * :%s" % (self.__nick, self.__nick))

            while True:
                rs, _, _ = select.select([self.__sock], [], [])

                # Read socket buffer, parse messages and handle them.
                self.__recv_ircmsgs()

        finally:
            self.__sock.shutdown(socket.SHUT_RDWR)

    def send_ircmsg_privmsg(self, target, text):
        head = "PRIVMSG %s :" % target
        max_tail_len = MAX_MSG_LEN - len(head)

        i = 0
        while i < len(text):
            tail = text[i:i+max_tail_len]
            self.__send_ircmsg("%s%s" % (head, tail))
            i += len(tail)

    def __send_ircmsg(self, msg):
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

            prefix = ""

            if msg.startswith(":"):
                prefix, sep, msg = msg.partition(" ")
                prefix = prefix[1:]
                if sep != " ":
                    raise Error("received message has malformed prefix", sep)

            cmd, _, paramstr = msg.partition(" ")

            params = []
            while paramstr:
                if paramstr.startswith(":"):
                    param = paramstr[1:]
                    paramstr = ""
                else:
                    param, _, paramstr = paramstr.partition(" ")
                params.append(param)

            if cmd == "ERROR":
                raise Error("received ERROR from the server", params)

            elif cmd == "PING":
                self.__send_ircmsg("PONG %s" % self.__nick)

            elif cmd == "PRIVMSG":
                self.__recv_ircmsg_privmsg(prefix, *params)

            elif cmd == "001":
                self.__send_ircmsg("JOIN %s" % self.__channel)

            elif cmd == "JOIN":
                self.send_ircmsg_privmsg(self.__channel,
                                           "USAGE: %s: !help" % self.__nick)

    def __recv_ircmsg_privmsg(self, prefix, target, text):
        nick, sep, host = prefix.partition("!")

        if target == self.__nick:
            # User-private messages are not supported and are silently
            # ignored.
            return

        self.__recv_ircmsg_privmsg_chan(nick, host, text)

    def __recv_ircmsg_privmsg_chan(self, nick, host, text):
        # Ignore all leading whitespaces.
        text = text.lstrip()

        if not text.startswith("%s:" % self.__nick):
            # The message is not designated to me, ignore.
            return

        # Strip my nick from the beginning of the text.
        cmdstr = text[len("%s:" % self.__nick):].lstrip()

        cmd, _, argstr = cmdstr.partition(' ')
        try:
            botcmd_handler = self.__botcmd_handlers[cmd]
        except KeyError:
            # Silently ignore all but commands.
            return

        if not self.__admin_check(nick, host, cmd):
            self.send_ircmsg_privmsg(self.__channel,
                                       "%s: only admin is allowed to %s"
                                       % (nick, cmd))
            return

        botcmd_handler(self, nick, host, self.__channel, cmd, argstr)

    def __admin_check(self, nick, host, cmd):
        if cmd not in self.__admin_botcmds:
            return True

        return (nick, host) in self.__admins

    def __log(self, name, msg):
        timestamp = datetime.datetime.utcnow().isoformat()
        print(timestamp, name, msg, file=self.__logfile)

    def __del__(self):
        self.__sock.close()

def command_help(bot, nick, host, channel, command, argstr):
    bot.send_ircmsg_privmsg(channel, "%s: List of commands:" % nick)
    for cmd, descr in bot.command_descriptions.items():
        bot.send_ircmsg_privmsg(channel, "%s: %s - %s" % (nick, cmd, descr))

def command_say(bot, nick, host, channel, command, argstr):
    bot.send_ircmsg_privmsg(channel, argstr)
    bot.send_ircmsg_privmsg(channel, "-- %s" % nick)

def main():
    bot = Bot("irc.elisa.fi", 6667, "tjjrbot", "#tjjrtjjr")
    bot.register_command("!help", command_help, "show help", require_admin=False)
    bot.register_command("!say", command_say, "say something to the channel")
    bot.run()

if __name__ == "__main__":
    main()
