# Interior Project Manager

A lightweight CLI tool for tracking interior design projects — rooms, tasks, budgets, and contractors.

## Features

- Track multiple projects with rooms and phases
- Manage tasks per room (demolition, flooring, painting, fixtures, etc.)
- Log budgets and actual costs
- Assign contractors to tasks
- Generate a project status report

## Requirements

- Python 3.8+

## Quick Start

```bash
python ipm.py --help
```

### Create a project

```bash
python ipm.py new "Taipei Apartment Renovation"
```

### Add a room

```bash
python ipm.py room add --project 1 --name "Living Room" --sqm 32
```

### Add a task

```bash
python ipm.py task add --project 1 --room "Living Room" \
  --name "Flooring" --budget 45000 --contractor "張師傅" --due 2026-08-15
```

### Update task status

```bash
python ipm.py task done --project 1 --task-id 3
```

### Add notes to a task

```bash
python ipm.py task notes --project 1 --task-id 2 \
  --text "Use moisture-resistant paint near windows."
```

### Show project report

```bash
python ipm.py report --project 1
```

## Data

All data is stored locally in `projects.json` in the same directory. No account or internet required.
