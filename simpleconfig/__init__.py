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
from io import StringIO
from typing import Optional, Iterable
from simpleconfig import store_engines
from simpleconfig.modifiers import get_modifier_by_name, get_modifier_by_value
from simpleconfig.immutable import mutator, ImmutableConfiguration


class SimplerConfig(object):
    """
    This class is a dictionary like object that can be used to easily add
    sub-dictionaries and be used as a key value store.
    Given a "conf" object:
    To create/access a sub-configuration "sub", simply use:
    > conf.sub
    To set a value:
    > conf.sub.something = 10
    To use a higher hierarchy, simply continue in the same manner:
    > conf.sub.subsub.etc.something_different = 20
    Or:
    > conf.something_else = 30
    The class does not allow overwriting keys.
    For example, the following will rise an exception:
    > conf.sub = 40
    This can be avoided by calling before:
    > del conf.sub

    To access a value:
    If it is a numeric value or a string, simply use its key:
    > temp = conf.something
    However, different encoders have different keys.
    For example, if you stored a class type or a function, use "object" to
    retrieve the class/function it self, or use "instance" to create an instance
    of that class with the parameters set as follows:
    conf.some_class_or_func.args = [1,2,3]
    conf.some_class_or_func.kwargs = {"a": 1, "b":2}
    > inst = conf.some_class.instance
    Same applies to function with the key "call":
    > ret = conf.some_func.call
    """

    def __init__(self, file_path: Optional[str] = None, owner: Optional['SimplerConfig'] = None,
                 modifier: Optional[str] = None, sub_path: Optional[Iterable] = None, key: Optional[str] = None,
                 store_engine: store_engines.STORE_TYPING = None, *args, **kwargs):
        """
        :param file_path: The full path of the file to read/store the configuration to.
        :param owner: If an owner is set, then when saving the configuration, the
            owner's configuration will be saved, while containing this object data.
        :param modifier: The modifier of this conf
        :param sub_path: The sub path that leads to this configuration item
        :param key: The key of this configuration item
        :param store_engine: A class that implements writer/parser interface
        :param args, kwargs: Same logic as dict() object
        """
        self.__init_private_data__(owner, modifier, sub_path, key, store_engine)

        if file_path is not None:
            self.load_from_file(file_path)

        self.update(*args, **kwargs)

    @mutator
    def __init_private_data__(self, owner, modifier, sub_path, key, store_engine):
        """ Create the inner structure of the object """
        # Holds the data of the configuration
        object.__setattr__(self, "__data__", {})
        # Holds the meta-data
        object.__setattr__(self, "__meta__", {
            'owner': owner,
            'back': owner,
            'root': self if owner is None else owner.root,
            'sub_path': tuple(sub_path) if sub_path else (),
            'modifier': modifier,
            'key': key,
        })

        writer, parser = store_engines.get_store_engine(store_engine)

        # Holds the class for writing conf to file
        object.__setattr__(self, "__writer__", writer)
        # Holds the class for reading conf from file
        object.__setattr__(self, "__parser__", parser)
        # Holds the order in which the data was added. Also holds comments.
        object.__setattr__(self, "__order__", [])
        # A set of the keys that are sections
        object.__setattr__(self, "__sections__", set())

    #################################################################################
    # Encoder
    #################################################################################

    def get_modifier_name(self):
        """ Get the current modifier name """
        return self.__meta__.get('modifier', None)

    def have_modifier(self):
        """ Returns true if an modifier is set for this  """
        return self.get_modifier_name() is not None

    def get_modifier(self):
        """ Get the modifier matching the inner data of the object """
        return get_modifier_by_name(self.get_modifier_name())

    @mutator
    def set_modifier(self, modifier_name: Optional[str]):
        """ Sets the modifier for this configuration. Deletes all the inner data """
        if modifier_name is not None and not isinstance(modifier_name, str):
            raise ValueError("Modifier name must be a string or None")

        self.__data__.clear()
        self.__meta__['modifier'] = modifier_name

    #################################################################################
    # Meta data
    #################################################################################

    def is_empty(self):
        """
        :return: True of the conf is empty
        """
        return len(self.__data__) == 0

    def get_file_path(self):
        """ Gets the file path of this configuration """
        return self.__meta__["config_file_path"]

    @mutator
    def set_file_path(self, file_path=None):
        """ Sets the file path of this configuration """
        self.__meta__["config_file_path"] = file_path

    @property
    def sections(self):
        """ Return the sections in this conf """
        return tuple(self.__sections__)

    @mutator
    def encode(self, value):
        """
        Encode a value in this configuration.
        If encoder is not defined, will raise an exception.
        """
        mod = self.get_modifier()
        if mod is None:
            raise Exception("Cannot call encode without a modifier")
        mod.encode(self, value)

    @mutator
    def set_immutable(self, recursive=True, from_root=True):
        """
        This method set the configuration to be immutable.
        It is not reversible. The only way to reverse it is to save the
        configuration to a file and load it again.
        :param recursive: Apply this to all the sub sections as well
        :param from_root: Apply this to all the configurations starting from root.
                If this is set, then recursive is implicitly also set to true.
        :return: None
        """
        if from_root is True and self is not self.root:
            return self.root.set_immutable(recursive=True, from_root=False)

        import inspect
        for f_name, f in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(f, "__is_mutator__", False):
                object.__setattr__(self, f_name, ImmutableConfiguration.immutable_function_factory(f_name))

        if recursive is True:
            for s in self.__sections__:
                self[s].set_immutable(recursive=True, from_root=False)

    #################################################################################
    # Private helper functions
    #################################################################################

    @mutator
    def __update_data__(self, key, value):
        """ Set a configuration value and store the order of assignment. """
        self.__data__[key] = value
        self.__order__.append(('key', key))

    @staticmethod
    def __key_transform__(key):
        """
        Unlike dict, we are not case-sensitive.
        We transform all the keys to lowercase and switch "-" and " " to "_" to allow access as a member.
        Integer keys (i.e., list behavior) will be replaced with list#
        We also verify that the key is a valid python name.
        """
        if isinstance(key, int):
            key = f"list{key}"

        key = str(key).lower().replace("-", "_").replace(" ", "_").replace(".", "_")

        if key[0] in map(str, range(10)):
            raise KeyError("Key must be a valid python name (cannot start with a digit)")

        return key

    #################################################################################
    # Conf data (read only)
    #################################################################################

    def get_value(self, key, default_value=None):
        """
        Read a value or section if exists, otherwise return default value.
        :param key: The key to get
        :param default_value: The default value to return if the key does not exist
        :return: The fetched value of the default value
        """
        key = self.__key_transform__(key)
        if key in self.__meta__:
            return self.__meta__[key]

        mod = self.get_modifier()
        value = self.__data__.get(key, default_value)

        if mod is None:
            return value
        elif key not in mod.implicit_fields:
            return mod.decode_field(self, key, value)
        else:
            # implicit fields does not store any value in its key
            return mod.decode_implicit_field(self, key)

    def get_section(self, key):
        """
        Get a subsection. If not exists, creates it.
        :param key: subsection key
        :return: The requested subsection
        """
        key = self.__key_transform__(key)
        if key in self.__sections__:
            return self.__data__[key]
        if key in self.__meta__:
            raise KeyError("Meta-data field %s is not a section" % key)
        if key in self.__data__:
            raise KeyError("%s is a value field, not a section" % key)
        else:
            return self.add_section(key)

    def has_section(self, key):
        """
        :param key: The key to check
        :return: True if a section exists with that key
        """
        return key in self.__sections__

    #################################################################################
    # Conf data (write/update)
    #################################################################################

    @mutator
    def set_value(self, key, value):
        """
        Set a value. If that key already been used, will raise an error.
        :param key: The key to store
        :param value: The value to store
        :return: None
        """
        key = self.__key_transform__(key)

        mod = self.get_modifier()
        if mod is not None:
            key, value = mod.encode_field(self, key, value)
            assert key not in mod.implicit_fields, "Cannot store values in implicit field"

        if key in self.__meta__:
            raise KeyError("Cannot set meta-data field: %s" % key)
        if key in self.__data__:
            raise KeyError("Cannot update existing data field or section: %s" % key)

        field_enc_name = get_modifier_by_value(value)
        if field_enc_name is not None:
            new_section = self.add_section(key, field_enc_name)
            new_section.encode(value)
        else:
            # Built in support for dictionaries and list/tuples
            if isinstance(value, dict):
                dict_section = self.add_section(key)
                for k, v in value.items():
                    dict_section[k] = v
            elif isinstance(value, list) or isinstance(value, tuple):
                list_section = self.add_section(key)
                for k, v in enumerate(value):
                    list_section[k] = v
            else:
                self.__update_data__(key, value)

    @mutator
    def add_section(self, key, section_type=None):
        """
        Adds subsection. If already exists, raise exception
        :param key: subsection key
        :param section_type: subsection type
        :return: The new subsection
        """
        key = self.__key_transform__(key)

        if key in self.__meta__:
            raise KeyError("Cannot use meta-data field: %s" % key)
        if self.has_section(key):
            raise KeyError("%s section already exists" % key)
        if key in self:
            raise KeyError("%s is used to store value" % key)

        sub_conf = self.__class__(owner=self, sub_path=[*self.sub_path, key],
                                  key=key, modifier=section_type)
        self.__update_data__(key, sub_conf)
        self.__sections__.add(key)
        return sub_conf

    @mutator
    def add_comment(self, comment):
        """ Adds a comment to the bottom of the stack """
        self.__order__.append(('comment', comment))

    #################################################################################
    # Emulating container types
    #################################################################################

    @mutator
    def update(self, *args, **kwargs):
        a = dict(*args, **kwargs)

        for key, value in a.items():
            self[key] = value

    def __len__(self):
        return len(self.__data__)

    def __missing__(self, key):
        return self.add_section(key)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            cur = self
            for k in key:
                cur = cur[k]
            return cur

        test_item = {'test'}
        ret = self.get_value(key, test_item)
        if ret is not test_item:
            return ret
        else:
            # If the item does not exist, we will look recursively in all the owners globals
            conf = self
            while conf is not None:
                if conf.has_section("globals") and key in conf.globals:
                    return conf.globals[key]
                else:
                    conf = conf.owner

            # Finally, if we didn't find it, create a new section
            return self.get_section(key)

    def __getattr__(self, key):
        if key == "__bases__":
            return object.__getattr__(self, key)
        else:
            return self[key]

    @mutator
    def __setitem__(self, key, value):
        return self.set_value(key, value)

    __setattr__ = __setitem__

    @mutator
    def __delitem__(self, key):
        key = self.__key_transform__(key)
        del self.__data__[key]
        if key in self.__sections__:
            self.__sections__.remove(key)

    def __contains__(self, key):
        return self.__key_transform__(key) in self.__data__

    def iter_as_list(self):
        string_keys = self.__data__.keys()
        if len(string_keys) == 0:
            return

        assert all(k.startswith("list") for k in string_keys)
        all_keys = set(int(k[4:]) for k in string_keys)
        max_key = max(all_keys)
        for i in range(max_key + 1):
            if i in all_keys:
                yield self[i]
            else:
                yield None

    def __iter__(self):
        try:
            return self.iter_as_list()
        except:
            return self.__data__.__iter__()

    def keys(self):
        return self.__data__.keys()

    def values(self):
        return self.__data__.values()

    def items(self):
        return self.__data__.items()

    def get(self, key, default_value=None):
        return self.get_value(key, default_value)

    def has_key(self, key):
        if key in self.__meta__:
            return True
        if key in self.__data__:
            return True
        return False

    @mutator
    def clear(self):
        self.__data__.clear()
        self.set_modifier(None)

    @mutator
    def setdefault(self, key, default):
        test_item = {'test'}
        ret = self.get_value(key, test_item)
        if ret is not test_item:
            return ret

        self.set_value(default)
        return default

    #################################################################################
    # Serialization and Deserialization
    #################################################################################

    def as_dict(self):
        return {**self}

    def __repr__(self):
        return str(self.as_dict())

    def dump(self, fp):
        """ Writes the conf to a file using the supplied writer """
        w = self.__writer__(fp)
        return self.__dump__(w)

    def __dump__(self, writer_object):
        """ Actual implementation of dump using the writer """
        w = writer_object
        for item_type, item_info in self.__order__:
            if item_type == 'key':
                if item_info not in self.__data__:
                    continue

                k, v = item_info, self.__data__[item_info]
                if self.has_section(k):
                    w.start_section(k, v.get_modifier_name())
                    v.__dump__(w)
                    w.end_section()
                else:
                    w.write_key_value(k, v)
            elif item_type == 'comment':
                w.write_comment(item_info)
            else:
                raise Exception("Internal error: unknown order information %s" % item_type)

    def dumps(self):
        """ dump() to a string """
        with StringIO() as s:
            self.dump(s)
            return s.getvalue()

    def save(self, file_path=None):
        """
        Saves the configuration to a file. Will only save the root owner.
        :file_path: If specified, will save the file to this file path.
                Does not change the internal file_path.
        """
        if self is not self.root:
            return self.root.save()

        if file_path is None:
            file_path = self.get_file_path()
        if file_path is None:
            raise Exception("No file path specified")

        with open(file_path, "w+") as f:
            self.dump(f)

    @mutator
    def save_as(self, file_path):
        """ Save the configuration to a specified file. Will still only save the root owner. """
        if self is not self.root:
            return self.root.save_as(file_path)
        self.set_file_path(file_path)
        self.save()

    @mutator
    def load(self, fp):
        """ Load a configuration from a file into this configuration object, using the parser """
        p = self.__parser__(fp, self)
        p.parse()

    @mutator
    def loads(self, string):
        """ load() from a string """
        with StringIO(string) as s:
            self.load(s)

    def load_from_file(self, file_path):
        """ load() from a file """
        is_new = len(self.__order__) == 0
        with open(file_path, "r") as f:
            self.load(f)

        if is_new:
            self.set_file_path(file_path)

    @classmethod
    def from_string(cls, string, file_path=None, owner=None):
        """ Creates a new configuration object from a string """
        cfg = cls(file_path, owner)
        cfg.loads(string)
        return cfg

    def copy(self, file_path=None, owner=None):
        """ Create a full depth copy of this configuration """
        with StringIO() as s:
            self.dump(s)
            s.seek(0)
            ret = self.__class__(file_path, owner)
            ret.load(s)

        return ret
