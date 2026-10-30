from __future__ import annotations

import asyncio
import json

from supportops.mcp_client import run_demo

if __name__ == "__main__":
    print(json.dumps(asyncio.run(run_demo()), indent=2, default=str))
