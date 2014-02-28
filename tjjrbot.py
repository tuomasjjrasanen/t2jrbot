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

import select
import socket
import sys

MAX_SEND_LEN = 510

def recv(sock):
    msg = sock.recv(512)
    print(msg, end="")
    return msg

def handle_msg(sock, msg):
    if msg_tail.startswith("PING "):
        ping_server = msg_tail.split()[1]
        send_pong(sock, ping_server)

def send(sock, msg):
    msg = "%s\r\n" % msg[:MAX_SEND_LEN]
    print(msg, end="")
    sock.send(msg)

def send_join(sock, channel):
    send(sock, "JOIN %s" % channel)

def send_nick(sock, nick):
    send(sock, "NICK %s" % nick)

def send_pong(sock, ping_server):
    send(sock, "PONG %s" % ping_server)

def send_privmsg(sock, target, text):
    head = "PRIVMSG %s :" % target
    max_tail_len = MAX_SEND_LEN - len(head)

    i = 0
    while i < len(text):
        tail = text[i:i+max_tail_len]
        send("%s%s" % (head, tail))
        i += len(tail)

def send_user(sock, user, mode=8, realname=None):
    if realname is None:
        realname = user
    send(sock, "USER %s %d * :%s" % (user, mode, realname))

def main(nick, channel, server, port=6667):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((server, port))

    send_user(sock, nick)
    send_nick(sock, nick)
    send_join(sock, channel)

    while True:
        rs, ws, es = select.select([sock, sys.stdin], [], [])

        if sock in rs:
            msg = recv(sock)
            handle_msg(sock, msg)

        # All 
        if sys.stdin in rs:
            send_privmsg(sock, channel, sys.stdin.readline())

if __name__ == "__main__":
    main("tjjrbot", "#tjjrtjjr", "irc.elisa.fi")
