#!/usr/bin/env python3
"""
Complete Schema Type Fix Script

This script identifies and documents all type mismatches between:
1. Database schema (UUID types)
2. SQLAlchemy models (UUID types)
3. Pydantic schemas (need to be UUID)

All ID fields should be UUID, not str!
"""

import os
import re

type_mismatches = [
    {
        "file": "app/projects/schemas.py",
        "class": "ProjectResponse",
        "field": "id",
        "current": "str",
        "correct": "uuid.UUID",
        "line_approx": 35
    },
    {
        "file": "app/projects/schemas.py",
        "class": "ModuleCreate",
        "field": "project_id",
        "current": "str",
        "correct": "uuid.UUID",
        "line_approx": 66
    },
    {
        "file": "app/projects/schemas.py",
        "class": "ModuleResponse",
        "field": "id",
        "current": "str",
        "correct": "uuid.UUID",
        "line_approx": 72
    },
    {
        "file": "app/projects/schemas.py",
        "class": "ModuleResponse",
        "field": "project_id",
        "current": "str",
        "correct": "uuid.UUID",
        "line_approx": 73
    },
    {
        "file": "app/modules/defects/schemas.py",
        "class": "DefectBase",
        "field": "module_id",
        "current": "Optional[str]",
        "correct": "Optional[uuid.UUID]",
        "line_approx": 20
    },
    {
        "file": "app/modules/defects/schemas.py",
        "class": "DefectCreate",
        "field": "project_id",
        "current": "str",
        "correct": "uuid.UUID",
        "line_approx": 48
    },
    {
        "file": "app/modules/defects/schemas.py",
        "class": "DefectUpdate",
        "field": "module_id",
        "current": "Optional[str]",
        "correct": "Optional[uuid.UUID]",
        "line_approx": 72
    },
    {
        "file": "app/modules/defects/schemas.py",
        "class": "DefectResponse",
        "field": "project_id",
        "current": "str",
        "correct": "uuid.UUID",
        "line_approx": 115
    },
]

if __name__ == "__main__":
    print("=" * 80)
    print("SCHEMA TYPE MISMATCH ANALYSIS")
    print("=" * 80)
    print()
    print("Found {} type mismatches that need to be fixed:\n".format(len(type_mismatches)))
    
    for i, mismatch in enumerate(type_mismatches, 1):
        print(f"{i}. {mismatch['file']}")
        print(f"   Class: {mismatch['class']}")
        print(f"   Field: {mismatch['field']}")
        print(f"   Current: {mismatch['current']} ❌")
        print(f"   Correct: {mismatch['correct']} ✅")
        print(f"   Line ~{mismatch['line_approx']}")
        print()
    
    print("=" * 80)
    print("ACTION REQUIRED:")
    print("=" * 80)
    print("All str ID fields need to be changed to uuid.UUID")
    print("This ensures Pydantic schemas match SQLAlchemy models and database types.")
    print()
    print("Use the edit_file tool to make these changes.")
    print("=" * 80)
