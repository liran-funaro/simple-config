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
from unittest import TestCase

from simpleconfig import SimplerConfig
from simpleconfig.immutable import ImmutableConfiguration


class MockClass:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def bar(self):
        return self.args, self.kwargs


def mock_foo(*args, **kwargs):
    return args, kwargs


class TestConfClass:
    def __init__(self, some_info, conf):
        self.some_info = some_info
        self.global_var = conf.global_var
        self.conf_class = conf.conf_class.instance

    def foo(self):
        return self.some_info, self.global_var, self.conf_class.bar()


class TestHierarchicalEncodedConfig(TestCase):
    def test_set_get_item(self):
        cfg = SimplerConfig()
        cfg["level1"] = "new val"
        self.assertEqual(cfg['level1'], "new val")

    def test_set_item_2deep(self):
        cfg = SimplerConfig()
        cfg['level1']['level2'] = "new val"
        self.assertEqual(cfg['level1']['level2'], "new val")

    def test_set_attr(self):
        cfg = SimplerConfig()
        cfg.level1 = "new val"
        self.assertEqual(cfg.level1, "new val")

    def test_set_attr_2deep(self):
        cfg = SimplerConfig()
        cfg.level1.level2 = "new val"
        self.assertEqual(cfg.level1.level2, "new val")

    def test_set_get_dict(self):
        cfg = SimplerConfig()
        cfg.level1 = {'a': 1, 'b': 2}
        self.assertEqual(cfg.level1.a, 1)
        self.assertEqual(cfg.level1.b, 2)
        self.assertDictEqual({'level1': cfg.level1}, {**cfg})

    def test_set_get_list_tuple(self):
        cfg = SimplerConfig()
        cfg.level_list = [10, 8, 9, 1]
        cfg.level_tuple = (10, 2)
        self.assertEqual(cfg.level_list[0], 10)
        self.assertEqual(cfg.level_list[1], 8)
        self.assertEqual(cfg.level_list[2], 9)
        self.assertEqual(cfg.level_list[3], 1)
        self.assertEqual(len(cfg.level_list), 4)
        self.assertListEqual([*cfg.level_list], [10, 8, 9, 1])

        self.assertEqual(cfg.level_tuple[0], 10)
        self.assertEqual(cfg.level_tuple[1], 2)
        self.assertEqual(len(cfg.level_tuple), 2)
        self.assertTupleEqual(tuple([*cfg.level_tuple]), (10, 2))

    def test_set_get_class(self):
        cfg = SimplerConfig()
        cfg.c = MockClass
        cfg.c.args = [10, 2, 3]
        cfg.c.kwargs["hello"] = 2
        self.assertEqual(cfg.c.object, MockClass)
        self.assertTupleEqual(cfg.c.instance.bar(), ((10, 2, 3), {'hello': 2}))

    def test_set_get_function(self):
        cfg = SimplerConfig()
        cfg.c = mock_foo
        cfg.c.args = [10, 2, 3]
        cfg.c.kwargs["hello"] = 2
        self.assertEqual(mock_foo, cfg.c.object)
        self.assertTupleEqual(((10, 2, 3), {'hello': 2}), cfg.c.call)

    def test_globals(self):
        cfg = SimplerConfig()
        cfg.globals.a = 1
        self.assertEqual(cfg.level1.a, 1)

    def test_globals_deep(self):
        cfg = SimplerConfig()
        cfg.globals.a = 1
        cfg.globals.b = 2
        cfg.level1.globals.c = 3
        cfg.level1.level2.globals.a = 4
        cfg.section1.section2.a = 5

        self.assertEqual(cfg.a, 1)
        self.assertEqual(cfg.globals.a, 1)

        self.assertEqual(cfg.b, 2)
        self.assertEqual(cfg.globals.b, 2)

        self.assertEqual(cfg.level1.a, 1)
        self.assertEqual(cfg.level1.b, 2)
        self.assertEqual(cfg.level1.c, 3)
        self.assertEqual(cfg.level1.globals.c, 3)

        self.assertEqual(cfg.level1.level2.a, 4)
        self.assertEqual(cfg.level1.level2.globals.a, 4)
        self.assertEqual(cfg.level1.level2.b, 2)
        self.assertEqual(cfg.level1.level2.c, 3)

        self.assertEqual(cfg.section1.section2.a, 5)
        self.assertEqual(cfg.section1.section2.b, 2)

    def test_complex_conf_arguments_to_class(self):
        cfg = SimplerConfig()
        cfg.globals.global_var = "global information"
        cfg.c = TestConfClass
        cfg.c.kwargs.some_info = "information"
        cfg.c.kwargs.conf.conf_class = MockClass
        cfg.c.kwargs.conf.conf_class.args = [2, 5, 1]
        cfg.c.kwargs.conf.conf_class.kwargs = {'hello': 2}

        self.assertTupleEqual(cfg.c.instance.foo(),
                              ("information", "global information", ((2, 5, 1), {'hello': 2})))

    def test_dumps(self):
        cfg = SimplerConfig()
        cfg.add_comment("Some comment")
        cfg.level1 = "new val"
        cfg.section1.add_comment("# Left most comment")
        cfg.add_comment("Should be after section 1")
        cfg.section1.item1 = "item 1"
        cfg.section1.add_comment("    # Indented comment")
        cfg.section1.subsection.item2 = "item 2"
        cfg.section2.subsection.item3 = 3
        _ = cfg.empty_section
        cfg.just_item = 5
        cfg.add_comment("Trailing comment")
        res = cfg.dumps()
        self.assertEqual(res, """\
# Some comment
level1 = new val
section1:
# Left most comment
    item1 = item 1
    # Indented comment
    subsection:
        item2 = item 2
# Should be after section 1
section2:
    subsection:
        item3 = 3
empty_section:
just_item = 5
# Trailing comment
""")

    def test_loads(self):
        file_string = """\
# Some comment
empty_section:
level1 = new val
section1:
# this is a comment for section1.item1:
    item1 = item 1
          # this is another comment
    # Indented comment
    subsection:
        item2 = item 2
# Should be after section 1
section2:
    subsection:
        item3 = 3
very_last = 7
# Trailing comment
"""
        cfg = SimplerConfig()
        cfg.loads(file_string)
        self.assertSetEqual(set(cfg.keys()),
                            {'empty_section', 'level1',
                             'section1', 'section2', 'very_last'})
        self.assertSetEqual(set(cfg.section1.keys()),
                            {'item1', 'subsection'})
        self.assertTrue(cfg['empty_section'].is_empty())
        self.assertEqual(cfg.level1, "new val")
        self.assertEqual(cfg.section1.item1, "item 1")
        self.assertEqual(cfg.section1.subsection.item2, "item 2")
        self.assertEqual(cfg.section2.subsection.item3, 3)
        self.assertEqual(cfg['very last'], 7)

    def test_preserve_comments(self):
        file_string = """\
# Some comment
empty_section:
level1 = new val
section1:
# this is a comment for section1.item1:
    item1 = item 1
          # this is another comment
    # Indented comment
    subsection:
        item2 = item 2
# Should be after section 1
section2:
    subsection:
        item3 = 3
very_last = 7
# Trailing comment
"""
        cfg = SimplerConfig()
        cfg.loads(file_string)
        res = cfg.dumps()
        self.assertEqual(file_string, res)

    def test_varying_indents(self):
        file_string = """\
empty_section:
level1 = new val
section1:
    item1 = item 1
    subsection:
        item2 = item 2
section2:
 subsection:
     item3 = 3
very_last = 7
"""
        cfg = SimplerConfig()
        cfg.loads(file_string)
        self.assertSetEqual(set(cfg.keys()),
                            {'empty_section', 'level1',
                             'section1', 'section2', 'very_last'})
        self.assertSetEqual(set(cfg.section1.keys()),
                            {'item1', 'subsection'})
        self.assertTrue(cfg['empty_section'].is_empty())
        self.assertEqual(cfg.level1, "new val")
        self.assertEqual(cfg.section1.item1, "item 1")
        self.assertEqual(cfg.section1.subsection.item2, "item 2")
        self.assertEqual(cfg.section2.subsection.item3, 3)
        self.assertEqual(cfg['very_last'], 7)

    def test_bad_syntax1(self):
        file_string = """\
empty_section:
level1 = new val
section1:
  item1 = item 1
    subsection:
        item2 = item 2
section2:
 subsection:
     item3 = 3
very_last = 7
"""
        cfg = SimplerConfig()
        with self.assertRaises(Exception) as context:
            cfg.loads(file_string)

        self.assertRegex(str(context.exception), 'LINE 5')

    def test_bad_syntax2(self):
        file_string = """\
empty_section:
level1 = new val
section1:
    item1 = item 1
    subsection:
        item2 = item 2
 section2:
  subsection:
     item3 = 3
very_last = 7
"""
        cfg = SimplerConfig()
        with self.assertRaises(Exception) as context:
            cfg.loads(file_string)

        self.assertRegex(str(context.exception), 'LINE 7')

    def test_bad_syntax3(self):
        file_string = """\
empty_section:
level1 = new val
section1:
    item1 = item 1
    subsection:
        item2 = item 2
section2:
  subsection:
     item3 = 3
 very_last = 7
"""
        cfg = SimplerConfig()
        with self.assertRaises(Exception) as context:
            cfg.loads(file_string)

        self.assertRegex(str(context.exception), 'LINE 10')

    def test_immutable(self):
        cfg = SimplerConfig()
        cfg.a = 1
        cfg.level1.b = 2
        cfg.level1.level2.c = 3
        cfg.section1.d = 4

        cfg.set_immutable()
        self.assertEqual(cfg.a, 1)
        self.assertEqual(cfg.level1.b, 2)
        self.assertEqual(cfg.level1.level2.c, 3)
        self.assertEqual(cfg.section1.d, 4)

        with self.assertRaises(ImmutableConfiguration) as context:
            cfg.loads("")

        self.assertTrue('loads' in str(context.exception))

        with self.assertRaises(ImmutableConfiguration):
            tmp = cfg.b

        with self.assertRaises(ImmutableConfiguration):
            cfg.b = 5

        with self.assertRaises(ImmutableConfiguration):
            tmp = cfg.level1.a

        with self.assertRaises(ImmutableConfiguration):
            cfg.level1.a = 6

        with self.assertRaises(ImmutableConfiguration):
            tmp = cfg.level1.level2.b

        with self.assertRaises(ImmutableConfiguration):
            cfg.level1.level2.b = 7

        with self.assertRaises(ImmutableConfiguration):
            tmp = cfg.section1.c

        with self.assertRaises(ImmutableConfiguration):
            cfg.section1.c = 7

    def test_immutable_non_recursive(self):
        cfg = SimplerConfig()
        cfg.a = 1
        cfg.level1.b = 2
        cfg.level1.level2.c = 3
        cfg.section1.d = 4

        cfg.set_immutable(recursive=False, from_root=False)
        self.assertEqual(cfg.a, 1)
        self.assertEqual(cfg.level1.b, 2)
        self.assertEqual(cfg.level1.level2.c, 3)
        self.assertEqual(cfg.section1.d, 4)

        with self.assertRaises(ImmutableConfiguration) as context:
            cfg.loads("")

        self.assertTrue('loads' in str(context.exception))

        with self.assertRaises(ImmutableConfiguration):
            tmp = cfg.b

        with self.assertRaises(ImmutableConfiguration):
            cfg.b = 5

        try:
            tmp = cfg.level1.a
        except:
            self.fail("Other levels should not be immutable")

        try:
            cfg.level1.aa = 6
        except:
            self.fail("Other levels should not be immutable")

        try:
            tmp = cfg.level1.level2.b
        except:
            self.fail("Other levels should not be immutable")

        try:
            cfg.level1.level2.bb = 7
        except:
            self.fail("Other levels should not be immutable")

        try:
            tmp = cfg.section1.c
        except:
            self.fail("Other levels should not be immutable")

        try:
            cfg.section1.cc = 7
        except:
            self.fail("Other levels should not be immutable")

    def test_immutable_non_root(self):
        cfg = SimplerConfig()
        cfg.a = 1
        cfg.level1.b = 2
        cfg.level1.level2.c = 3
        cfg.section1.d = 4

        cfg.level1.set_immutable(recursive=True, from_root=False)
        self.assertEqual(cfg.a, 1)
        self.assertEqual(cfg.level1.b, 2)
        self.assertEqual(cfg.level1.level2.c, 3)
        self.assertEqual(cfg.section1.d, 4)

        with self.assertRaises(ImmutableConfiguration) as context:
            cfg.level1.loads("")

        self.assertTrue('loads' in str(context.exception))

        try:
            cfg.loads("")
        except:
            self.fail("Other levels should not be immutable")

        try:
            tmp = cfg.b
        except:
            self.fail("Other levels should not be immutable")

        try:
            cfg.bb = 5
        except:
            self.fail("Other levels should not be immutable")

        with self.assertRaises(ImmutableConfiguration) as context:
            tmp = cfg.level1.a

        with self.assertRaises(ImmutableConfiguration) as context:
            cfg.level1.a = 6

        with self.assertRaises(ImmutableConfiguration) as context:
            tmp = cfg.level1.level2.b

        with self.assertRaises(ImmutableConfiguration) as context:
            cfg.level1.level2.b = 7

        try:
            tmp = cfg.section1.c
        except:
            self.fail("Other levels should not be immutable")

        try:
            cfg.section1.cc = 7
        except:
            self.fail("Other levels should not be immutable")

    def test_sub_path(self):
        cfg = SimplerConfig()
        cfg.a = 1
        cfg.level1.b = 2
        cfg.level1.level2.c = 3
        cfg.section1.d = 4

        self.assertTupleEqual(tuple(), cfg.sub_path)
        self.assertTupleEqual(tuple(['level1']), cfg.level1.sub_path)
        self.assertTupleEqual(tuple(['level1', 'level2']), cfg.level1.level2.sub_path)
        self.assertTupleEqual(tuple(['section1']), cfg.section1.sub_path)

    def test_get_tuple(self):
        cfg = SimplerConfig()
        cfg.a = 1
        cfg.level1.b = 2
        cfg.level1.level2.c = 3
        cfg.section1.d = 4

        ret = cfg['level1', 'level2'].c
        self.assertEqual(ret, 3)

        ret = cfg['level1', 'level2', 'c']
        self.assertEqual(ret, 3)

    def test_key_meta_data(self):
        cfg = SimplerConfig()

        self.assertEqual('path2', cfg.path1.path2.key)
        self.assertEqual('path1', cfg.path1.key)
        self.assertEqual('path3', cfg.path3.key)
        self.assertEqual('path4', cfg.path3.path4.key)
