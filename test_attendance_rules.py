"""Safe unit checks: run against an isolated temporary SQLite database."""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import database
import schedule
from attendance import mark_attendance


class AttendanceRulesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(database, "DB_PATH", Path(self.temp.name) / "test.db")
        self.db_patch.start()
        database.initialize_database()
        with database.connect() as conn:
            conn.execute("INSERT INTO students(student_id,name) VALUES('101','Test Student')")
            conn.execute("INSERT INTO enrollments(student_id,course) VALUES('101','CSC130')")

    def tearDown(self):
        self.db_patch.stop()
        self.temp.cleanup()

    def test_boundaries(self):
        def status(clock):
            return schedule.attendance_status("CSC130", datetime.fromisoformat("2026-10-26T" + clock))
        self.assertEqual(status("07:59:59"), "Before class")
        self.assertEqual(status("08:00:00"), "Present")
        self.assertEqual(status("08:15:00"), "Present")
        self.assertEqual(status("08:15:01"), "Late")
        self.assertEqual(status("08:59:59"), "Late")
        self.assertEqual(status("09:00:00"), "Closed")

    def test_checkin_and_duplicate(self):
        when = datetime.fromisoformat("2026-10-26T08:20:00")
        self.assertEqual(mark_attendance("101", "CSC130", when), "late")
        self.assertEqual(mark_attendance("101", "CSC130", when), "duplicate")
        with database.connect() as conn:
            self.assertEqual(conn.execute("SELECT status FROM attendance").fetchone()[0], "Late")

    def test_unenrolled_and_nonmeeting_day(self):
        self.assertEqual(mark_attendance("101", "CSC131", datetime.fromisoformat("2026-10-26T08:10:00")), "recorded")
        self.assertEqual(mark_attendance("101", "CSC130", datetime.fromisoformat("2026-10-25T08:10:00")), "outside_window")


if __name__ == "__main__":
    unittest.main()
