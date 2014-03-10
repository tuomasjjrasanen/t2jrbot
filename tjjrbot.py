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

    def __init__(self, **kwargs):
        self.__nick = kwargs["nick"]
        self.__port = kwargs["port"]
        self.__server = kwargs["server"]
        self.__channel = kwargs["channel"]
        self.__logfile=kwargs.get("logfile", sys.stdout)
        self.__admins = kwargs.get("admins", ())

        self.__oldbuf = ""
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__botcmds = {
            "!help": (self.__botcmd_help, "show help"),
            "!say": (self.__botcmd_say, "say something to the channel"),
        }

        self.__admin_botcmds = (
            "!say",
        )

    def start(self):
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

    def __send_ircmsg(self, msg):
        if len(msg) > MAX_MSG_LEN:
            raise Error("message is too long to send", len(msg))
        self.__log("=>IRC", msg)
        self.__sock.sendall("%s%s" % (msg, CRLF))

    def send_ircmsg_privmsg(self, target, text):
        head = "PRIVMSG %s :" % target
        max_tail_len = MAX_MSG_LEN - len(head)

        i = 0
        while i < len(text):
            tail = text[i:i+max_tail_len]
            self.__send_ircmsg("%s%s" % (head, tail))
            i += len(tail)

    def __recv_ircmsgs(self):
        newbuf = self.__sock.recv(4096)
        if not newbuf:
            raise Error("receive failed, connection reset by peer")

        # Concatenate old and new bufs.
        buf = self.__oldbuf + newbuf

        while True:
            msg, sep, buf = buf.partition(CRLF)
            if sep != CRLF:
                # Save the incomplete msg for later concatenation.
                self.__oldbuf = msg
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
            botcmd, _ = self.__botcmds[cmd]
        except KeyError:
            # Silently ignore all but commands.
            return

        if not self.__admin_check(nick, host, cmd):
            self.send_ircmsg_privmsg(self.__channel,
                                       "%s: only admin is allowed to %s"
                                       % (nick, cmd))
            return

        botcmd(nick, host, cmd, argstr)

    def __botcmd_help(self, nick, host, cmd, argstr):
        self.send_ircmsg_privmsg(self.__channel,
                                   "%s: List of commands:" % nick)
        for name in self.__botcmds:
            _, description = self.__botcmds[name]
            self.send_ircmsg_privmsg(self.__channel,
                                       "%s: %s - %s"
                                       % (nick, name, description))

    def __botcmd_say(self, nick, host, cmd, argstr):
        self.send_ircmsg_privmsg(self.__channel, argstr)
        self.send_ircmsg_privmsg(self.__channel, "-- %s" % nick)

    def __admin_check(self, nick, host, cmd):
        if cmd not in self.__admin_botcmds:
            return True

        for admin_nick, admin_host in self.__admins:
            if nick == admin_nick and host == admin_host:
                return True

        return False

    def __log(self, name, msg):
        timestamp = datetime.datetime.utcnow().isoformat()
        print(timestamp, name, msg, file=self.__logfile)

    def __del__(self):
        self.__sock.close()

def main():
    bot = Bot(
        server="irc.elisa.fi",
        port=6667,
        nick="tjjrbot",
        channel="#tjjrtjjr",
        logfile=open("tjjrbot.log", "a", 1),
    )
    bot.start()

if __name__ == "__main__":
    main()
