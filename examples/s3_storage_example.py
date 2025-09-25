#!/usr/bin/env python3
"""Example demonstrating S3 storage backend usage."""

import asyncio
import os
from a2a_registry.s3_storage import S3Storage


async def main():
    """Demonstrate S3 storage operations."""
    # Configure S3 storage
    bucket_name = os.getenv("S3_BUCKET_NAME", "my-a2a-registry-bucket")
    prefix = os.getenv("S3_PREFIX", "a2a-registry/")
    
    print(f"Using S3 bucket: {bucket_name}")
    print(f"Using prefix: {prefix}")
    
    # Initialize S3 storage
    storage = S3Storage(bucket_name=bucket_name, prefix=prefix)
    
    # Sample agent
    agent_card = {
        "name": "example-weather-agent",
        "description": "Provides weather information and forecasts",
        "version": "1.2.0",
        "protocol_version": "0.3.0",
        "url": "https://weather-agent.example.com",
        "capabilities": {
            "streaming": True,
            "push_notifications": False,
            "state_transition_history": True
        },
        "default_input_modes": ["text"],
        "default_output_modes": ["text", "json"],
        "skills": [
            {
                "id": "get_current_weather",
                "description": "Get current weather for a location"
            },
            {
                "id": "get_weather_forecast",
                "description": "Get weather forecast for a location"
            }
        ],
        "preferred_transport": "JSONRPC"
    }
    
    try:
        # 1. Register the agent
        print("\n1. Registering agent...")
        success = await storage.register_agent(agent_card)
        if success:
            print(f"✅ Successfully registered agent: {agent_card['name']}")
        else:
            print(f"❌ Failed to register agent: {agent_card['name']}")
            return
        
        # 2. Retrieve the agent
        print("\n2. Retrieving agent...")
        retrieved_agent = await storage.get_agent(agent_card["name"])
        if retrieved_agent:
            print(f"✅ Retrieved agent: {retrieved_agent['name']}")
            print(f"   Description: {retrieved_agent['description']}")
            print(f"   Skills: {len(retrieved_agent['skills'])}")
        else:
            print("❌ Failed to retrieve agent")
        
        # 3. List all agents
        print("\n3. Listing all agents...")
        agents = await storage.list_agents()
        print(f"✅ Found {len(agents)} agents:")
        for agent in agents:
            print(f"   - {agent['name']}: {agent['description']}")
        
        # 4. Search agents
        print("\n4. Searching agents...")
        search_results = await storage.search_agents("weather")
        print(f"✅ Found {len(search_results)} agents matching 'weather':")
        for agent in search_results:
            print(f"   - {agent['name']}")
        
        # 5. Update agent extensions
        print("\n5. Adding extensions to agent...")
        extensions = [
            {
                "uri": "weather://openweathermap",
                "description": "OpenWeatherMap API integration",
                "required": True,
                "params": {
                    "api_key_required": True,
                    "rate_limit": "1000/hour"
                }
            },
            {
                "uri": "weather://weatherapi",
                "description": "WeatherAPI.com integration",
                "required": False,
                "params": {
                    "api_key_required": True,
                    "rate_limit": "1000000/month"
                }
            }
        ]
        
        success = await storage.update_agent_extensions(agent_card["name"], extensions)
        if success:
            print("✅ Successfully updated agent extensions")
        else:
            print("❌ Failed to update agent extensions")
        
        # 6. Get agent extensions
        print("\n6. Retrieving agent extensions...")
        agent_extensions = await storage.get_agent_extensions(agent_card["name"])
        print(f"✅ Agent has {len(agent_extensions)} extensions:")
        for ext in agent_extensions:
            print(f"   - {ext.uri}: {ext.description}")
            print(f"     Required: {ext.required}, Usage count: {ext.usage_count}")
        
        # 7. List all extensions
        print("\n7. Listing all extensions...")
        all_extensions, next_token, total = await storage.list_extensions()
        print(f"✅ Found {total} total extensions:")
        for ext in all_extensions:
            print(f"   - {ext.uri}: {ext.description}")
            print(f"     Declared by: {', '.join(ext.declaring_agents)}")
        
        # 8. Clean up - unregister agent
        print("\n8. Cleaning up...")
        success = await storage.unregister_agent(agent_card["name"])
        if success:
            print(f"✅ Successfully unregistered agent: {agent_card['name']}")
        else:
            print(f"❌ Failed to unregister agent: {agent_card['name']}")
        
        # Verify cleanup
        final_agents = await storage.list_agents()
        print(f"✅ Final agent count: {len(final_agents)}")
        
    except Exception as e:
        print(f"❌ Error during S3 operations: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("A2A Registry S3 Storage Example")
    print("=" * 40)
    print()
    print("Prerequisites:")
    print("1. AWS credentials configured (via IAM role, credentials file, or env vars)")
    print("2. S3 bucket exists and is accessible")
    print("3. Set S3_BUCKET_NAME environment variable")
    print()
    
    # Check if bucket name is provided
    if not os.getenv("S3_BUCKET_NAME"):
        print("❌ Please set S3_BUCKET_NAME environment variable")
        print("   Example: export S3_BUCKET_NAME=my-a2a-registry-bucket")
        exit(1)
    
    asyncio.run(main())
