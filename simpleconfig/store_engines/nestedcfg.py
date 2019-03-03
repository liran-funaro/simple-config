"""
Author: Liran Funaro <liran.funaro@gmail.com>

Copyright (C) 2006-2018 Liran Funaro

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import re
from ast import literal_eval
from contextlib import suppress

REGEXP_NAME = r"[a-zA-Z_][a-zA-Z0-9_]*"
REGEXP_SECTION_TYPE = r"(?P<is_section>:)\s*(?P<encoder>%s)?\s*" % REGEXP_NAME
REGEXP_VALUE = r"(?P<is_value>=)\s*(?P<value>\S.*)"
REGEXP_DATA_LINE = r"(?P<indent>[ ]*)(?P<key>%s)\s*(?:(?:%s)|(?:%s))" % (REGEXP_NAME, REGEXP_SECTION_TYPE, REGEXP_VALUE)
REGEXP_COMMENT = r"([ \t\r\f\v]*)(?:#(.*)?)?"
RE_COMMENT = re.compile("^" + REGEXP_COMMENT + "$")
RE_ALL_LINES = re.compile(r"^(?:%s)|(?P<comment>%s)$" % (REGEXP_DATA_LINE, REGEXP_COMMENT))

BASE_TYPES = int, float, literal_eval, str


def _convert_from_string(value):
    for known_type in BASE_TYPES:
        with suppress(Exception):
            return known_type(value)

    # All other types failed (including string) raise error
    raise ValueError("Unknown type")


class Parser:
    __slots__ = 'fp', 'new_conf', 'conf_stack'

    def __init__(self, fp, conf):
        self.fp = fp

        self.new_conf = None
        self.conf_stack = [(0, conf)]

    def parse_line(self, input_line):
        m = RE_ALL_LINES.match(input_line)
        if m is None:
            raise Exception("Ill formed line: could not be matched by regular expression")

        d = m.groupdict()
        if d['comment'] is not None:
            return self.__update_comment(d['comment'])

        self.__update_indent(indent=len(d['indent']))
        key = d['key']

        if d['is_section'] is not None:
            return self.__update_section(key, d['encoder'])
        elif d['is_value'] is not None:
            return self.__update_value(key, _convert_from_string(d['value']))
        else:
            raise Exception("Internal Error: line matched expression, but could be parsed")

    def __update_indent(self, indent):
        if indent > self.conf_stack[-1][0]:
            if self.new_conf is not None:
                self.conf_stack.append((indent, self.new_conf))
                self.new_conf = None
            else:
                raise ValueError("Unexpected indentation")
        else:
            self.new_conf = None

        while indent != self.conf_stack[-1][0]:
            self.conf_stack.pop(-1)
            if len(self.conf_stack) == 0:
                raise ValueError("Unexpected indentation")

    def __get_cur_conf(self):
        if self.new_conf is not None:
            return self.new_conf
        else:
            return self.conf_stack[-1][1]

    def __update_comment(self, comment):
        conf = self.__get_cur_conf()
        conf.add_comment(comment)

    def __update_value(self, key, value):
        conf = self.__get_cur_conf()
        conf[key] = value

    def __update_section(self, key, encoder):
        conf = self.__get_cur_conf()
        self.new_conf = conf.add_section(key, encoder)

    def parse(self):
        for n, l in enumerate(self.fp):
            try:
                self.parse_line(l)
            except Exception as e:
                raise Exception(f"[LINE {n+1}] ({type(e).__name__}) {e}")


class Writer:
    def __init__(self, fp):
        self.fp = fp
        self.current_indent = 0
        self.indent_spaces = 4
        self.line_break = "\n"

    def write(self, *data):
        for s in data:
            self.fp.write(str(s))

    def write_indent(self):
        all_indents = [" "] * (self.current_indent * self.indent_spaces)
        self.write(*all_indents)

    def write_line(self, *data):
        self.write(*data)
        self.write(self.line_break)

    def start_section(self, key, encoder):
        self.write_indent()
        if encoder is not None:
            self.write_line(key, ": ", encoder)
        else:
            self.write_line(key, ":")
        self.current_indent += 1

    def end_section(self):
        self.current_indent -= 1

    def write_key_value(self, key, value):
        self.write_indent()
        self.write_line(key, " = ", value)

    def write_comment(self, comment):
        comments_list = comment.split("\n")
        for c in comments_list:
            m = RE_COMMENT.match(c)
            if m is None:
                c = "# " + c
            self.write_line(c)
