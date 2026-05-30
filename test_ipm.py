"""Tests for Interior Project Manager."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Point the module at a temp data file before importing
_tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
_tmp.close()

import ipm
ipm.DATA_FILE = _tmp.name


def _reset():
    """Reset data file to empty state."""
    if os.path.exists(ipm.DATA_FILE):
        os.remove(ipm.DATA_FILE)


def run_cmd(argv: list[str]) -> None:
    parser = ipm.build_parser()
    args = parser.parse_args(argv)
    data = ipm.load()
    dispatch = {
        "new": ipm.cmd_new,
        "list": ipm.cmd_list_projects,
        "report": ipm.cmd_report,
    }
    if args.command in dispatch:
        dispatch[args.command](args, data)
    elif args.command == "room":
        {"add": ipm.cmd_room_add, "list": ipm.cmd_room_list}[args.room_command](args, data)
    elif args.command == "task":
        {"add": ipm.cmd_task_add, "list": ipm.cmd_task_list,
         "status": ipm.cmd_task_status, "done": ipm.cmd_task_done,
         "notes": ipm.cmd_task_notes}[args.task_command](args, data)


class TestProjects(unittest.TestCase):
    def setUp(self):
        _reset()

    def test_create_project(self):
        run_cmd(["new", "Test Apartment"])
        data = ipm.load()
        self.assertEqual(len(data["projects"]), 1)
        self.assertEqual(data["projects"][0]["name"], "Test Apartment")
        self.assertEqual(data["projects"][0]["id"], 1)

    def test_create_multiple_projects(self):
        run_cmd(["new", "Project A"])
        run_cmd(["new", "Project B"])
        data = ipm.load()
        self.assertEqual(len(data["projects"]), 2)
        self.assertEqual(data["projects"][1]["id"], 2)


class TestRooms(unittest.TestCase):
    def setUp(self):
        _reset()
        run_cmd(["new", "Renovation"])

    def test_add_room(self):
        run_cmd(["room", "add", "--project", "1", "--name", "Living Room", "--sqm", "30"])
        data = ipm.load()
        rooms = data["projects"][0]["rooms"]
        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0]["name"], "Living Room")
        self.assertAlmostEqual(rooms[0]["sqm"], 30.0)

    def test_duplicate_room_rejected(self):
        run_cmd(["room", "add", "--project", "1", "--name", "Kitchen", "--sqm", "10"])
        with self.assertRaises(SystemExit):
            run_cmd(["room", "add", "--project", "1", "--name", "Kitchen", "--sqm", "10"])


class TestTasks(unittest.TestCase):
    def setUp(self):
        _reset()
        run_cmd(["new", "Office Fit-out"])
        run_cmd(["room", "add", "--project", "1", "--name", "Main Hall", "--sqm", "50"])

    def test_add_task(self):
        run_cmd(["task", "add", "--project", "1", "--room", "Main Hall",
                 "--name", "Flooring", "--budget", "80000", "--contractor", "Wang"])
        data = ipm.load()
        tasks = data["projects"][0]["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["name"], "Flooring")
        self.assertEqual(tasks[0]["status"], "pending")
        self.assertEqual(tasks[0]["budget"], 80000)

    def test_mark_task_done(self):
        run_cmd(["task", "add", "--project", "1", "--name", "Demolition", "--budget", "20000"])
        run_cmd(["task", "done", "--project", "1", "--task-id", "1", "--cost", "19500"])
        data = ipm.load()
        task = data["projects"][0]["tasks"][0]
        self.assertEqual(task["status"], "done")
        self.assertEqual(task["actual_cost"], 19500)

    def test_task_status_transitions(self):
        run_cmd(["task", "add", "--project", "1", "--name", "Painting"])
        for status in ["in_progress", "blocked", "done"]:
            run_cmd(["task", "status", "--project", "1", "--task-id", "1", "--status", status])
            data = ipm.load()
            self.assertEqual(data["projects"][0]["tasks"][0]["status"], status)

    def test_add_notes_to_task(self):
        run_cmd(["task", "add", "--project", "1", "--name", "Ceiling work"])
        run_cmd(["task", "notes", "--project", "1", "--task-id", "1",
                 "--text", "Use moisture-resistant paint near windows."])
        data = ipm.load()
        self.assertEqual(
            data["projects"][0]["tasks"][0]["notes"],
            "Use moisture-resistant paint near windows.",
        )

    def test_task_requires_existing_room(self):
        with self.assertRaises(SystemExit):
            run_cmd(["task", "add", "--project", "1", "--room", "Nonexistent",
                     "--name", "Painting"])


class TestReport(unittest.TestCase):
    def setUp(self):
        _reset()
        run_cmd(["new", "Villa"])
        run_cmd(["room", "add", "--project", "1", "--name", "Bedroom", "--sqm", "20"])
        run_cmd(["task", "add", "--project", "1", "--room", "Bedroom",
                 "--name", "Flooring", "--budget", "30000"])
        run_cmd(["task", "add", "--project", "1", "--room", "Bedroom",
                 "--name", "Painting", "--budget", "10000"])
        run_cmd(["task", "done", "--project", "1", "--task-id", "1", "--cost", "28000"])

    def test_report_runs(self):
        # Just check it doesn't crash
        run_cmd(["report", "--project", "1"])

    def test_budget_totals(self):
        data = ipm.load()
        tasks = data["projects"][0]["tasks"]
        total_budget = sum(t["budget"] for t in tasks)
        total_actual = sum(t["actual_cost"] for t in tasks)
        self.assertEqual(total_budget, 40000)
        self.assertEqual(total_actual, 28000)


if __name__ == "__main__":
    unittest.main()
