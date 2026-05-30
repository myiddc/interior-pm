#!/usr/bin/env python3
"""Interior Project Manager — CLI tool for tracking interior design projects."""

import argparse
import json
import os
import sys
from datetime import date, datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "projects.json")

TASK_STATUSES = ["pending", "in_progress", "done", "blocked"]


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"projects": [], "_next_project_id": 1, "_next_task_id": 1}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_project(data: dict, project_id: int) -> dict | None:
    return next((p for p in data["projects"] if p["id"] == project_id), None)


def find_room(project: dict, room_name: str) -> dict | None:
    return next((r for r in project["rooms"] if r["name"] == room_name), None)


def today() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_new(args, data):
    project = {
        "id": data["_next_project_id"],
        "name": args.name,
        "created": today(),
        "rooms": [],
        "tasks": [],
    }
    data["_next_project_id"] += 1
    data["projects"].append(project)
    save(data)
    print(f"Created project #{project['id']}: {project['name']}")


def cmd_list_projects(args, data):
    if not data["projects"]:
        print("No projects yet. Use: python ipm.py new \"Project Name\"")
        return
    for p in data["projects"]:
        task_count = len(p["tasks"])
        done_count = sum(1 for t in p["tasks"] if t["status"] == "done")
        print(f"  [{p['id']}] {p['name']}  ({done_count}/{task_count} tasks done)  created {p['created']}")


def cmd_room_add(args, data):
    project = find_project(data, args.project)
    if not project:
        sys.exit(f"Project #{args.project} not found.")
    if find_room(project, args.name):
        sys.exit(f"Room '{args.name}' already exists in this project.")
    project["rooms"].append({"name": args.name, "sqm": args.sqm})
    save(data)
    print(f"Added room '{args.name}' ({args.sqm} m²) to project #{args.project}.")


def cmd_room_list(args, data):
    project = find_project(data, args.project)
    if not project:
        sys.exit(f"Project #{args.project} not found.")
    if not project["rooms"]:
        print("No rooms yet.")
        return
    for r in project["rooms"]:
        tasks = [t for t in project["tasks"] if t["room"] == r["name"]]
        done = sum(1 for t in tasks if t["status"] == "done")
        print(f"  {r['name']}  ({r['sqm']} m²)  tasks: {done}/{len(tasks)} done")


def cmd_task_add(args, data):
    project = find_project(data, args.project)
    if not project:
        sys.exit(f"Project #{args.project} not found.")
    if args.room and not find_room(project, args.room):
        sys.exit(f"Room '{args.room}' not found. Add it first with: python ipm.py room add ...")
    task = {
        "id": data["_next_task_id"],
        "project_id": args.project,
        "room": args.room or "",
        "name": args.name,
        "status": "pending",
        "budget": args.budget or 0,
        "actual_cost": 0,
        "contractor": args.contractor or "",
        "due": args.due or "",
        "notes": "",
        "created": today(),
    }
    data["_next_task_id"] += 1
    project["tasks"].append(task)
    save(data)
    print(f"Added task #{task['id']}: {task['name']} ({task['room'] or 'no room'})")


def cmd_task_list(args, data):
    project = find_project(data, args.project)
    if not project:
        sys.exit(f"Project #{args.project} not found.")
    tasks = project["tasks"]
    if args.room:
        tasks = [t for t in tasks if t["room"] == args.room]
    if not tasks:
        print("No tasks found.")
        return
    for t in tasks:
        budget_str = f"  budget {t['budget']:,}" if t["budget"] else ""
        cost_str = f"  actual {t['actual_cost']:,}" if t["actual_cost"] else ""
        due_str = f"  due {t['due']}" if t["due"] else ""
        contractor_str = f"  [{t['contractor']}]" if t["contractor"] else ""
        print(f"  #{t['id']} [{t['status']:11}] {t['name']}{contractor_str}{budget_str}{cost_str}{due_str}")


def cmd_task_status(args, data):
    project = find_project(data, args.project)
    if not project:
        sys.exit(f"Project #{args.project} not found.")
    task = next((t for t in project["tasks"] if t["id"] == args.task_id), None)
    if not task:
        sys.exit(f"Task #{args.task_id} not found.")
    if args.status not in TASK_STATUSES:
        sys.exit(f"Status must be one of: {', '.join(TASK_STATUSES)}")
    old = task["status"]
    task["status"] = args.status
    if args.cost is not None:
        task["actual_cost"] = args.cost
    save(data)
    print(f"Task #{task['id']} '{task['name']}': {old} → {task['status']}")


def cmd_task_done(args, data):
    args.status = "done"
    cmd_task_status(args, data)


def cmd_report(args, data):
    project = find_project(data, args.project)
    if not project:
        sys.exit(f"Project #{args.project} not found.")

    tasks = project["tasks"]
    total_budget = sum(t["budget"] for t in tasks)
    total_actual = sum(t["actual_cost"] for t in tasks)
    by_status = {s: [] for s in TASK_STATUSES}
    for t in tasks:
        by_status[t["status"]].append(t)

    print(f"\n{'='*60}")
    print(f"  Project #{project['id']}: {project['name']}")
    print(f"  Created: {project['created']}")
    print(f"{'='*60}")
    print(f"  Rooms   : {len(project['rooms'])}")
    print(f"  Tasks   : {len(tasks)}")
    print(f"  Budget  : {total_budget:>12,}")
    print(f"  Actual  : {total_actual:>12,}  ({total_actual - total_budget:+,} variance)")

    for status in TASK_STATUSES:
        t_list = by_status[status]
        if t_list:
            print(f"\n  {status.upper().replace('_', ' ')} ({len(t_list)})")
            for t in t_list:
                due = f"  due {t['due']}" if t["due"] else ""
                contractor = f"  [{t['contractor']}]" if t["contractor"] else ""
                room = f"  ({t['room']})" if t["room"] else ""
                print(f"    #{t['id']} {t['name']}{room}{contractor}{due}")
    print()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ipm",
        description="Interior Project Manager",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # new
    p_new = sub.add_parser("new", help="Create a new project")
    p_new.add_argument("name", help="Project name")

    # list
    sub.add_parser("list", help="List all projects")

    # room
    p_room = sub.add_parser("room", help="Manage rooms")
    room_sub = p_room.add_subparsers(dest="room_command", required=True)

    p_room_add = room_sub.add_parser("add", help="Add a room")
    p_room_add.add_argument("--project", type=int, required=True)
    p_room_add.add_argument("--name", required=True)
    p_room_add.add_argument("--sqm", type=float, default=0)

    p_room_list = room_sub.add_parser("list", help="List rooms")
    p_room_list.add_argument("--project", type=int, required=True)

    # task
    p_task = sub.add_parser("task", help="Manage tasks")
    task_sub = p_task.add_subparsers(dest="task_command", required=True)

    p_task_add = task_sub.add_parser("add", help="Add a task")
    p_task_add.add_argument("--project", type=int, required=True)
    p_task_add.add_argument("--room")
    p_task_add.add_argument("--name", required=True)
    p_task_add.add_argument("--budget", type=int)
    p_task_add.add_argument("--contractor")
    p_task_add.add_argument("--due", help="Due date (YYYY-MM-DD)")

    p_task_list = task_sub.add_parser("list", help="List tasks")
    p_task_list.add_argument("--project", type=int, required=True)
    p_task_list.add_argument("--room")

    p_task_status = task_sub.add_parser("status", help="Update task status")
    p_task_status.add_argument("--project", type=int, required=True)
    p_task_status.add_argument("--task-id", type=int, required=True)
    p_task_status.add_argument("--status", required=True, choices=TASK_STATUSES)
    p_task_status.add_argument("--cost", type=int, help="Record actual cost")

    p_task_done = task_sub.add_parser("done", help="Mark task as done")
    p_task_done.add_argument("--project", type=int, required=True)
    p_task_done.add_argument("--task-id", type=int, required=True)
    p_task_done.add_argument("--cost", type=int, help="Record actual cost")

    # report
    p_report = sub.add_parser("report", help="Show project report")
    p_report.add_argument("--project", type=int, required=True)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    data = load()

    dispatch = {
        "new": cmd_new,
        "list": cmd_list_projects,
        "report": cmd_report,
    }

    if args.command in dispatch:
        dispatch[args.command](args, data)
    elif args.command == "room":
        {"add": cmd_room_add, "list": cmd_room_list}[args.room_command](args, data)
    elif args.command == "task":
        {"add": cmd_task_add, "list": cmd_task_list,
         "status": cmd_task_status, "done": cmd_task_done}[args.task_command](args, data)


if __name__ == "__main__":
    main()
