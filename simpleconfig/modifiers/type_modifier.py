"""
Modify types such as a class and a function.
This modifier should be the model for any other modifier.

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
import types
import importlib


# The fields that can be used as implicit fields
implicit_fields = 'object', 'instance', 'call'

# The types that will trigger this modifier
types = type, types.FunctionType


def encode(conf, value):
    """
    Modify the input value

    :param conf: A configuration object
    :param value: The value requested to store
    :return: None
    """
    conf.name = value.__name__
    conf.module = value.__module__


def decode(conf):
    """
    Decode the modified configuration

    :param conf: The configuration which stores the modified value
    :return: A decoded value
    """
    type_obj = conf.object
    if not conf.has_section('args') and not conf.has_section('kwargs'):
        return type_obj
    args = conf.args
    kwargs = conf.kwargs
    return type_obj(*args, **kwargs)


def encode_field(_conf, key, value):
    """
    Set a specialized field of this modifier

    :param _conf: A configuration object
    :param key: The field to set
    :param value: The value requested to store
    :return: None
    """
    if key in ('name', 'module'):
        return key, str(value)
    elif key == "args":
        return key, list(value)
    elif key == "kwargs":
        return key, dict(value)
    else:
        raise ValueError("Modifier does not support field: %s" % key)


def decode_field(_conf, _key, value):
    """
    Reads the value that was modified

    :param _conf: A configuration object
    :param _key: The field used by the user. Should be verified that a correct field was used.
    :param value: The value to decode
    :return: The decoded value
    """
    return value


def decode_implicit_field(conf, key):
    """
    Create a value from other values that are stored in the configuration.
    Implicit fields does not store their own value.

    :param conf: The configuration object
    :param key: The key that have been used
    :return: A value
    """
    if key == 'object':
        module = importlib.import_module(conf.module)
        return getattr(module, conf.name)
    elif key in ('instance', 'call'):
        type_obj = conf.object
        if type(type_obj) == type:
            assert key == "instance", f"Operation: {key} is not supported. Type object only supports instantiation."
        else:
            assert key == "call", f"Operation: {key} is not supported. Function object only supports calling."

        args = conf.args if 'args' in conf else []
        kwargs = conf.kwargs if 'kwargs' in conf else {}
        return type_obj(*args, **kwargs)
    else:
        raise ValueError("%s is not an implicit field" % key)
