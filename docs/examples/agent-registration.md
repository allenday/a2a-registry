# Agent Registration Examples

This guide demonstrates various agent registration patterns and best practices for the A2A Registry.

## Protocol Support

The A2A Registry supports both JSON-RPC 2.0 (primary) and REST (secondary) protocols. Agent cards default to `JSONRPC` as the preferred transport per the **A2A Protocol v0.3.0** specification.

## Basic Agent Registration

### Minimal Agent Card

The simplest possible agent registration using JSON-RPC:

```json
{
  "agent_card": {
    "name": "minimal-agent",
    "description": "A minimal example agent",
    "url": "http://localhost:3000",
    "version": "0.420.0",
    "protocol_version": "0.3.0",
    "preferred_transport": "JSONRPC",
    "skills": []
  }
}
```

Register using JSON-RPC:
```bash
curl -X POST http://localhost:8000/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "register_agent",
    "params": {
      "agent_card": {
        "name": "minimal-agent",
        "description": "A minimal example agent",
        "url": "http://localhost:3000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "preferred_transport": "JSONRPC",
        "skills": []
      }
    },
    "id": 1
  }'
```

REST alternative:
```bash
curl -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_card": {
      "name": "minimal-agent",
      "description": "A minimal example agent",
      "url": "http://localhost:3000",
      "version": "0.420.0",
      "protocol_version": "0.3.0",
      "preferred_transport": "JSONRPC",
      "skills": []
    }
  }'
```

### Complete Agent Card

A fully-featured agent card with all optional fields:

```json
{
  "agent_card": {
    "name": "advanced-agent",
    "description": "A comprehensive agent with multiple capabilities",
    "url": "http://advanced-agent.example.com:8080",
    "version": "2.1.3",
    "protocol_version": "0.3.0",
    "preferred_transport": "JSONRPC",
    "skills": [
      {
        "id": "natural_language_processing",
        "description": "Process and understand natural language text",
        "input_schema": {
          "type": "object",
          "properties": {
            "text": {"type": "string"},
            "language": {"type": "string", "default": "en"}
          },
          "required": ["text"]
        },
        "output_schema": {
          "type": "object",
          "properties": {
            "sentiment": {"type": "string"},
            "entities": {"type": "array"},
            "summary": {"type": "string"}
          }
        }
      },
      {
        "id": "image_analysis",
        "description": "Analyze and describe images",
        "input_schema": {
          "type": "object",
          "properties": {
            "image_url": {"type": "string", "format": "uri"},
            "analysis_type": {
              "type": "string",
              "enum": ["objects", "faces", "text", "all"]
            }
          },
          "required": ["image_url"]
        }
      },
      {
        "id": "data_visualization",
        "description": "Create charts and graphs from data",
        "input_schema": {
          "type": "object",
          "properties": {
            "data": {"type": "array"},
            "chart_type": {
              "type": "string",
              "enum": ["line", "bar", "pie", "scatter"]
            }
          },
          "required": ["data", "chart_type"]
        }
      }
    ],
    "metadata": {
      "author": "AI Systems Corp",
      "license": "MIT",
      "homepage": "https://advanced-agent.example.com",
      "documentation": "https://docs.advanced-agent.example.com",
      "source_code": "https://github.com/aisystems/advanced-agent",
      "tags": ["nlp", "vision", "visualization"],
      "categories": ["analysis", "processing"],
      "supported_languages": ["en", "es", "fr", "de"],
      "max_concurrent_tasks": 10,
      "average_response_time_ms": 500
    }
  }
}
```

## Specialized Agent Types

### AI/ML Service Agent

```python
def register_ml_agent():
    agent_card = {
        "name": "ml-classifier-service",
        "description": "Machine learning classification service with multiple model support",
        "url": "http://ml-service.internal:8000",
        "version": "3.2.1",
        "protocol_version": "0.3.0",
        "skills": [
            {
                "id": "text_classification",
                "description": "Classify text into predefined categories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "model": {
                            "type": "string",
                            "enum": ["sentiment", "spam", "topic", "language"],
                            "default": "sentiment"
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.8
                        }
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "classification": {"type": "string"},
                        "confidence": {"type": "number"},
                        "alternatives": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "confidence": {"type": "number"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "id": "image_classification",
                "description": "Classify images using computer vision models",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image_url": {"type": "string", "format": "uri"},
                        "model": {
                            "type": "string",
                            "enum": ["general", "medical", "satellite"],
                            "default": "general"
                        }
                    },
                    "required": ["image_url"]
                }
            },
            {
                "id": "batch_processing",
                "description": "Process multiple items in batch for efficiency",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "maxItems": 1000
                        },
                        "processing_type": {
                            "type": "string",
                            "enum": ["text_classification", "image_classification"]
                        }
                    },
                    "required": ["items", "processing_type"]
                }
            }
        ],
        "metadata": {
            "model_versions": {
                "text_classifier": "bert-base-v2.1",
                "image_classifier": "resnet50-v1.5",
                "language_detector": "fasttext-v0.9"
            },
            "supported_formats": {
                "text": ["plain", "json", "xml"],
                "images": ["jpeg", "png", "webp", "tiff"]
            },
            "performance_metrics": {
                "text_classification_accuracy": 0.94,
                "image_classification_accuracy": 0.89,
                "average_latency_ms": 150,
                "throughput_per_second": 100
            },
            "resource_requirements": {
                "cpu_cores": 4,
                "memory_gb": 8,
                "gpu_required": True,
                "gpu_memory_gb": 6
            }
        }
    }
    
    return register_agent(agent_card)
```

### Data Processing Agent

```python
def register_data_processor():
    agent_card = {
        "name": "data-pipeline-processor",
        "description": "High-performance data processing and transformation service",
        "url": "http://data-processor.cluster.local:9000",
        "version": "1.4.0",
        "protocol_version": "0.3.0",
        "skills": [
            {
                "id": "csv_processing",
                "description": "Process and transform CSV data files",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_url": {"type": "string", "format": "uri"},
                        "operations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["filter", "transform", "aggregate", "join"]
                                    },
                                    "config": {"type": "object"}
                                }
                            }
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["csv", "json", "parquet"],
                            "default": "csv"
                        }
                    },
                    "required": ["file_url", "operations"]
                }
            },
            {
                "id": "json_transformation",
                "description": "Transform JSON data structures",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "object"},
                        "schema_mapping": {"type": "object"},
                        "validation_rules": {"type": "array"}
                    },
                    "required": ["data", "schema_mapping"]
                }
            },
            {
                "id": "data_validation",
                "description": "Validate data against schemas and business rules",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {},
                        "schema": {"type": "object"},
                        "rules": {"type": "array"}
                    },
                    "required": ["data", "schema"]
                }
            }
        ],
        "metadata": {
            "supported_file_sizes": {
                "max_file_size_mb": 1000,
                "recommended_chunk_size_mb": 50
            },
            "processing_capabilities": {
                "parallel_processing": True,
                "streaming_support": True,
                "memory_efficient": True
            },
            "data_formats": {
                "input": ["csv", "json", "xml", "parquet", "avro"],
                "output": ["csv", "json", "parquet", "xlsx"]
            }
        }
    }
    
    return register_agent(agent_card)
```

### Integration Service Agent

```python
def register_integration_service():
    agent_card = {
        "name": "api-integration-hub",
        "description": "Universal API integration and transformation service",
        "url": "https://integration-hub.company.com/api/v1",
        "version": "2.0.0",
        "protocol_version": "0.3.0",
        "skills": [
            {
                "id": "rest_api_call",
                "description": "Make REST API calls with authentication and error handling",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "format": "uri"},
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                        },
                        "headers": {"type": "object"},
                        "body": {},
                        "auth": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["bearer", "basic", "api_key", "oauth2"]
                                },
                                "credentials": {"type": "object"}
                            }
                        },
                        "timeout_seconds": {"type": "number", "default": 30}
                    },
                    "required": ["url", "method"]
                }
            },
            {
                "id": "data_mapping",
                "description": "Transform data between different API schemas",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source_data": {},
                        "source_schema": {"type": "object"},
                        "target_schema": {"type": "object"},
                        "mapping_rules": {"type": "object"}
                    },
                    "required": ["source_data", "target_schema", "mapping_rules"]
                }
            },
            {
                "id": "webhook_delivery",
                "description": "Deliver data to webhook endpoints with retry logic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "webhook_url": {"type": "string", "format": "uri"},
                        "payload": {},
                        "retry_config": {
                            "type": "object",
                            "properties": {
                                "max_retries": {"type": "integer", "default": 3},
                                "retry_delay_seconds": {"type": "number", "default": 1},
                                "exponential_backoff": {"type": "boolean", "default": True}
                            }
                        }
                    },
                    "required": ["webhook_url", "payload"]
                }
            }
        ],
        "metadata": {
            "supported_protocols": ["HTTP/1.1", "HTTP/2", "WebSocket"],
            "supported_auth_methods": ["OAuth2", "JWT", "API Key", "Basic Auth"],
            "security_features": {
                "encryption_in_transit": True,
                "credential_vault": True,
                "audit_logging": True,
                "rate_limiting": True
            },
            "compliance": ["SOC2", "GDPR", "HIPAA"],
            "sla": {
                "uptime_percentage": 99.9,
                "max_response_time_ms": 2000,
                "support_hours": "24/7"
            }
        }
    }
    
    return register_agent(agent_card)
```

## Registration Patterns

### Auto-Registration with Health Checks

```python
import time
import threading
import logging
from datetime import datetime

class HealthAwareAgent:
    def __init__(self, registry_client, agent_card):
        self.client = registry_client
        self.agent_card = agent_card
        self.registered = False
        self.health_check_interval = 60  # seconds
        self.registration_retry_interval = 30  # seconds
        self.max_retries = 5
        self.logger = logging.getLogger(__name__)
        self._stop_event = threading.Event()
    
    def register_with_retry(self):
        """Register with exponential backoff retry."""
        retry_count = 0
        while retry_count < self.max_retries and not self._stop_event.is_set():
            try:
                result = self.client.register_agent(self.agent_card)
                self.registered = True
                self.logger.info(f"Agent {self.agent_card['name']} registered successfully")
                return result
            except Exception as e:
                retry_count += 1
                wait_time = min(self.registration_retry_interval * (2 ** retry_count), 300)
                self.logger.warning(
                    f"Registration attempt {retry_count} failed: {e}. "
                    f"Retrying in {wait_time} seconds..."
                )
                self._stop_event.wait(wait_time)
        
        raise Exception(f"Failed to register after {self.max_retries} attempts")
    
    def health_check_loop(self):
        """Continuous health check and re-registration."""
        while not self._stop_event.is_set():
            try:
                if self.registered:
                    # Update agent card with current timestamp
                    updated_card = self.agent_card.copy()
                    updated_card["metadata"] = updated_card.get("metadata", {})
                    updated_card["metadata"]["last_heartbeat"] = datetime.utcnow().isoformat()
                    
                    # Re-register to update last seen time
                    self.client.register_agent(updated_card)
                    self.logger.debug(f"Health check passed for {self.agent_card['name']}")
                else:
                    # Try to re-register if not currently registered
                    self.register_with_retry()
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                self.registered = False
            
            self._stop_event.wait(self.health_check_interval)
    
    def start(self):
        """Start the agent with health monitoring."""
        # Initial registration
        self.register_with_retry()
        
        # Start health check thread
        health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        health_thread.start()
        
        return health_thread
    
    def stop(self):
        """Stop health monitoring and unregister."""
        self._stop_event.set()
        if self.registered:
            try:
                self.client.unregister_agent(self.agent_card['name'])
                self.logger.info(f"Agent {self.agent_card['name']} unregistered")
            except Exception as e:
                self.logger.error(f"Failed to unregister: {e}")
```

### Dynamic Skill Registration

```python
class DynamicSkillAgent:
    def __init__(self, registry_client, base_agent_card):
        self.client = registry_client
        self.base_card = base_agent_card
        self.active_skills = set()
    
    def add_skill(self, skill_definition):
        """Add a new skill to the agent."""
        # Update local skill set
        self.active_skills.add(skill_definition['id'])
        
        # Update agent card
        updated_card = self.base_card.copy()
        current_skills = {skill['id']: skill for skill in updated_card.get('skills', [])}
        current_skills[skill_definition['id']] = skill_definition
        updated_card['skills'] = list(current_skills.values())
        
        # Re-register with updated skills
        result = self.client.register_agent(updated_card)
        self.base_card = updated_card
        
        print(f"Added skill '{skill_definition['id']}' to agent {self.base_card['name']}")
        return result
    
    def remove_skill(self, skill_id):
        """Remove a skill from the agent."""
        if skill_id in self.active_skills:
            self.active_skills.remove(skill_id)
            
            # Update agent card
            updated_card = self.base_card.copy()
            updated_card['skills'] = [
                skill for skill in updated_card.get('skills', [])
                if skill['id'] != skill_id
            ]
            
            # Re-register with updated skills
            result = self.client.register_agent(updated_card)
            self.base_card = updated_card
            
            print(f"Removed skill '{skill_id}' from agent {self.base_card['name']}")
            return result
    
    def list_available_skills(self):
        """List all available skills for this agent type."""
        # This could be loaded from a configuration file or service
        return [
            {
                "id": "text_summarization",
                "description": "Summarize long text documents",
                "category": "nlp"
            },
            {
                "id": "sentiment_analysis", 
                "description": "Analyze sentiment of text",
                "category": "nlp"
            },
            {
                "id": "language_detection",
                "description": "Detect language of input text",
                "category": "nlp"
            },
            {
                "id": "keyword_extraction",
                "description": "Extract important keywords from text",
                "category": "nlp"
            }
        ]
    
    def auto_configure_skills(self, required_capabilities):
        """Automatically configure skills based on requirements."""
        available_skills = self.list_available_skills()
        
        for capability in required_capabilities:
            matching_skills = [
                skill for skill in available_skills
                if capability.lower() in skill['description'].lower() or
                   capability.lower() in skill['id'].lower()
            ]
            
            for skill in matching_skills:
                if skill['id'] not in self.active_skills:
                    self.add_skill(skill)

# Usage example
def main():
    from examples.basic_usage import A2ARegistryClient
    
    client = A2ARegistryClient()
    
    base_card = {
        "name": "adaptive-nlp-agent",
        "description": "Natural language processing agent with dynamic capabilities",
        "url": "http://localhost:7000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": []
    }
    
    agent = DynamicSkillAgent(client, base_card)
    
    # Register base agent
    agent.client.register_agent(agent.base_card)
    
    # Add skills dynamically
    agent.add_skill({
        "id": "text_summarization",
        "description": "Summarize long text documents",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "max_sentences": {"type": "integer", "default": 3}
            },
            "required": ["text"]
        }
    })
    
    # Auto-configure based on requirements
    agent.auto_configure_skills(["sentiment", "language detection"])
    
    # List current skills
    current_agent = client.get_agent("adaptive-nlp-agent")
    print(f"Agent now has {len(current_agent['agent_card']['skills'])} skills")

if __name__ == "__main__":
    main()
```

### Multi-Instance Registration

```python
class MultiInstanceAgent:
    def __init__(self, registry_client, base_agent_card):
        self.client = registry_client
        self.base_card = base_agent_card
        self.instances = {}
    
    def register_instance(self, instance_id, instance_config):
        """Register a new instance of the agent."""
        instance_card = self.base_card.copy()
        instance_card['name'] = f"{self.base_card['name']}-{instance_id}"
        instance_card['url'] = instance_config.get('url', instance_card['url'])
        
        # Add instance-specific metadata
        instance_card['metadata'] = instance_card.get('metadata', {})
        instance_card['metadata'].update({
            'instance_id': instance_id,
            'instance_type': instance_config.get('type', 'standard'),
            'region': instance_config.get('region', 'unknown'),
            'capacity': instance_config.get('capacity', 100)
        })
        
        # Modify skills based on instance capabilities
        if 'skill_overrides' in instance_config:
            for skill in instance_card['skills']:
                if skill['id'] in instance_config['skill_overrides']:
                    skill.update(instance_config['skill_overrides'][skill['id']])
        
        result = self.client.register_agent(instance_card)
        self.instances[instance_id] = {
            'card': instance_card,
            'config': instance_config,
            'registered': True
        }
        
        print(f"Registered instance {instance_id} of {self.base_card['name']}")
        return result
    
    def unregister_instance(self, instance_id):
        """Unregister a specific instance."""
        if instance_id in self.instances:
            agent_name = f"{self.base_card['name']}-{instance_id}"
            result = self.client.unregister_agent(agent_name)
            self.instances[instance_id]['registered'] = False
            print(f"Unregistered instance {instance_id}")
            return result
    
    def scale_instances(self, target_count, instance_template):
        """Scale the number of instances up or down."""
        current_count = len([
            inst for inst in self.instances.values() 
            if inst['registered']
        ])
        
        if target_count > current_count:
            # Scale up
            for i in range(current_count, target_count):
                instance_config = instance_template.copy()
                instance_config['url'] = instance_config['url'].replace(
                    '{instance}', str(i)
                )
                self.register_instance(f"instance-{i}", instance_config)
        
        elif target_count < current_count:
            # Scale down
            instances_to_remove = list(self.instances.keys())[target_count:]
            for instance_id in instances_to_remove:
                self.unregister_instance(instance_id)

# Usage example
def main():
    from examples.basic_usage import A2ARegistryClient
    
    client = A2ARegistryClient()
    
    base_card = {
        "name": "worker-agent",
        "description": "Scalable worker agent for distributed processing",
        "url": "http://worker-base:8000",
        "version": "0.420.0",
        "protocol_version": "0.3.0",
        "skills": [
            {
                "id": "process_task",
                "description": "Process computational tasks"
            }
        ]
    }
    
    multi_agent = MultiInstanceAgent(client, base_card)
    
    # Define instance template
    instance_template = {
        'type': 'worker',
        'url': 'http://worker-{instance}:8000',
        'region': 'us-east-1',
        'capacity': 50
    }
    
    # Scale to 3 instances
    multi_agent.scale_instances(3, instance_template)
    
    # Register a specialized instance
    multi_agent.register_instance('gpu-worker', {
        'type': 'gpu-accelerated',
        'url': 'http://gpu-worker:8000',
        'region': 'us-west-2',
        'capacity': 200,
        'skill_overrides': {
            'process_task': {
                'description': 'Process GPU-accelerated computational tasks',
                'gpu_required': True
            }
        }
    })
    
    # List all registered instances
    agents = client.list_agents()
    worker_agents = [
        agent for agent in agents['agents']
        if agent['name'].startswith('worker-agent')
    ]
    print(f"Total worker instances: {len(worker_agents)}")

if __name__ == "__main__":
    main()
```

This comprehensive guide covers various agent registration patterns, from simple basic registration to complex multi-instance and dynamic skill management scenarios.