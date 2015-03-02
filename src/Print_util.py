#!/usr/bin/env python
# -*- coding: utf-8 -*-

DEFAULT_CHARACTER = ""


def format_table(format_dict, header_name, table_body):
    for line in table_body:
            for i, name in enumerate(header_name):
                if name in format_dict:
                    if line[i]:
                        line[i] = format_dict[name].format(line[i])
                    else:
                        line[i] = DEFAULT_CHARACTER

    return table_body
