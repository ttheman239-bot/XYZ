"""Entry point: python -m live_host --config config/config.yaml --product samples/product.json"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from .orchestrator import Orchestrator


def main() -> None:
    p = argparse.ArgumentParser(description="Thai AI Live Host — orchestrator")
    p.add_argument("--config", type=Path, default=Path("config/config.yaml"))
    p.add_argument("--product", type=Path, required=True,
                   help="product info JSON (name, price, highlights, product_id, ...)")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    if not args.config.exists():
        print(f"ไม่พบ config: {args.config} — สร้างจาก config/config.example.yaml", file=sys.stderr)
        sys.exit(2)

    product = json.loads(args.product.read_text(encoding="utf-8"))
    orch = Orchestrator(args.config)
    asyncio.run(orch.run_product(product))


if __name__ == "__main__":
    main()
