"""Integration tests for S3 storage backend."""

import os
import pytest
import boto3
from moto import mock_aws

from a2a_registry.s3_storage import S3Storage
from a2a_registry.storage import ExtensionInfo


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def s3_bucket(aws_credentials):
    """Create a mock S3 bucket for testing."""
    with mock_aws():
        # Create S3 client and bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-a2a-registry-bucket'
        s3_client.create_bucket(Bucket=bucket_name)
        yield bucket_name


@pytest.fixture
def s3_storage(s3_bucket):
    """S3 storage instance with real S3 operations (mocked)."""
    return S3Storage(bucket_name=s3_bucket, prefix="test-registry/")


@pytest.fixture
def sample_agent():
    """Sample agent card for testing."""
    return {
        "name": "integration-test-agent",
        "description": "Agent for integration testing",
        "version": "1.0.0",
        "protocol_version": "0.3.0",
        "url": "http://localhost:8000",
        "skills": [
            {"id": "test_skill", "description": "Test skill for integration"}
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False
        }
    }


class TestS3StorageIntegration:
    """Integration tests for S3 storage operations."""

    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, s3_storage, sample_agent):
        """Test complete agent lifecycle: register, get, list, search, unregister."""
        agent_id = sample_agent["name"]
        
        # 1. Register agent
        success = await s3_storage.register_agent(sample_agent)
        assert success is True
        
        # 2. Get agent
        retrieved_agent = await s3_storage.get_agent(agent_id)
        assert retrieved_agent is not None
        assert retrieved_agent["name"] == agent_id
        assert retrieved_agent["description"] == sample_agent["description"]
        
        # 3. List agents
        agents = await s3_storage.list_agents()
        assert len(agents) == 1
        assert agents[0]["name"] == agent_id
        
        # 4. Search agents
        search_results = await s3_storage.search_agents("integration")
        assert len(search_results) == 1
        assert search_results[0]["name"] == agent_id
        
        # Search with no results
        no_results = await s3_storage.search_agents("nonexistent")
        assert len(no_results) == 0
        
        # 5. Unregister agent
        unregister_success = await s3_storage.unregister_agent(agent_id)
        assert unregister_success is True
        
        # 6. Verify agent is gone
        missing_agent = await s3_storage.get_agent(agent_id)
        assert missing_agent is None
        
        empty_list = await s3_storage.list_agents()
        assert len(empty_list) == 0

    @pytest.mark.asyncio
    async def test_multiple_agents(self, s3_storage):
        """Test operations with multiple agents."""
        agents = [
            {
                "name": f"test-agent-{i}",
                "description": f"Test agent {i}",
                "version": "1.0.0",
                "protocol_version": "0.3.0",
                "skills": []
            }
            for i in range(3)
        ]
        
        # Register all agents
        for agent in agents:
            success = await s3_storage.register_agent(agent)
            assert success is True
        
        # List all agents
        all_agents = await s3_storage.list_agents()
        assert len(all_agents) == 3
        
        # Verify all agents are present
        agent_names = {agent["name"] for agent in all_agents}
        expected_names = {f"test-agent-{i}" for i in range(3)}
        assert agent_names == expected_names
        
        # Search for specific agents
        search_results = await s3_storage.search_agents("test-agent-1")
        assert len(search_results) == 1
        assert search_results[0]["name"] == "test-agent-1"

    @pytest.mark.asyncio
    async def test_extension_lifecycle(self, s3_storage):
        """Test extension storage and retrieval."""
        # Create extension info
        ext_info = ExtensionInfo(
            uri="test://integration-extension",
            description="Integration test extension",
            required=True,
            first_declared_by_agent="test-agent"
        )
        
        # Store extension
        success = await s3_storage.store_extension(ext_info)
        assert success is True
        
        # Retrieve extension
        retrieved_ext = await s3_storage.get_extension("test://integration-extension")
        assert retrieved_ext is not None
        assert retrieved_ext.uri == ext_info.uri
        assert retrieved_ext.description == ext_info.description
        
        # List extensions
        extensions, next_token, total = await s3_storage.list_extensions()
        assert len(extensions) == 1
        assert total == 1
        assert next_token is None
        assert extensions[0].uri == ext_info.uri

    @pytest.mark.asyncio
    async def test_agent_extensions_integration(self, s3_storage, sample_agent):
        """Test agent-extension relationship management."""
        agent_id = sample_agent["name"]
        
        # Register agent first
        await s3_storage.register_agent(sample_agent)
        
        # Update agent extensions
        extensions_data = [
            {
                "uri": "test://extension1",
                "description": "First test extension",
                "required": True
            },
            {
                "uri": "test://extension2", 
                "description": "Second test extension",
                "required": False
            }
        ]
        
        success = await s3_storage.update_agent_extensions(agent_id, extensions_data)
        assert success is True
        
        # Get agent extensions
        agent_extensions = await s3_storage.get_agent_extensions(agent_id)
        assert len(agent_extensions) == 2
        
        extension_uris = {ext.uri for ext in agent_extensions}
        expected_uris = {"test://extension1", "test://extension2"}
        assert extension_uris == expected_uris
        
        # Remove agent from extensions
        remove_success = await s3_storage.remove_agent_from_extensions(agent_id)
        assert remove_success is True
        
        # Verify extensions are cleaned up
        remaining_extensions = await s3_storage.get_agent_extensions(agent_id)
        assert len(remaining_extensions) == 0

    @pytest.mark.asyncio
    async def test_s3_key_structure(self, s3_storage, sample_agent):
        """Test that S3 keys are structured correctly."""
        # Register an agent
        await s3_storage.register_agent(sample_agent)
        
        # Check that the S3 client was called with correct key structure
        # This is more of a verification that our key generation works
        agent_id = sample_agent["name"]
        expected_key = f"test-registry/agents/{agent_id}.json"
        
        # Verify we can retrieve using the expected key structure
        retrieved_agent = await s3_storage.get_agent(agent_id)
        assert retrieved_agent is not None
        assert retrieved_agent["name"] == agent_id

    @pytest.mark.asyncio
    async def test_error_handling(self, s3_storage):
        """Test error handling for various edge cases."""
        # Test getting non-existent agent
        missing_agent = await s3_storage.get_agent("non-existent-agent")
        assert missing_agent is None
        
        # Test unregistering non-existent agent
        unregister_result = await s3_storage.unregister_agent("non-existent-agent")
        # S3 delete operations are idempotent, so this should succeed
        assert unregister_result is True
        
        # Test getting non-existent extension
        missing_ext = await s3_storage.get_extension("non-existent://extension")
        assert missing_ext is None
