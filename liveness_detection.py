"""Prototype randomized facial movement challenge. Not certified anti-spoofing."""
import random
import time
import math

LEFT_EYE = (33, 160, 158, 133, 153, 144)
RIGHT_EYE = (362, 385, 387, 263, 373, 380)


def eye_ratio(points, ids):
    def dist(a, b):
        return math.hypot(points[a].x - points[b].x, points[a].y - points[b].y)
    width = dist(ids[0], ids[3])
    return (dist(ids[1], ids[5]) + dist(ids[2], ids[4])) / (2 * width) if width else 0


def face_signals(landmarks):
    points = landmarks.landmark
    eye = (eye_ratio(points, LEFT_EYE) + eye_ratio(points, RIGHT_EYE)) / 2
    # Approximate horizontal nose position relative to eye corners; camera mirrored/non-mirrored is irrelevant.
    left, right = points[33].x, points[263].x
    span = abs(right - left)
    nose_offset = (points[1].x - (left + right) / 2) / span if span else 0
    return eye, nose_offset


class LivenessChallenge:
    def __init__(self, timeout=12, rng=None):
        self.timeout = timeout
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.student_id = None
        self.action = None
        self.started = 0
        self.open_seen = False
        self.closed_seen = False
        self.neutral_seen = False
        self.verified = False

    def begin(self, student_id, now=None):
        self.reset()
        self.student_id = str(student_id)
        self.action = self.rng.choice(('blink', 'turn'))
        self.started = time.monotonic() if now is None else now

    def observe(self, student_id, eye, nose, now=None):
        now = time.monotonic() if now is None else now
        if student_id is None:
            self.reset()
            return False
        if str(student_id) != self.student_id or self.action is None:
            self.begin(student_id, now)
            return False
        if now - self.started > self.timeout:
            self.begin(student_id, now)
            return False
        if self.verified:
            return True
        if self.action == 'blink':
            # Open -> closed -> open sequence; thresholds need real-camera calibration.
            if eye > 0.24:
                if self.closed_seen:
                    self.verified = True
                self.open_seen = True
            elif eye < 0.19 and self.open_seen:
                self.closed_seen = True
        else:
            # Start facing forward, then visibly turn to either side.
            if abs(nose) < 0.10:
                self.neutral_seen = True
            elif abs(nose) > 0.19 and self.neutral_seen:
                self.verified = True
        return self.verified

    @property
    def instruction(self):
        if self.verified:
            return 'Movement verified'
        return 'Blink once' if self.action == 'blink' else 'Face forward, then turn your head'
