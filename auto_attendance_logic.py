"""Conservative, per-camera recognition stability and retry control."""
import time

class AutoCheckIn:
    def __init__(self, required_frames=12, cooldown_seconds=10):
        self.required_frames = required_frames
        self.cooldown_seconds = cooldown_seconds
        self.candidate = None
        self.frames = 0
        self.last_attempt = {}

    def observe(self, student_id, now=None):
        now = time.monotonic() if now is None else now
        if student_id is None:
            self.candidate = None
            self.frames = 0
            return None
        if student_id != self.candidate:
            self.candidate = student_id
            self.frames = 1
        else:
            self.frames += 1
        if self.frames < self.required_frames:
            return None
        if now - self.last_attempt.get(student_id, float('-inf')) < self.cooldown_seconds:
            return None
        self.last_attempt[student_id] = now
        self.frames = 0
        return student_id
