"""Create the Card table if it is not already there."""

from __future__ import annotations

from botocore.exceptions import ClientError, EndpointConnectionError
from django.core.management.base import BaseCommand, CommandError

from boards import dynamodb


class Command(BaseCommand):
    help = "Create the DynamoDB Card table. Safe to run repeatedly."

    def handle(self, *args, **options):
        resource = dynamodb.get_resource()
        table_name = dynamodb.CARD_TABLE_NAME

        try:
            table = resource.create_table(
                TableName=table_name,
                KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
        except EndpointConnectionError as exc:
            raise CommandError(
                f"Cannot reach DynamoDB at {dynamodb._settings()['endpoint_url']!r}. "
                "Is DYNAMODB_ENDPOINT_URL correct and the service running?"
            ) from exc
        except ClientError as exc:
            # The original script called create_table at import time with no
            # error handling, so the container entrypoint crashed on every boot
            # after the first with ResourceInUseException.
            if exc.response["Error"]["Code"] == "ResourceInUseException":
                self.stdout.write(f"Table {table_name!r} already exists; nothing to do.")
                return
            raise

        table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
        self.stdout.write(self.style.SUCCESS(f"Created table {table_name!r}."))
