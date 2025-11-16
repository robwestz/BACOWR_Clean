#!/usr/bin/env python3
"""
Simple Task Runner for BACOWR

Usage:
    python tools/run_task.py T1
    python tools/run_task.py T4

This script prints a composed prompt that you can copy-paste into a LLM:
- A short system context
- The full MODULES_AND_TASKS.md
- A note about which task (e.g. T4) should be implemented now
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/run_task.py <TASK_ID>")
        print("Example: python tools/run_task.py T3")
        sys.exit(1)

    task_id = sys.argv[1].strip().upper()
    tasks_file = ROOT / "MODULES_AND_TASKS.md"

    if not tasks_file.exists():
        print("ERROR: MODULES_AND_TASKS.md not found at project root.")
        sys.exit(1)

    tasks_text = tasks_file.read_text(encoding="utf-8")

    system_context = f\"\"\"You are a senior Python backend engineer.
You are working in the BACOWR project (Backlink Content Writer).

You MUST:
- Read and follow the architecture and constraints from MODULES_AND_TASKS.md
- Implement EXACTLY ONE task: {task_id}
- NOT change scope, add features or modify other tasks
- Deliver working, self-contained code for this task only
- Make reasonable assumptions without asking questions if something is underspecified

\"\"\"

    prompt = []
    prompt.append(system_context)
    prompt.append("=== BEGIN MODULES_AND_TASKS.md ===")
    prompt.append(tasks_text)
    prompt.append("=== END MODULES_AND_TASKS.md ===")
    prompt.append("")
    prompt.append(f"Your current task is: {task_id}")
    prompt.append("")
    prompt.append("Instructions for this response:")
    prompt.append("1. Briefly restate what you will implement (3–5 bullet points).")
    prompt.append("2. Then output the full code for any new/updated files.")
    prompt.append("3. Do NOT propose new features or modify the scope beyond this task.")
    prompt.append("4. If you must make an assumption, add a short comment in the code explaining it.")

    print(\"\\n\".join(prompt))


if __name__ == \"__main__\":
    main()
