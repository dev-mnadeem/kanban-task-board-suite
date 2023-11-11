"""Characterisation tests for the app's security posture.

These do not assert that the app is secure. They pin what is actually true
today so that the gap is visible in the suite rather than only in the README,
and so that anyone adding authentication has to come here and change them
deliberately.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings

from boards import dynamodb
from mini_trello_be.schema import schema


class TestNoTenancy:
    """The board is a single global collection with no owner.

    There is no user model, no login mutation and no per-card owner attribute,
    so "another user's card" is not a concept that exists. Every caller reads
    and writes the same cards. This is a real limitation, documented in the
    README, not something these tests are hiding.
    """

    def test_a_card_has_no_owner_attribute(self, service, card_table):
        card = service.create_card(title="Anyone's card")

        assert "owner" not in card
        assert "user_id" not in card

    def test_an_unauthenticated_caller_can_read_every_card(self, seeded, card_table):
        result = schema.execute("query { allCards { id } }")

        assert not result.errors
        assert len(result.data["allCards"]) == len(seeded)

    def test_an_unauthenticated_caller_can_delete_any_card(self, seeded, card_table):
        card_id = seeded[0]["id"]
        result = schema.execute(f'mutation {{ deleteCard(cardId: "{card_id}") {{ success }} }}')

        assert not result.errors
        assert result.data["deleteCard"]["success"] is True

    def test_the_schema_exposes_no_user_or_auth_fields(self):
        query_fields = set(schema.get_query_type().fields)
        mutation_fields = set(schema.get_mutation_type().fields)

        assert not {f for f in query_fields if "user" in f.lower() or f.lower() == "me"}
        assert not {
            f
            for f in mutation_fields
            if any(word in f.lower() for word in ("login", "token", "auth", "register"))
        }


class TestSettingsHardening:
    def test_the_secret_key_is_not_hardcoded_in_the_source(self):
        source = (Path(settings.BASE_DIR) / "mini_trello_be" / "settings.py").read_text()

        assert "django-insecure-a%thmamk8tj" not in source, "the committed key is back"
        assert 'os.environ.get("DJANGO_SECRET_KEY"' in source

    def test_a_missing_secret_key_is_fatal_when_debug_is_off(self):
        """Run in a subprocess: importing settings twice in-process would leave
        django.conf.settings holding a half-executed module."""
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "mini_trello_be.settings",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": "",
        }
        result = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            cwd=str(settings.BASE_DIR),
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "DJANGO_SECRET_KEY must be set" in result.stderr

    def test_a_supplied_secret_key_boots_with_debug_off(self):
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "mini_trello_be.settings",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": "a-real-key-supplied-by-the-environment",
        }
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import django;django.setup();"
                "from django.conf import settings;"
                "print(settings.DEBUG, settings.GRAPHIQL_ENABLED)",
            ],
            cwd=str(settings.BASE_DIR),
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        # GraphiQL must be off when DEBUG is off.
        assert result.stdout.strip() == "False False"

    def test_cors_middleware_runs_before_common_middleware(self):
        order = settings.MIDDLEWARE

        assert order.index("corsheaders.middleware.CorsMiddleware") < order.index(
            "django.middleware.common.CommonMiddleware"
        )

    def test_no_dead_auth_dependencies_remain(self):
        """django-graphql-jwt was configured as graphene middleware but no login
        mutation ever existed, and djangorestframework was installed and unused."""
        requirements = (Path(settings.BASE_DIR) / "requirements.txt").read_text()

        assert "graphql-jwt" not in requirements
        assert "djangorestframework" not in requirements
        assert "graphql_jwt" not in str(settings.GRAPHENE)


class TestNoNetworkAtImport:
    def test_the_dynamodb_client_is_built_lazily(self):
        """The original built a boto3 resource and a table handle at import time,
        pointed at the hostname 'dynamodb', which made the module unimportable
        outside docker compose and untestable anywhere."""
        dynamodb.reset_connection()

        assert dynamodb._resource is None

        # Importing the data-access layer must still not connect.
        from boards import repositories  # noqa: F401

        assert dynamodb._resource is None

    def test_the_repository_resolves_its_table_per_call(self, card_table):
        """This is what lets the suite point the whole app at a mock."""
        from boards.repositories import CardRepository

        repo = CardRepository()

        assert repo._table.name == dynamodb.CARD_TABLE_NAME
        assert "_table" not in repo.__dict__
