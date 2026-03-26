# Python Project

This repository contains a Python app with separate dashboards for students and mentors, backed by a local SQLite database.

## Files

- `main.py` - app entry point.
- `student_dashboard.py` - student-side dashboard logic.
- `mentor_dashboard.py` - mentor-side dashboard logic.
- `database.py` - database helper and data access utilities.
- `college.db` - local SQLite database file.

## Requirements

- Python 3.10+

## Run Locally

1. Open the project folder.
2. Run:

```bash
python main.py
```

## Notes

- The project currently uses a local database file (`college.db`).
- Keep sensitive or production data out of this file before sharing publicly.