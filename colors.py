#!/usr/bin/python

names = ['Red', 'Green', 'Yellow', 'Blue', 'Magenta', 'Cyan']
colors = range(31, 37)  # ANSI escape codes for color
for name, color in zip(names, colors):
    print u'\033[0;{}m{}  {}\033[0m'.format(color, 5*u'\u2588', name)