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
import sys
import pkgutil
import importlib
import warnings
from typing import Iterable, Optional


MODIFIERS = set([modname for _, modname, _ in pkgutil.iter_modules(sys.modules[__name__].__path__)])


def import_modifier(modifier_name: str):
    if not isinstance(modifier_name, str):
        raise TypeError(f"Modifier name must be a string. Not {type(modifier_name)}. "
                        f"Choose one of the followings: {MODIFIERS}.")

    if modifier_name not in MODIFIERS:
        raise ValueError(f"No such modifier: {modifier_name}. Choose one of the followings: {MODIFIERS}.")

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=ImportWarning)
        return importlib.import_module(f'.{modifier_name}', __name__)


def include_modifier(modifier_name: str, by_name: Optional[dict] = None, by_type: Optional[dict] = None):
    """ Include modifier in the  """
    if by_name is None:
        by_name = {}
    if by_type is None:
        by_type = {}
    mod = import_modifier(modifier_name)
    by_name[modifier_name] = mod
    for t in mod.types:
        by_type[t] = modifier_name
    return by_name, by_type


def include_all_modifiers(modifier_names: Iterable, by_name: Optional[dict] = None, by_type: Optional[dict] = None):
    """ Create the global encoders list """
    for modifier_name in modifier_names:
        by_name, by_type = include_modifier(modifier_name, by_name, by_type)
    return by_name, by_type


BY_NAME, BY_TYPE = include_all_modifiers(MODIFIERS)


def get_modifier_by_name(name):
    """ Find modifier by its name """
    return BY_NAME.get(name, None)


def get_modifier_by_value(value):
    """ Detect a fitting modifier by the type of the value """
    value_type = type(value)
    return BY_TYPE.get(value_type, None)
