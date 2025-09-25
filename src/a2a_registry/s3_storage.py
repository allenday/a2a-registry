"""S3 storage backend for A2A Registry."""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError
from fasta2a.schema import AgentCard

from .storage import ExtensionInfo, StorageBackend
from .config import config

logger = logging.getLogger(__name__)


class S3Storage(StorageBackend):
    """S3-based storage for agent registry."""

    def __init__(self, bucket_name: str, prefix: str = "a2a-registry/") -> None:
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.s3_client = boto3.client('s3')
        self._agents_key = f"{prefix}agents/"
        self._extensions_key = f"{prefix}extensions/"

    async def register_agent(self, agent_card: AgentCard) -> bool:
        """Register an agent in the registry."""
        agent_id = agent_card.get("name")
        print(f"S3Storage: Attempting to register agent: {agent_id}")
        logger.info(f"S3Storage: Attempting to register agent: {agent_id}")
        
        if not agent_id:
            error_msg = "S3Storage: No agent name provided in agent_card"
            print(error_msg)
            logger.error(error_msg)
            return False
        
        try:
            key = f"{self._agents_key}{agent_id}.json"
            agent_json = json.dumps(agent_card, ensure_ascii=False)
            print(f"S3Storage: Storing agent {agent_id} to S3 key: {key}")
            print(f"S3Storage: Agent data: {agent_json[:200]}...")
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=agent_json,
                ContentType='application/json'
            )
            success_msg = f"S3Storage: Successfully registered agent: {agent_id}"
            logger.info(success_msg)
            print(success_msg)
            return True
        except ClientError as e:
            error_msg = f"S3Storage: Failed to register agent {agent_id}: {e}"
            logger.error(error_msg)
            print(error_msg)
            return False

    async def get_agent(self, agent_id: str) -> AgentCard | None:
        """Get an agent by ID."""
        print(f"S3Storage: get_agent called for agent_id: {agent_id}")
        try:
            key = f"{self._agents_key}{agent_id}.json"
            print(f"S3Storage: Looking for S3 key: {key} in bucket: {self.bucket_name}")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            agent_data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"S3Storage: Found agent {agent_id}: {agent_data.get('name')}")
            return agent_data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"S3Storage: Agent {agent_id} not found (NoSuchKey)")
                return None
            error_msg = f"S3Storage: Failed to get agent {agent_id}: {e}"
            logger.error(error_msg)
            print(error_msg)
            return None

    async def list_agents(self) -> list[AgentCard]:
        """List all registered agents."""
        print(f"S3Storage: list_agents called")
        agents = []
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            print(f"S3Storage: Listing objects in bucket {self.bucket_name} with prefix {self._agents_key}")
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=self._agents_key):
                objects = page.get('Contents', [])
                print(f"S3Storage: Found {len(objects)} objects in this page")
                for obj in objects:
                    print(f"S3Storage: Processing object: {obj['Key']}")
                    if obj['Key'].endswith('.json'):
                        agent_id = obj['Key'].split('/')[-1].replace('.json', '')
                        print(f"S3Storage: Extracting agent_id: {agent_id}")
                        agent = await self.get_agent(agent_id)
                        if agent:
                            agents.append(agent)
                            print(f"S3Storage: Added agent {agent_id} to list")
            print(f"S3Storage: Returning {len(agents)} agents: {[agent.get('name') for agent in agents]}")
        except ClientError as e:
            error_msg = f"S3Storage: Failed to list agents: {e}"
            logger.error(error_msg)
            print(error_msg)
        return agents

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        try:
            key = f"{self._agents_key}{agent_id}.json"
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        except ClientError as e:
            error_msg = f"Failed to unregister agent {agent_id}: {e}"
            logger.error(error_msg)
            print(error_msg)
            return False

    async def search_agents(self, query: str) -> list[AgentCard]:
        """Search agents by name, description, or capabilities."""
        all_agents = await self.list_agents()
        results = []
        query_lower = query.lower()

        for agent in all_agents:
            if (
                query_lower in agent.get("name", "").lower()
                or query_lower in agent.get("description", "").lower()
                or any(
                    query_lower in skill.get("id", "").lower()
                    for skill in agent.get("skills", [])
                )
            ):
                results.append(agent)

        return results

    async def store_extension(self, extension_info: ExtensionInfo) -> bool:
        """Store extension information."""
        try:
            key = f"{self._extensions_key}{extension_info.uri.replace('/', '_')}.json"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(extension_info.to_dict(), ensure_ascii=False),
                ContentType='application/json'
            )
            logger.info(f"Stored extension: {extension_info.uri}")
            return True
        except ClientError as e:
            error_msg = f"Failed to store extension {extension_info.uri}: {e}"
            logger.error(error_msg)
            print(error_msg)
            return False

    async def get_extension(self, uri: str) -> ExtensionInfo | None:
        """Get extension information by URI."""
        try:
            key = f"{self._extensions_key}{uri.replace('/', '_')}.json"
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return ExtensionInfo.from_dict(data)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            error_msg = f"Failed to get extension {uri}: {e}"
            logger.error(error_msg)
            print(error_msg)
            return None

    async def list_extensions(
        self,
        uri_pattern: str | None = None,
        declaring_agents: list[str] | None = None,
        trust_levels: list[str] | None = None,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> tuple[list[ExtensionInfo], str | None, int]:
        """List extensions with optional filtering and pagination."""
        extensions = []
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=self._extensions_key):
                for obj in page.get('Contents', []):
                    if obj['Key'].endswith('.json'):
                        uri = obj['Key'].split('/')[-1].replace('.json', '').replace('_', '/')
                        ext = await self.get_extension(uri)
                        if ext:
                            extensions.append(ext)
        except ClientError as e:
            error_msg = f"Failed to list extensions: {e}"
            logger.error(error_msg)
            print(error_msg)

        # Apply filters
        if uri_pattern:
            extensions = [ext for ext in extensions if uri_pattern.lower() in ext.uri.lower()]

        if declaring_agents:
            extensions = [
                ext for ext in extensions
                if any(agent in ext.declaring_agents for agent in declaring_agents)
            ]

        if trust_levels:
            extensions = [ext for ext in extensions if ext.trust_level in trust_levels]

        # Simple pagination
        total_count = len(extensions)
        start_idx = 0
        if page_token:
            try:
                start_idx = int(page_token)
            except ValueError:
                start_idx = 0

        end_idx = start_idx + page_size
        page_extensions = extensions[start_idx:end_idx]

        next_page_token = None
        if end_idx < total_count:
            next_page_token = str(end_idx)

        return page_extensions, next_page_token, total_count

    async def get_agent_extensions(self, agent_id: str) -> list[ExtensionInfo]:
        """Get all extensions used by a specific agent."""
        extensions, _, _ = await self.list_extensions()
        return [ext for ext in extensions if agent_id in ext.declaring_agents]

    async def update_agent_extensions(self, agent_id: str, extensions: list[dict]) -> bool:
        """Update extensions for an agent."""
        # Remove agent from all current extensions
        await self.remove_agent_from_extensions(agent_id)

        # Add agent to new extensions
        for ext_data in extensions:
            uri = ext_data.get("uri", "")
            if not uri:
                continue

            if not config.is_extension_allowed(uri):
                logger.warning(f"Extension {uri} not allowed in current mode")
                continue

            existing_ext = await self.get_extension(uri)
            if existing_ext:
                existing_ext.add_declaring_agent(agent_id)
                await self.store_extension(existing_ext)
            else:
                # Create new extension info
                ext_info = ExtensionInfo(
                    uri=uri,
                    description=ext_data.get("description", ""),
                    required=ext_data.get("required", False),
                    params=ext_data.get("params", {}),
                    first_declared_by_agent=agent_id,
                    trust_level=config.get_default_trust_level(),
                )
                await self.store_extension(ext_info)

        return True

    async def remove_agent_from_extensions(self, agent_id: str) -> bool:
        """Remove agent from all extension declarations."""
        extensions, _, _ = await self.list_extensions()
        extensions_to_remove = []

        for ext_info in extensions:
            if agent_id in ext_info.declaring_agents:
                ext_info.remove_declaring_agent(agent_id)
                if ext_info.usage_count == 0:
                    extensions_to_remove.append(ext_info.uri)
                else:
                    await self.store_extension(ext_info)

        # Remove unused extensions
        for uri in extensions_to_remove:
            try:
                key = f"{self._extensions_key}{uri.replace('/', '_')}.json"
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info(f"Removed unused extension: {uri}")
            except ClientError as e:
                error_msg = f"Failed to remove extension {uri}: {e}"
                logger.error(error_msg)
                print(error_msg)

        return True