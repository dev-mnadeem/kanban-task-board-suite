"""Test fixtures.

Every test runs against moto's in-process DynamoDB. Nothing here touches the
network, AWS, or Docker, and no test makes a paid API call.
"""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from boards import dynamodb
from boards.repositories import CardRepository
from boards.services import CardService


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    """Fake credentials, and make sure no test can reach a real endpoint."""
    for name, value in {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_DEFAULT_REGION": "us-west-2",
    }.items():
        monkeypatch.setenv(name, value)
    # An endpoint override would bypass moto and hit whatever is listening.
    monkeypatch.delenv("DYNAMODB_ENDPOINT_URL", raising=False)


@pytest.fixture
def card_table(aws_credentials):
    """A freshly created, empty Card table, wired into the app's connection."""
    with mock_aws():
        dynamodb.reset_connection()
        client = boto3.resource("dynamodb", region_name="us-west-2")
        table = client.create_table(
            TableName=dynamodb.CARD_TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=dynamodb.CARD_TABLE_NAME)
        yield table
        dynamodb.reset_connection()


@pytest.fixture
def repository(card_table) -> CardRepository:
    return CardRepository()


@pytest.fixture
def service(repository) -> CardService:
    return CardService(repository)


@pytest.fixture
def seeded(service):
    """Three cards, one in each lane."""
    return [
        service.create_card(title="Write the spec", description="One pager", status="todo"),
        service.create_card(title="Build it", description="", status="in-progress"),
        service.create_card(title="Ship it", description="", status="done"),
    ]
