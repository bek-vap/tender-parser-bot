#!/usr/bin/env python3
"""Create monitored_companies table if missing."""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine, tables=[models.MonitoredCompany.__table__])
    print("monitored_companies table OK")


if __name__ == "__main__":
    main()
