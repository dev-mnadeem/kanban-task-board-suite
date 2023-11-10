"""URL routing.

The API is a single GraphQL endpoint. GraphiQL, the in-browser explorer, is
enabled only when GRAPHIQL_ENABLED is on (it follows DEBUG by default).
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "graphql",
        csrf_exempt(GraphQLView.as_view(graphiql=settings.GRAPHIQL_ENABLED)),
        name="graphql",
    ),
]
