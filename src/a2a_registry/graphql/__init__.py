"""GraphQL module for A2A Registry AgentExtension system."""

from .app import create_graphql_app
from .resolvers import Mutation, Query, Subscription
from .schema import schema

__all__ = ["create_graphql_app", "Query", "Mutation", "Subscription", "schema"]
