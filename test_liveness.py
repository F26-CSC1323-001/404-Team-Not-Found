import unittest
from liveness_detection import LivenessChallenge

class FixedRandom:
    def __init__(self, value): self.value = value
    def choice(self, options): return self.value

class ChallengeTests(unittest.TestCase):
    def test_blink(self):
        c = LivenessChallenge(rng=FixedRandom('blink'))
        self.assertFalse(c.observe('101', .30, 0, 1))
        self.assertFalse(c.observe('101', .30, 0, 2))
        self.assertFalse(c.observe('101', .14, 0, 3))
        self.assertTrue(c.observe('101', .30, 0, 4))
    def test_turn(self):
        c = LivenessChallenge(rng=FixedRandom('turn'))
        self.assertFalse(c.observe('101', .30, 0, 1))
        self.assertFalse(c.observe('101', .30, 0, 2))
        self.assertTrue(c.observe('101', .30, .25, 3))
    def test_face_change_resets(self):
        c = LivenessChallenge(rng=FixedRandom('turn'))
        c.observe('101', .3, 0, 1)
        c.observe('101', .3, 0, 2)
        self.assertFalse(c.observe('102', .3, .3, 3))
    def test_timeout(self):
        c = LivenessChallenge(timeout=5, rng=FixedRandom('blink'))
        c.observe('101', .3, 0, 1)
        c.observe('101', .3, 0, 2)
        self.assertFalse(c.observe('101', .1, 0, 8))

if __name__ == '__main__': unittest.main()
