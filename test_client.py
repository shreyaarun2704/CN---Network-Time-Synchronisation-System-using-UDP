import unittest
from client import parse_server_reply
class ParseReplyTests(unittest.TestCase):
    def test_four_timestamp_json(self):
        t2,t3=parse_server_reply(b'{"t2":100.1,"t3":100.2}')
        self.assertAlmostEqual(t2,100.1);self.assertAlmostEqual(t3,100.2)
    def test_invalid_reply(self):
        with self.assertRaises((ValueError,TypeError)):parse_server_reply(b"not a timestamp")
    def test_missing_timestamps(self):
        with self.assertRaises(ValueError):parse_server_reply(b'{"ok":true}')
if __name__=="__main__":unittest.main()
