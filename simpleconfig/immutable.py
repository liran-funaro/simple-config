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


def mutator(f):
    """ A decorator for a function to mark as mutator method """
    setattr(f, "__is_mutator__", True)
    return f


class ImmutableConfiguration(Exception):
    def __init__(self, function_name):
        super(ImmutableConfiguration, self).__init__("Immutable configuration does not support %s" % function_name)

    @staticmethod
    def immutable_function_factory(f_name):
        """ :return: a function that raises this exception """

        def immutable_function_placeholder(*_args, **_kwargs):
            raise ImmutableConfiguration(f_name)

        return immutable_function_placeholder
