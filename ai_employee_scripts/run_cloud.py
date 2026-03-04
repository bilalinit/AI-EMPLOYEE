#!/usr/bin/env python3
"""
Cloud Orchestrator Runner
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cloud.cloud_orchestrator import main

if __name__ == "__main__":
    asyncio.run(main())
