# API examples

Captured against a live backend on 2026-09-25 with the stack described in the
README's "Running without Docker" section (moto DynamoDB on 8785, Django on 8781).
Every block below is literal terminal output.

## Fetch the board (lanes + cards)

```console
$ curl -s -X POST http://localhost:8781/graphql -H 'Content-Type: application/json' \
    -d '{"query":"{ lanes { id title position } cardPage(limit: 2) { cards { id title status } nextCursor hasNextPage } }"}' | python -m json.tool
{
    "data": {
        "lanes": [
            {
                "id": "todo",
                "title": "To Do",
                "position": 0
            },
            {
                "id": "in-progress",
                "title": "In Progress",
                "position": 1
            },
            {
                "id": "done",
                "title": "Done",
                "position": 2
            }
        ],
        "cardPage": {
            "cards": [
                {
                    "id": "150bd1b9-04b2-445e-a038-b20aa8d85e4f",
                    "title": "Move the Django secret key to the environment",
                    "status": "done"
                },
                {
                    "id": "3368250b-6a9e-4bdc-a7c6-ba5f8f49af58",
                    "title": "Add pagination to the card list",
                    "status": "todo"
                }
            ],
            "nextCursor": "eyJpZCI6ICIzMzY4MjUwYi02YTllLTRiZGMtYTdjNi1iYTVmOGY0OWFmNTgifQ==",
            "hasNextPage": true
        }
    }
}
```

## Validation errors come back as GraphQL errors, not 500s

```console
$ curl -s -X POST http://localhost:8781/graphql -H 'Content-Type: application/json' \
    -d '{"query":"mutation { createCard(title: \"x\", status: \"nowhere\") { card { id } } }"}' | python -m json.tool
{
    "errors": [
        {
            "message": "Unknown status 'nowhere'. Expected one of: todo, in-progress, done.",
            "locations": [
                {
                    "line": 1,
                    "column": 12
                }
            ],
            "path": [
                "createCard"
            ]
        }
    ],
    "data": {
        "createCard": null
    }
}
```

## An unknown card id returns null rather than crashing

```console
$ curl -s -X POST http://localhost:8781/graphql -H 'Content-Type: application/json' \
    -d '{"query":"{ card(id: \"does-not-exist\") { id title } }"}' | python -m json.tool
{
    "data": {
        "card": null
    }
}
```

## Deleting a card that is not there reports failure

```console
$ curl -s -X POST http://localhost:8781/graphql -H 'Content-Type: application/json' \
    -d '{"query":"mutation { deleteCard(cardId: \"does-not-exist\") { success } }"}' | python -m json.tool
{
    "data": {
        "deleteCard": {
            "success": false
        }
    }
}
```
