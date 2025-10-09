"""Tests for S3 storage backend."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from a2a_registry.s3_storage import S3Storage
from a2a_registry.storage import ExtensionInfo


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    with patch('boto3.client') as mock_client:
        client = Mock()
        mock_client.return_value = client
        yield client


@pytest.fixture
def s3_storage(mock_s3_client):
    """S3 storage instance with mocked client."""
    return S3Storage(bucket_name="test-bucket", prefix="test-prefix/")


@pytest.fixture
def sample_agent():
    """Sample agent card for testing."""
    return {
        "name": "test-agent",
        "description": "Test agent",
        "version": "1.0.0",
        "protocol_version": "0.3.0",
        "skills": [{"id": "test_skill", "description": "Test skill"}]
    }


@pytest.fixture
def sample_extension():
    """Sample extension info for testing."""
    return ExtensionInfo(
        uri="test://extension",
        description="Test extension",
        required=True,
        first_declared_by_agent="test-agent"
    )


class TestS3StorageAgents:
    """Test S3 storage agent operations."""

    @pytest.mark.asyncio
    async def test_register_agent_success(self, s3_storage, mock_s3_client, sample_agent):
        """Test successful agent registration."""
        mock_s3_client.put_object.return_value = {}
        
        result = await s3_storage.register_agent(sample_agent)
        
        assert result is True
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args
        assert call_args[1]['Bucket'] == 'test-bucket'
        assert call_args[1]['Key'] == 'test-prefix/agents/test-agent.json'
        assert call_args[1]['ContentType'] == 'application/json'

    @pytest.mark.asyncio
    async def test_register_agent_no_name(self, s3_storage, mock_s3_client):
        """Test agent registration without name."""
        agent_without_name = {"description": "Test agent"}
        
        result = await s3_storage.register_agent(agent_without_name)
        
        assert result is False
        mock_s3_client.put_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_agent_s3_error(self, s3_storage, mock_s3_client, sample_agent):
        """Test agent registration with S3 error."""
        mock_s3_client.put_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'PutObject'
        )
        
        result = await s3_storage.register_agent(sample_agent)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_agent_success(self, s3_storage, mock_s3_client, sample_agent):
        """Test successful agent retrieval."""
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = json.dumps(sample_agent).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        result = await s3_storage.get_agent("test-agent")
        
        assert result == sample_agent
        mock_s3_client.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test-prefix/agents/test-agent.json'
        )

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, s3_storage, mock_s3_client):
        """Test agent retrieval when agent doesn't exist."""
        mock_s3_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            'GetObject'
        )
        
        result = await s3_storage.get_agent("nonexistent-agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_s3_error(self, s3_storage, mock_s3_client):
        """Test agent retrieval with S3 error."""
        mock_s3_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'GetObject'
        )
        
        result = await s3_storage.get_agent("test-agent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_agents_success(self, s3_storage, mock_s3_client, sample_agent):
        """Test successful agent listing."""
        # Mock paginator
        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator
        
        # Mock pagination response
        mock_paginator.paginate.return_value = [
            {
                'Contents': [
                    {'Key': 'test-prefix/agents/test-agent.json'},
                    {'Key': 'test-prefix/agents/another-agent.json'}
                ]
            }
        ]
        
        # Mock get_object responses
        mock_response = {'Body': Mock()}
        mock_response['Body'].read.return_value = json.dumps(sample_agent).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        result = await s3_storage.list_agents()
        
        assert len(result) == 2
        assert all(agent == sample_agent for agent in result)

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, s3_storage, mock_s3_client):
        """Test listing agents when none exist."""
        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{'Contents': []}]
        
        result = await s3_storage.list_agents()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_unregister_agent_success(self, s3_storage, mock_s3_client):
        """Test successful agent unregistration."""
        mock_s3_client.delete_object.return_value = {}
        
        result = await s3_storage.unregister_agent("test-agent")
        
        assert result is True
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test-prefix/agents/test-agent.json'
        )

    @pytest.mark.asyncio
    async def test_unregister_agent_s3_error(self, s3_storage, mock_s3_client):
        """Test agent unregistration with S3 error."""
        mock_s3_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DeleteObject'
        )
        
        result = await s3_storage.unregister_agent("test-agent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_search_agents(self, s3_storage, mock_s3_client):
        """Test agent search functionality."""
        agents = [
            {"name": "weather-agent", "description": "Weather service", "skills": []},
            {"name": "news-agent", "description": "News service", "skills": [{"id": "weather", "description": "Weather news"}]},
            {"name": "chat-agent", "description": "Chat service", "skills": []}
        ]
        
        # Mock list_agents
        with patch.object(s3_storage, 'list_agents', return_value=agents):
            result = await s3_storage.search_agents("weather")
        
        assert len(result) == 2
        assert result[0]["name"] == "weather-agent"
        assert result[1]["name"] == "news-agent"


class TestS3StorageExtensions:
    """Test S3 storage extension operations."""

    @pytest.mark.asyncio
    async def test_store_extension_success(self, s3_storage, mock_s3_client, sample_extension):
        """Test successful extension storage."""
        mock_s3_client.put_object.return_value = {}
        
        result = await s3_storage.store_extension(sample_extension)
        
        assert result is True
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_extension_s3_error(self, s3_storage, mock_s3_client, sample_extension):
        """Test extension storage with S3 error."""
        mock_s3_client.put_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'PutObject'
        )
        
        result = await s3_storage.store_extension(sample_extension)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_extension_success(self, s3_storage, mock_s3_client, sample_extension):
        """Test successful extension retrieval."""
        mock_response = {'Body': Mock()}
        mock_response['Body'].read.return_value = json.dumps(sample_extension.to_dict()).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        result = await s3_storage.get_extension("test://extension")
        
        assert result is not None
        assert result.uri == sample_extension.uri

    @pytest.mark.asyncio
    async def test_get_extension_not_found(self, s3_storage, mock_s3_client):
        """Test extension retrieval when extension doesn't exist."""
        mock_s3_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            'GetObject'
        )
        
        result = await s3_storage.get_extension("nonexistent://extension")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_extensions_with_filters(self, s3_storage, mock_s3_client, sample_extension):
        """Test extension listing with filters."""
        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {'Contents': [{'Key': 'test-prefix/extensions/test:__extension.json'}]}
        ]
        
        mock_response = {'Body': Mock()}
        mock_response['Body'].read.return_value = json.dumps(sample_extension.to_dict()).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        extensions, next_token, total = await s3_storage.list_extensions(
            uri_pattern="test",
            declaring_agents=["test-agent"],
            page_size=10
        )
        
        assert len(extensions) == 1
        assert extensions[0].uri == sample_extension.uri
        assert next_token is None
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_agent_extensions(self, s3_storage, sample_extension):
        """Test getting extensions for a specific agent."""
        extensions = [sample_extension]
        
        with patch.object(s3_storage, 'list_extensions', return_value=(extensions, None, 1)):
            result = await s3_storage.get_agent_extensions("test-agent")
        
        assert len(result) == 1
        assert result[0].uri == sample_extension.uri

    @pytest.mark.asyncio
    async def test_update_agent_extensions(self, s3_storage, mock_s3_client):
        """Test updating agent extensions."""
        extensions_data = [
            {"uri": "test://extension1", "description": "Test extension 1"},
            {"uri": "test://extension2", "description": "Test extension 2"}
        ]
        
        with patch.object(s3_storage, 'remove_agent_from_extensions', return_value=True), \
             patch.object(s3_storage, 'get_extension', return_value=None), \
             patch.object(s3_storage, 'store_extension', return_value=True):
            
            result = await s3_storage.update_agent_extensions("test-agent", extensions_data)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_agent_from_extensions(self, s3_storage, mock_s3_client, sample_extension):
        """Test removing agent from extensions."""
        extensions = [sample_extension]
        
        with patch.object(s3_storage, 'list_extensions', return_value=(extensions, None, 1)), \
             patch.object(s3_storage, 'store_extension', return_value=True):
            
            result = await s3_storage.remove_agent_from_extensions("test-agent")
        
        assert result is True


class TestS3StorageConfiguration:
    """Test S3 storage configuration and initialization."""

    def test_s3_storage_initialization(self):
        """Test S3 storage initialization with custom parameters."""
        storage = S3Storage(bucket_name="custom-bucket", prefix="custom-prefix/")
        
        assert storage.bucket_name == "custom-bucket"
        assert storage.prefix == "custom-prefix/"
        assert storage._agents_key == "custom-prefix/agents/"
        assert storage._extensions_key == "custom-prefix/extensions/"

    def test_s3_storage_default_prefix(self):
        """Test S3 storage initialization with default prefix."""
        storage = S3Storage(bucket_name="test-bucket")
        
        assert storage.bucket_name == "test-bucket"
        assert storage.prefix == "a2a-registry/"
        assert storage._agents_key == "a2a-registry/agents/"
        assert storage._extensions_key == "a2a-registry/extensions/"
