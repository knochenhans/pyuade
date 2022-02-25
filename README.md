# PyUADE

*A retro music player using UADE (Unix Amiga Delitracker Emulator) as its back end*

This is mainly a personal project for now. I started working on this because there I found no other convenient way to play a huge library of all kinds of retro tunes under Linux besides the ages old and cumbersome Deli Player 2 in WINE. My player of choice would be Foobar2000, but it’s not open source and doesn’t natively run under Linux. I was looking for a project to get some more Python experience so I started PyUADE. My goal is to build a minimalistic music player that doesn’t get in the way and specializes in playing retro formats.

This only runs under Linux for now.

Dependencies:
- libuade
- libao (I’m planning to switch to a pure Python library sooner or later)
- libbencode (bencode-tools)
- [Python requirements](requirements.txt)

![screenshot](https://user-images.githubusercontent.com/5293125/155572697-cf70b894-14d4-4ce8-8e8c-ffd813df8694.png)
