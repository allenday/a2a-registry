"""Pagination utilities for GraphQL queries."""

import base64
import json
from typing import Any, Optional

from .types import AgentExtension, ExtensionConnection, ExtensionEdge, PageInfo


def encode_cursor(data: dict[str, Any]) -> str:
    """Encode cursor data to base64 string."""
    json_str = json.dumps(data, default=str)
    return base64.b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode base64 cursor to data dictionary."""
    try:
        json_str = base64.b64decode(cursor.encode()).decode()
        result = json.loads(json_str)
        if not isinstance(result, dict):
            raise ValueError(f"Invalid cursor data: expected dict, got {type(result)}")
        return result
    except Exception:
        return {}


def create_cursor_from_extension(extension: AgentExtension) -> str:
    """Create cursor from extension data."""
    return encode_cursor(
        {
            "id": extension.id,
            "created_at": extension.created_at.isoformat(),
            "name": extension.name,
        }
    )


def create_connection(
    extensions: list[AgentExtension],
    first: Optional[int] = None,
    after: Optional[str] = None,
    last: Optional[int] = None,
    before: Optional[str] = None,
    total_count: Optional[int] = None,
) -> ExtensionConnection:
    """Create paginated connection from extension list."""

    if not extensions:
        return ExtensionConnection(
            edges=[],
            page_info=PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
                total_count=total_count or 0,
            ),
        )

    # Create edges
    edges = []
    for extension in extensions:
        cursor = create_cursor_from_extension(extension)
        edges.append(ExtensionEdge(node=extension, cursor=cursor))

    # Determine pagination info
    has_next_page = False
    has_previous_page = False
    start_cursor = edges[0].cursor if edges else None
    end_cursor = edges[-1].cursor if edges else None

    # Calculate pagination flags
    if first is not None:
        # Forward pagination
        has_next_page = len(extensions) == first
        has_previous_page = after is not None
    elif last is not None:
        # Backward pagination
        has_previous_page = len(extensions) == last
        has_next_page = before is not None

    return ExtensionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
            total_count=total_count or len(extensions),
        ),
    )


class PaginationHelper:
    """Helper class for handling complex pagination scenarios."""

    @staticmethod
    def validate_pagination_args(
        first: Optional[int],
        after: Optional[str],
        last: Optional[int],
        before: Optional[str],
    ) -> list[str]:
        """Validate pagination arguments."""
        errors = []

        # Can't use both first/after and last/before
        if (first is not None or after is not None) and (
            last is not None or before is not None
        ):
            errors.append("Cannot use both forward and backward pagination")

        # Validate limits
        max_limit = 100
        if first is not None and (first <= 0 or first > max_limit):
            errors.append(f"'first' must be between 1 and {max_limit}")

        if last is not None and (last <= 0 or last > max_limit):
            errors.append(f"'last' must be between 1 and {max_limit}")

        return errors

    @staticmethod
    def parse_pagination_args(
        first: Optional[int],
        after: Optional[str],
        last: Optional[int],
        before: Optional[str],
    ) -> tuple[int, int, str]:
        """Parse pagination arguments into limit, offset, and direction."""

        limit = 20  # default
        offset = 0
        direction = "forward"

        if first is not None:
            limit = min(first, 100)
            direction = "forward"

            if after:
                cursor_data = decode_cursor(after)
                # In a real implementation, convert cursor to offset
                # For now, assume cursor contains offset information
                offset = cursor_data.get("offset", 0)

        elif last is not None:
            limit = min(last, 100)
            direction = "backward"

            if before:
                cursor_data = decode_cursor(before)
                offset = cursor_data.get("offset", 0)

        return limit, offset, direction

    @staticmethod
    def apply_cursor_conditions(
        query_conditions: dict[str, Any],
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> dict[str, Any]:
        """Apply cursor-based filtering to query conditions."""

        if after:
            cursor_data = decode_cursor(after)
            if "created_at" in cursor_data:
                # Add condition for items created after cursor
                query_conditions["created_at__gt"] = cursor_data["created_at"]
            elif "id" in cursor_data:
                # Fallback to ID-based pagination
                query_conditions["id__gt"] = cursor_data["id"]

        if before:
            cursor_data = decode_cursor(before)
            if "created_at" in cursor_data:
                query_conditions["created_at__lt"] = cursor_data["created_at"]
            elif "id" in cursor_data:
                query_conditions["id__lt"] = cursor_data["id"]

        return query_conditions


async def paginate_results(
    storage_service: Any,
    search_params: dict[str, Any],
    first: Optional[int] = None,
    after: Optional[str] = None,
    last: Optional[int] = None,
    before: Optional[str] = None,
    sort_field: str = "created_at",
    sort_direction: str = "desc",
) -> tuple[list[AgentExtension], int]:
    """Generic pagination helper for storage queries."""

    # Validate pagination arguments
    pagination_helper = PaginationHelper()
    errors = pagination_helper.validate_pagination_args(first, after, last, before)
    if errors:
        raise ValueError(f"Pagination errors: {', '.join(errors)}")

    # Parse pagination parameters
    limit, offset, direction = pagination_helper.parse_pagination_args(
        first, after, last, before
    )

    # Apply cursor conditions
    query_conditions = pagination_helper.apply_cursor_conditions(
        search_params, after, before
    )

    # Adjust sort direction for backward pagination
    if direction == "backward":
        sort_direction = "asc" if sort_direction == "desc" else "desc"

    # Execute query
    results = await storage_service.search_extensions(
        conditions=query_conditions,
        limit=limit + 1,  # Request one extra to determine if there are more results
        offset=offset,
        sort_field=sort_field,
        sort_direction=sort_direction,
    )

    # Check if there are more results
    has_more = len(results) > limit
    if has_more:
        results = results[:limit]

    # Reverse results for backward pagination
    if direction == "backward":
        results.reverse()

    # Get total count for page info
    total_count = await storage_service.count_extensions(search_params)

    return results, total_count


# Specialized pagination for different query types
class ExtensionPaginator:
    """Specialized paginator for extension queries."""

    def __init__(self, storage_service: Any) -> None:
        self.storage = storage_service

    async def paginate_search(
        self,
        search_input: Any,
        sort_input: Any,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> ExtensionConnection:
        """Paginate extension search results."""

        # Convert search input to query parameters
        search_params = self._convert_search_input(search_input)

        # Determine sort parameters
        sort_field = sort_input.field.value if sort_input else "created_at"
        sort_direction = sort_input.direction.value if sort_input else "desc"

        # Execute paginated query
        results, total_count = await paginate_results(
            self.storage,
            search_params,
            first,
            after,
            last,
            before,
            sort_field,
            sort_direction,
        )

        return create_connection(results, first, after, last, before, total_count)

    async def paginate_dependencies(
        self,
        extension_id: str,
        first: Optional[int] = None,
        after: Optional[str] = None,
    ) -> ExtensionConnection:
        """Paginate extension dependencies."""

        # Get dependencies
        dependencies = await self.storage.get_dependencies(extension_id)

        # Resolve dependency extensions
        dependency_ids = [dep.extension_id for dep in dependencies]
        extensions = await self.storage.get_extensions_by_ids(dependency_ids)

        # Apply pagination
        if first and after:
            cursor_data = decode_cursor(after)
            start_index = cursor_data.get("index", 0)
            extensions = extensions[start_index : start_index + first]
        elif first:
            extensions = extensions[:first]

        return create_connection(extensions, first, after)

    def _convert_search_input(self, search_input: Any) -> dict[str, Any]:
        """Convert GraphQL search input to storage query parameters."""
        params: dict[str, Any] = {}

        if not search_input:
            return params

        if search_input.query:
            params["text_search"] = search_input.query

        if search_input.types:
            params["types"] = [t.value for t in search_input.types]

        if search_input.trust_levels:
            params["trust_levels"] = [tl.value for tl in search_input.trust_levels]

        if search_input.tags:
            params["tags"] = search_input.tags

        if search_input.author:
            params["author"] = search_input.author

        if search_input.min_downloads:
            params["min_downloads"] = search_input.min_downloads

        if search_input.published_after:
            params["published_after"] = search_input.published_after

        if search_input.published_before:
            params["published_before"] = search_input.published_before

        return params


# Cursor-based pagination for real-time subscriptions
class SubscriptionPaginator:
    """Paginator for real-time subscription data."""

    def __init__(self, max_buffer_size: int = 1000):
        self.max_buffer_size = max_buffer_size
        self.event_buffer: list[Any] = []

    def add_event(self, event: Any) -> None:
        """Add event to buffer with size management."""
        self.event_buffer.append(event)

        # Maintain buffer size
        if len(self.event_buffer) > self.max_buffer_size:
            self.event_buffer = self.event_buffer[-self.max_buffer_size :]

    def get_events_after_cursor(
        self, cursor: Optional[str], limit: int = 50
    ) -> list[Any]:
        """Get events after a specific cursor."""

        if not cursor:
            return self.event_buffer[:limit]

        cursor_data = decode_cursor(cursor)
        timestamp = cursor_data.get("timestamp")

        if not timestamp:
            return self.event_buffer[:limit]

        # Filter events after timestamp
        filtered_events = [
            event
            for event in self.event_buffer
            if getattr(event, "timestamp", None) and event.timestamp > timestamp
        ]

        return filtered_events[:limit]
