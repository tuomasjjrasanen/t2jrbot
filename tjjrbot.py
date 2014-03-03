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
import time

MAX_MSG_LEN = 510
CRLF = "\r\n"

class Error(Exception):
    pass

class Bot(object):

    def __init__(self, **kwargs):
        self.__channel = kwargs.get("channel")
        self.__registration_timeout = kwargs.get("registration_timeout", 0)
        self.__nick = kwargs["nick"]
        self.__port = kwargs["port"]
        self.__server = kwargs["server"]
        self.__logfile=kwargs.get("logfile", sys.stdout)

        self.__oldbuf = ""
        self.__ircmsgs = []
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __log(self, name, msg):
        timestamp = datetime.datetime.utcnow().isoformat()
        print(timestamp, name, msg, file=self.__logfile)

    def __recv_ircmsgs(self):
        # Concatenate old and new bufs.
        buf = self.__oldbuf + self.__sock.recv(4096)

        while True:
            msg, sep, buf = buf.partition(CRLF)
            if sep != CRLF:
                # Save the incomplete msg for later concatenation.
                self.__oldbuf = msg
                break
            self.__log("IRC", msg)

            prefix = ""

            if msg.startswith(":"):
                prefix, sep, msg = msg.partition(" ")
                if sep != " ":
                    raise Error("malformed prefixed message")

            cmd, _, params = msg.partition(" ")

            self.__ircmsgs.append((prefix, cmd, params))

    def __handle_ircmsgs(self):
        while self.__ircmsgs:
            prefix, cmd, params = self.__ircmsgs.pop()

            if cmd == "ERROR":
                raise Error(params)

            elif cmd == "PING":
                self.__send_ircmsg("PONG %s" % self.__nick)

    def __send_ircmsg(self, msg):
        if len(msg) > MAX_MSG_LEN:
            raise Error("message is too long")
        self.__log("IRC", msg)
        self.__sock.sendall("%s%s" % (msg, CRLF))

    def __send_ircmsg_privmsg(self, text):
        head = "PRIVMSG %s :" % self.__channel
        max_tail_len = MAX_MSG_LEN - len(head)

        i = 0
        while i < len(text):
            tail = text[i:i+max_tail_len]
            self.__send_ircmsg("%s%s" % (head, tail))
            i += len(tail)

    def __wait_ircrpl(self, expected_cmd, timeout=None):
        next_timeout = timeout
        start_time = time.time()
        while True:
            rs, ws, es = select.select([self.__sock], [], [], next_timeout)

            # Timeout
            if rs == ws == es == []:
                return False

            if timeout is not None:
                next_timeout = max(0, start_time + timeout - time.time())

            self.__recv_ircmsgs()
            for _, cmd, _ in self.__ircmsgs:
                if cmd == expected_cmd:
                    return True

        raise RuntimeError("impossible code path")

    def __del__(self):
        self.__sock.close()

    def start(self):
        self.__sock.connect((self.__server, self.__port))
        try:
            start_time = time.time()

            # Register connection.
            self.__send_ircmsg("NICK %s" % self.__nick)
            self.__send_ircmsg("USER %s 0 * :%s" % (self.__nick, self.__nick))
            if not self.__wait_ircrpl("001", timeout=self.__registration_timeout):
                raise Error("connection registration timeout")

            while True:
                rs, _, _ = select.select([self.__sock], [], [], 1)

                # Handle messages server has sent to us.
                if self.__sock in rs:
                    # Read socket buffer, parse messages and push them
                    # to the message buffer.
                    self.__recv_ircmsgs()

                    # Handle messages in the message buffer.
                    self.__handle_ircmsgs()

        finally:
            self.__sock.shutdown(socket.SHUT_RDWR)

def main():
    bot = Bot(
        server="irc.elisa.fi",
        port=6667,
        nick="tjjrbot",
        channel="#tjjrbot",
        registration_timeout=60,
        logfile=open("tjjrbot.log", "a", 1),
    )
    bot.start()

if __name__ == "__main__":
    main()
