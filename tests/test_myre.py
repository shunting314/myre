import myre
from unittest import TestCase

class MyreTest(TestCase):
    def test_basic(self):
        self.assertTrue(myre.match("(a|b)*abb", "ababb").text() == "ababb")
        self.assertTrue(myre.match("(a|b)*a(a|b)(a|b)", "ababbc").text() == "ababb")
        self.assertFalse(myre.match("(a|b)*a(a|b)(a|b)", "cbbbb"))

        # support plus
        id_pattern = "[a-zA-Z_]+[a-zA-Z_0-9]*" 
        self.assertEqual(myre.match(id_pattern, "abc129+-").text(), "abc129")
        self.assertFalse(myre.match(id_pattern, "12"))
