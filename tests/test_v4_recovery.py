from hashlib import sha256
import unittest
from scripts.recover_v4_study005 import historical_bytes


class RecoveryTests(unittest.TestCase):
    def test_only_archived_byte_identity_is_accepted(self):
        original = b'{"value":1}\r\n'
        digest = sha256(original).hexdigest()
        self.assertEqual(historical_bytes(original, digest), (original, False))
        self.assertEqual(historical_bytes(b'{"value":1}\n', digest), (original, True))
        with self.assertRaises(ValueError):
            historical_bytes(b'{"value":2}\n', digest)
        with self.assertRaises(ValueError):
            historical_bytes(b'{"value":1}', digest)
