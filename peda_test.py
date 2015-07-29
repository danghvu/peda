import unittest

# NOTE: This only works inside GDB. Run as either follow:
# gdb-peda$ source peda_test.py
# gdb -x peda_test.py

class TestPedaMethods(unittest.TestCase):

    def setUp(self):
        self.peda = PEDA()
        self.assertIsNotNone(self.peda)
        self.peda.execute_redirect("peda set option context ''")
        self.peda.execute_redirect("set logging off")
        self.execute("file ls", "start > /dev/null")

    def tearDown(self):
        self.execute("finish")
        self.execute("kill")

    """ Execute multiple command for testing. """
    def execute(self, *args):
        for arg in args:
            self.peda.execute_redirect(arg)

    def test_execute(self):
        self.assertTrue(self.peda.execute_redirect('peda'))
        self.assertFalse(self.peda.execute('unknown_command'))

    def test_execute_redirect(self):
        self.assertEquals('x', self.peda.execute_redirect('echo x'))

    def test_parse_and_eval(self):
        self.assertEquals("0x2", self.peda.parse_and_eval("1 + 1"))
        self.assertEquals("0x6", self.peda.parse_and_eval("0x3 * 0x2"))
        # Run in a ls context.
        self.execute("set $eax=0x10")
        self.assertEquals("0x10", self.peda.parse_and_eval("$eax"))

    def test_string_to_argv(self):
        self.assertEquals(['1', '2', '3'], self.peda.string_to_argv("1 2 3"))
        self.execute("set $eax=1")
        self.assertEquals(['0x1', '1'], self.peda.string_to_argv("$eax 1"))
        self.assertEquals(['0xdeadbeef', '0x1'],
            self.peda.string_to_argv("0xdeadbeef 0x1"))

    def test_is_target_remote(self):
        self.assertFalse(self.peda.is_target_remote())
        # TODO: test actual remote.

    def test_getfile(self):
        self.execute("file /usr/bin/ls")
        self.assertEquals("/usr/bin/ls", self.peda.getfile())

    def test_get_status(self):
        self.execute("finish", "kill")
        self.assertEquals("STOPPED", self.peda.get_status())
        self.execute("file /usr/bin/ls")
        self.assertEquals("STOPPED", self.peda.get_status())
        self.execute("start > /dev/null")
        self.assertEquals("BREAKPOINT", self.peda.get_status())
        self.execute("set $pc=0x0", "continue >/dev/null")
        self.assertEquals("SIGSEGV", self.peda.get_status())
        self.execute("finish")

    def test_getpid(self):
        pid = self.peda.getpid()
        expected = self.execute("call getpid()")
        expected = int(self.peda.execute_redirect("print $").split('=')[1], 16)
        self.assertEquals(expected, pid)

    def test_getreg(self):
        self.execute("set $eax=1337")
        self.assertEquals(1337, self.peda.getreg("eax"))
        self.assertEquals(1337, self.peda.getreg("Eax"))
        self.execute("set $al=13")
        self.assertEquals((1337 & 0xFF00) + 13, self.peda.getreg("eax"))

    def test_breakpoint(self):
        self.peda.set_breakpoint(0x1337)
        self.peda.set_breakpoint(0xdeadbeef)
        brs = self.peda.get_breakpoints()
        self.assertEquals(2, len(brs))
        self.execute("delete")
        self.assertEquals(0x1337, brs[0][4])
        self.assertEquals(0xdeadbeef, brs[1][4])

if __name__ == '__main__':
    unittest.main()
