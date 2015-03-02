#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  _
# /   _  | |  _   _ _|_ o  _  ._
# \_ (_) | | (/_ (_  |_ | (_) | |
#
from collections import defaultdict


from src.Requirement_util import config

# Format dict
format_dict = defaultdict()
for name, value in config.items("Format_dict"):
    format_dict[name] = config.get("Format_mesure", value)


DEFAULT_CHARACTER = ""


def format_table(header_name, table_body):
    for line in table_body:
            for i, name in enumerate(header_name):
                if name in format_dict:
                    if line[i]:
                        line[i] = format_dict[name].format(line[i])
                    else:
                        line[i] = DEFAULT_CHARACTER

    return table_body
