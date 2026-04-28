import json
import logging
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from botocore.exceptions import ClientError

from spillway.aws.client import get_securityhub_client
from spillway.aws.filters import _build_filters
from spillway.config import SpillwayConfig

logger = logging.getLogger(__name__)


def get_findings(config: SpillwayConfig) -> Iterator[dict[str, Any]]:
    """
    Yields active findings.
    If SPILLWAY_ENV=local, it reads from a local JSON file instead of calling AWS.
    """

    if os.getenv("SPILLWAY_ENV", "production").lower() == "local":
        dummy_file = Path("dummy_findings.json")

        if not dummy_file.exists():
            raise FileNotFoundError(
                f"Local mode enabled, but '{dummy_file}' is missing."
            )

        with dummy_file.open("r") as f:
            data = json.load(f)
            yield from data.get("Findings", [])

        return

    boto_filters = _build_filters(config)
    client = get_securityhub_client(region=config.region, profile=config.profile)

    try:
        paginator = client.get_paginator("get_findings_v2")
        page_iterator = paginator.paginate(Filters=boto_filters)

        for page in page_iterator:
            yield from page.get("Findings", [])

    except ClientError as e:
        logger.error(f"AWS API Error: {e.response['Error']['Message']}")
        raise
