"""DynamoDB connection management.

The table handle is built lazily and cached. Two things depend on that:

* nothing connects to AWS at import time, so the module can be imported by
  tests, by ``manage.py`` and by ``django-admin check`` without a database;
* tests can point the whole app at an in-process mock by setting the endpoint
  environment variable and calling :func:`reset_connection`.
"""

from __future__ import annotations

import os
import threading
from typing import Any

import boto3
from botocore.config import Config

_lock = threading.Lock()
_resource: Any = None

#: Name of the single DynamoDB table backing the board.
CARD_TABLE_NAME = os.environ.get("DYNAMODB_CARD_TABLE", "Card")

#: Global secondary index used to read one lane without scanning the table.
CARD_STATUS_INDEX = "status-created_at-index"


def _settings() -> dict[str, Any]:
    """Read connection settings from the environment on every (re)connect."""
    return {
        "endpoint_url": os.environ.get("DYNAMODB_ENDPOINT_URL") or None,
        "region_name": os.environ.get("AWS_DEFAULT_REGION", "us-west-2"),
        "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
    }


def get_resource() -> Any:
    """Return the cached boto3 DynamoDB resource, creating it on first use."""
    global _resource
    if _resource is None:
        with _lock:
            if _resource is None:
                _resource = boto3.resource(
                    "dynamodb",
                    config=Config(retries={"max_attempts": 5, "mode": "standard"}),
                    **_settings(),
                )
    return _resource


def get_card_table() -> Any:
    """Return a handle to the Card table."""
    return get_resource().Table(CARD_TABLE_NAME)


def reset_connection() -> None:
    """Drop the cached resource so the next call re-reads the environment."""
    global _resource
    with _lock:
        _resource = None
