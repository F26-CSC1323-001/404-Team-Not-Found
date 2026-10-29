import unittest
from auto_attendance_logic import AutoCheckIn

class AutoCheckInTests(unittest.TestCase):
    def test_stable_recognition(self):
        c = AutoCheckIn(required_frames=3, cooldown_seconds=10)
        self.assertIsNone(c.observe('101', now=1))
        self.assertIsNone(c.observe('101', now=2))
        self.assertEqual(c.observe('101', now=3), '101')
        self.assertIsNone(c.observe('101', now=4))
        self.assertIsNone(c.observe('101', now=5))
        self.assertIsNone(c.observe('101', now=6))
        self.assertEqual(c.observe('101', now=14), '101')

    def test_unknown_resets(self):
        c = AutoCheckIn(required_frames=3)
        c.observe('101', now=1)
        c.observe('101', now=2)
        c.observe(None, now=3)
        self.assertIsNone(c.observe('101', now=4))
        self.assertIsNone(c.observe('101', now=5))
        self.assertEqual(c.observe('101', now=6), '101')

    def test_switching_identity_resets(self):
        c = AutoCheckIn(required_frames=2)
        c.observe('101', now=1)
        self.assertIsNone(c.observe('102', now=2))
        self.assertEqual(c.observe('102', now=3), '102')

if __name__ == '__main__':
    unittest.main()
