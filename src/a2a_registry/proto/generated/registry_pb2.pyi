import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import empty_pb2 as _empty_pb2
import a2a_pb2 as _a2a_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HealthStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HEALTH_UNKNOWN: _ClassVar[HealthStatus]
    HEALTH_HEALTHY: _ClassVar[HealthStatus]
    HEALTH_DEGRADED: _ClassVar[HealthStatus]
    HEALTH_UNHEALTHY: _ClassVar[HealthStatus]
    HEALTH_OFFLINE: _ClassVar[HealthStatus]
HEALTH_UNKNOWN: HealthStatus
HEALTH_HEALTHY: HealthStatus
HEALTH_DEGRADED: HealthStatus
HEALTH_UNHEALTHY: HealthStatus
HEALTH_OFFLINE: HealthStatus

class AgentRegistration(_message.Message):
    __slots__ = ("agent_id", "agent_card", "registered_at", "last_seen", "last_health_check", "health_status", "metadata", "tags", "domains", "endpoints")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_CARD_FIELD_NUMBER: _ClassVar[int]
    REGISTERED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_SEEN_FIELD_NUMBER: _ClassVar[int]
    LAST_HEALTH_CHECK_FIELD_NUMBER: _ClassVar[int]
    HEALTH_STATUS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    DOMAINS_FIELD_NUMBER: _ClassVar[int]
    ENDPOINTS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    agent_card: _a2a_pb2.AgentCard
    registered_at: _timestamp_pb2.Timestamp
    last_seen: _timestamp_pb2.Timestamp
    last_health_check: _timestamp_pb2.Timestamp
    health_status: HealthStatus
    metadata: _struct_pb2.Struct
    tags: _containers.RepeatedScalarFieldContainer[str]
    domains: _containers.RepeatedScalarFieldContainer[str]
    endpoints: _containers.RepeatedCompositeFieldContainer[NetworkEndpoint]
    def __init__(self, agent_id: _Optional[str] = ..., agent_card: _Optional[_Union[_a2a_pb2.AgentCard, _Mapping]] = ..., registered_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., last_seen: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., last_health_check: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., health_status: _Optional[_Union[HealthStatus, str]] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ..., domains: _Optional[_Iterable[str]] = ..., endpoints: _Optional[_Iterable[_Union[NetworkEndpoint, _Mapping]]] = ...) -> None: ...

class NetworkEndpoint(_message.Message):
    __slots__ = ("address", "port", "protocol", "is_primary", "metadata")
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    IS_PRIMARY_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    address: str
    port: int
    protocol: str
    is_primary: bool
    metadata: _struct_pb2.Struct
    def __init__(self, address: _Optional[str] = ..., port: _Optional[int] = ..., protocol: _Optional[str] = ..., is_primary: bool = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class HealthInfo(_message.Message):
    __slots__ = ("status", "message", "timestamp", "metrics")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    METRICS_FIELD_NUMBER: _ClassVar[int]
    status: HealthStatus
    message: str
    timestamp: _timestamp_pb2.Timestamp
    metrics: _struct_pb2.Struct
    def __init__(self, status: _Optional[_Union[HealthStatus, str]] = ..., message: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., metrics: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class RegisterAgentRequest(_message.Message):
    __slots__ = ("agent_card", "tags", "domains", "endpoints", "metadata", "agent_id")
    AGENT_CARD_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    DOMAINS_FIELD_NUMBER: _ClassVar[int]
    ENDPOINTS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    agent_card: _a2a_pb2.AgentCard
    tags: _containers.RepeatedScalarFieldContainer[str]
    domains: _containers.RepeatedScalarFieldContainer[str]
    endpoints: _containers.RepeatedCompositeFieldContainer[NetworkEndpoint]
    metadata: _struct_pb2.Struct
    agent_id: str
    def __init__(self, agent_card: _Optional[_Union[_a2a_pb2.AgentCard, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ..., domains: _Optional[_Iterable[str]] = ..., endpoints: _Optional[_Iterable[_Union[NetworkEndpoint, _Mapping]]] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., agent_id: _Optional[str] = ...) -> None: ...

class RegisterAgentResponse(_message.Message):
    __slots__ = ("agent_id", "registration", "created")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    registration: AgentRegistration
    created: bool
    def __init__(self, agent_id: _Optional[str] = ..., registration: _Optional[_Union[AgentRegistration, _Mapping]] = ..., created: bool = ...) -> None: ...

class UpdateAgentRequest(_message.Message):
    __slots__ = ("agent_id", "agent_card", "tags", "domains", "endpoints", "metadata")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_CARD_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    DOMAINS_FIELD_NUMBER: _ClassVar[int]
    ENDPOINTS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    agent_card: _a2a_pb2.AgentCard
    tags: _containers.RepeatedScalarFieldContainer[str]
    domains: _containers.RepeatedScalarFieldContainer[str]
    endpoints: _containers.RepeatedCompositeFieldContainer[NetworkEndpoint]
    metadata: _struct_pb2.Struct
    def __init__(self, agent_id: _Optional[str] = ..., agent_card: _Optional[_Union[_a2a_pb2.AgentCard, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ..., domains: _Optional[_Iterable[str]] = ..., endpoints: _Optional[_Iterable[_Union[NetworkEndpoint, _Mapping]]] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class UpdateAgentResponse(_message.Message):
    __slots__ = ("registration",)
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    registration: AgentRegistration
    def __init__(self, registration: _Optional[_Union[AgentRegistration, _Mapping]] = ...) -> None: ...

class GetAgentRequest(_message.Message):
    __slots__ = ("agent_id", "include_health_history")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_HEALTH_HISTORY_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    include_health_history: bool
    def __init__(self, agent_id: _Optional[str] = ..., include_health_history: bool = ...) -> None: ...

class GetAgentResponse(_message.Message):
    __slots__ = ("registration", "health_history")
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    HEALTH_HISTORY_FIELD_NUMBER: _ClassVar[int]
    registration: AgentRegistration
    health_history: _containers.RepeatedCompositeFieldContainer[HealthInfo]
    def __init__(self, registration: _Optional[_Union[AgentRegistration, _Mapping]] = ..., health_history: _Optional[_Iterable[_Union[HealthInfo, _Mapping]]] = ...) -> None: ...

class SearchAgentsRequest(_message.Message):
    __slots__ = ("query", "tags", "domains", "capabilities", "skill_ids", "health_statuses", "page_size", "page_token", "sort_by", "sort_desc")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    DOMAINS_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    SKILL_IDS_FIELD_NUMBER: _ClassVar[int]
    HEALTH_STATUSES_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SORT_BY_FIELD_NUMBER: _ClassVar[int]
    SORT_DESC_FIELD_NUMBER: _ClassVar[int]
    query: str
    tags: _containers.RepeatedScalarFieldContainer[str]
    domains: _containers.RepeatedScalarFieldContainer[str]
    capabilities: _containers.RepeatedScalarFieldContainer[str]
    skill_ids: _containers.RepeatedScalarFieldContainer[str]
    health_statuses: _containers.RepeatedScalarFieldContainer[HealthStatus]
    page_size: int
    page_token: str
    sort_by: str
    sort_desc: bool
    def __init__(self, query: _Optional[str] = ..., tags: _Optional[_Iterable[str]] = ..., domains: _Optional[_Iterable[str]] = ..., capabilities: _Optional[_Iterable[str]] = ..., skill_ids: _Optional[_Iterable[str]] = ..., health_statuses: _Optional[_Iterable[_Union[HealthStatus, str]]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ..., sort_by: _Optional[str] = ..., sort_desc: bool = ...) -> None: ...

class SearchAgentsResponse(_message.Message):
    __slots__ = ("agents", "next_page_token", "total_count")
    AGENTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    agents: _containers.RepeatedCompositeFieldContainer[AgentRegistration]
    next_page_token: str
    total_count: int
    def __init__(self, agents: _Optional[_Iterable[_Union[AgentRegistration, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class ListAgentsRequest(_message.Message):
    __slots__ = ("domains", "health_statuses", "page_size", "page_token", "sort_by", "sort_desc", "include_health_info")
    DOMAINS_FIELD_NUMBER: _ClassVar[int]
    HEALTH_STATUSES_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    SORT_BY_FIELD_NUMBER: _ClassVar[int]
    SORT_DESC_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_HEALTH_INFO_FIELD_NUMBER: _ClassVar[int]
    domains: _containers.RepeatedScalarFieldContainer[str]
    health_statuses: _containers.RepeatedScalarFieldContainer[HealthStatus]
    page_size: int
    page_token: str
    sort_by: str
    sort_desc: bool
    include_health_info: bool
    def __init__(self, domains: _Optional[_Iterable[str]] = ..., health_statuses: _Optional[_Iterable[_Union[HealthStatus, str]]] = ..., page_size: _Optional[int] = ..., page_token: _Optional[str] = ..., sort_by: _Optional[str] = ..., sort_desc: bool = ..., include_health_info: bool = ...) -> None: ...

class ListAgentsResponse(_message.Message):
    __slots__ = ("agents", "next_page_token", "total_count")
    AGENTS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    agents: _containers.RepeatedCompositeFieldContainer[AgentRegistration]
    next_page_token: str
    total_count: int
    def __init__(self, agents: _Optional[_Iterable[_Union[AgentRegistration, _Mapping]]] = ..., next_page_token: _Optional[str] = ..., total_count: _Optional[int] = ...) -> None: ...

class DeleteAgentRequest(_message.Message):
    __slots__ = ("agent_id", "reason")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    reason: str
    def __init__(self, agent_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class HealthReportRequest(_message.Message):
    __slots__ = ("agent_id", "health_info", "load_metrics")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    HEALTH_INFO_FIELD_NUMBER: _ClassVar[int]
    LOAD_METRICS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    health_info: HealthInfo
    load_metrics: _struct_pb2.Struct
    def __init__(self, agent_id: _Optional[str] = ..., health_info: _Optional[_Union[HealthInfo, _Mapping]] = ..., load_metrics: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class HealthReportResponse(_message.Message):
    __slots__ = ("accepted", "message", "next_check_time")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    NEXT_CHECK_TIME_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    message: str
    next_check_time: _timestamp_pb2.Timestamp
    def __init__(self, accepted: bool = ..., message: _Optional[str] = ..., next_check_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class RegistryInfoResponse(_message.Message):
    __slots__ = ("total_agents", "healthy_agents", "unhealthy_agents", "registry_start_time", "registry_version", "domain_stats", "metadata")
    TOTAL_AGENTS_FIELD_NUMBER: _ClassVar[int]
    HEALTHY_AGENTS_FIELD_NUMBER: _ClassVar[int]
    UNHEALTHY_AGENTS_FIELD_NUMBER: _ClassVar[int]
    REGISTRY_START_TIME_FIELD_NUMBER: _ClassVar[int]
    REGISTRY_VERSION_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_STATS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    total_agents: int
    healthy_agents: int
    unhealthy_agents: int
    registry_start_time: _timestamp_pb2.Timestamp
    registry_version: str
    domain_stats: _containers.RepeatedCompositeFieldContainer[DomainStats]
    metadata: _struct_pb2.Struct
    def __init__(self, total_agents: _Optional[int] = ..., healthy_agents: _Optional[int] = ..., unhealthy_agents: _Optional[int] = ..., registry_start_time: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., registry_version: _Optional[str] = ..., domain_stats: _Optional[_Iterable[_Union[DomainStats, _Mapping]]] = ..., metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class DomainStats(_message.Message):
    __slots__ = ("domain", "agent_count", "healthy_count", "capabilities")
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    AGENT_COUNT_FIELD_NUMBER: _ClassVar[int]
    HEALTHY_COUNT_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    domain: str
    agent_count: int
    healthy_count: int
    capabilities: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, domain: _Optional[str] = ..., agent_count: _Optional[int] = ..., healthy_count: _Optional[int] = ..., capabilities: _Optional[_Iterable[str]] = ...) -> None: ...
