"""Basic tests to ensure the package imports correctly."""

import pytest

from a2a_registry import __version__, A2A_PROTOCOL_VERSION
from a2a_registry.proto.generated import a2a_pb2, registry_pb2


def test_version():
    """Test that version is accessible."""
    assert __version__ == "0.1.0"


def test_a2a_protocol_version():
    """Test that A2A protocol version is accessible."""
    assert A2A_PROTOCOL_VERSION == "0.3.0"


def test_protobuf_imports():
    """Test that protobuf modules can be imported."""
    # Test A2A protobuf
    assert hasattr(a2a_pb2, "AgentCard")
    assert hasattr(a2a_pb2, "Task")
    
    # Test registry protobuf
    assert hasattr(registry_pb2, "RegistryAgentCard")
    assert hasattr(registry_pb2, "RegistryMetadata")


def test_create_agent_card():
    """Test creating basic protobuf message instances."""
    # Create A2A agent card
    agent_card = a2a_pb2.AgentCard()
    agent_card.name = "test-agent"
    assert agent_card.name == "test-agent"
    
    # Create registry metadata
    metadata = registry_pb2.RegistryMetadata()
    metadata.registrar_id = "test-registrar"
    assert metadata.registrar_id == "test-registrar"
    
    # Create registry agent card
    registry_card = registry_pb2.RegistryAgentCard()
    registry_card.agent_card.CopyFrom(agent_card)
    registry_card.registry_metadata.CopyFrom(metadata)
    
    assert registry_card.agent_card.name == "test-agent"
    assert registry_card.registry_metadata.registrar_id == "test-registrar"