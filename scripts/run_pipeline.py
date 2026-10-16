#!/usr/bin/env python
"""Project root launcher for the single-command end-to-end QuickBooks financial analysis pipeline.

Usage:
    python scripts/run_pipeline.py [options]

Options:
    --offline, --cached  Use existing saved QuickBooks report without making live API requests.
    --thresholds, -t     Optional path to custom anomaly thresholds JSON configuration file.
    --quiet, -q          Suppress intermediate step progress output.
    --help, -h           Show options.
"""

import sys
from pathlib import Path

# Add abc-trend-analysis to sys.path so scripts can be imported cleanly
root_dir = Path(__file__).resolve().parent.parent
abc_dir = root_dir / "abc-trend-analysis"
if str(abc_dir) not in sys.path:
    sys.path.insert(0, str(abc_dir))

from scripts.run_pipeline import main

if __name__ == "__main__":
    sys.exit(main())
