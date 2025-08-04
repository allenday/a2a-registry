# Competencies and Vector Search Extensions

This document describes the proposed extensions to the A2A Registry protocol to support agent competencies and vector-based semantic search.

## Overview

The extensions add two key capabilities to the registry:

1. **Competencies**: Structured representation of agent capabilities with confidence scores
2. **Vector Search**: Semantic search using embedding vectors for natural language queries

## Competencies

### Competency Model

Competencies represent specific capabilities or skills that an agent possesses, with confidence scores indicating proficiency levels.

```protobuf
message Competency {
  string name = 1;                    // e.g., "strategic planning and long-term vision"
  float confidence_score = 2;         // 0.0 to 1.0 proficiency level
  string description = 3;             // Optional description
  google.protobuf.Struct metadata = 4; // Optional metadata
}
```

### CompetencySet

A collection of competencies for an agent or extension:

```protobuf
message CompetencySet {
  map<string, Competency> competencies = 1;
  float overall_confidence = 2;
  google.protobuf.Timestamp last_updated = 3;
  string assessment_source = 4;       // e.g., "self-assessment", "verified"
}
```

### Example Competency Data

```json
{
  "competencies": {
    "strategic planning and long-term vision": {
      "name": "strategic planning and long-term vision",
      "confidence_score": 0.95,
      "description": "Ability to develop comprehensive strategic plans and long-term vision",
      "metadata": {
        "category": "leadership",
        "verified_by": "peer_review"
      }
    },
    "team leadership and inspiring others": {
      "name": "team leadership and inspiring others", 
      "confidence_score": 0.92,
      "description": "Capability to lead teams and inspire others to achieve goals"
    }
  },
  "overall_confidence": 0.93,
  "assessment_source": "self_assessment"
}
```

## Vector Search

### Vector Representation

Vectors are used for semantic search and similarity matching:

```protobuf
message Vector {
  repeated float values = 1;          // Embedding vector values
  google.protobuf.Struct metadata = 2; // Optional metadata
}
```

### Vector Search Configuration

Configurable parameters for vector search:

```protobuf
message VectorSearchConfig {
  string embedding_model = 1;         // e.g., "text-embedding-ada-002"
  int32 vector_dimensions = 2;        // e.g., 1536
  float similarity_threshold = 3;     // 0.0 to 1.0
  int32 max_results = 4;
  bool use_approximate_search = 5;    // For performance
  google.protobuf.Struct metadata = 6;
}
```

## Enhanced Agent Extensions

Agent extensions are enhanced with competencies and vectors:

```protobuf
message EnhancedAgentExtension {
  a2a.v1.AgentExtension extension = 1;
  CompetencySet competencies = 2;
  Vector semantic_vector = 3;
  // ... registry metadata
}
```

## Search Capabilities

### Multi-Modal Search

The registry supports three search modes:

1. **Keyword Search**: Traditional text-based search
2. **Vector Search**: Semantic search using embeddings
3. **Hybrid Search**: Combination of both approaches

### Search Criteria Extensions

```protobuf
message AgentSearchCriteria {
  // Existing fields...
  
  // Competency filters
  repeated string required_competencies = 13;
  float min_competency_score = 14;
  
  // Vector search
  VectorSearchConfig vector_search_config = 15;
  Vector query_vector = 16;
  string semantic_query = 17;         // Text to vectorize
  
  string search_mode = 18;            // "keyword", "vector", "hybrid"
}
```

## New Service Methods

### Competency Operations

- `UpdateAgentCompetencies`: Update agent competencies
- `SearchByCompetencies`: Search agents by specific competencies

### Vector Search Operations

- `SemanticSearch`: Perform semantic search using text queries
- `UpdateAgentVectors`: Update agent and extension vectors

## Usage Examples

### 1. Register Agent with Competencies

```python
# Agent registration with competencies
agent_card = RegistryAgentCard(
    agent_card=a2a_agent_card,
    registry_metadata=RegistryMetadata(
        overall_competencies=CompetencySet(
            competencies={
                "strategic_planning": Competency(
                    name="strategic planning and long-term vision",
                    confidence_score=0.95
                ),
                "team_leadership": Competency(
                    name="team leadership and inspiring others", 
                    confidence_score=0.92
                )
            },
            overall_confidence=0.93,
            assessment_source="self_assessment"
        )
    )
)
```

### 2. Semantic Search

```python
# Search for agents with strategic planning capabilities
request = SemanticSearchRequest(
    query="I need an agent that can help with strategic planning and long-term vision",
    search_config=VectorSearchConfig(
        embedding_model="text-embedding-ada-002",
        similarity_threshold=0.8,
        max_results=10
    ),
    trust_levels=[TRUST_LEVEL_VERIFIED, TRUST_LEVEL_OFFICIAL]
)
```

### 3. Competency-Based Filtering

```python
# Search by specific competencies
request = SearchByCompetenciesRequest(
    required_competencies=["strategic planning", "team leadership"],
    min_competency_score=0.9,
    trust_levels=[TRUST_LEVEL_VERIFIED]
)
```

### 4. Hybrid Search

```python
# Combine keyword and semantic search
request = SearchAgentsRequest(
    criteria=AgentSearchCriteria(
        required_skills=["leadership"],
        required_competencies=["strategic planning"],
        semantic_query="long-term vision and planning",
        search_mode="hybrid",
        vector_search_config=VectorSearchConfig(
            similarity_threshold=0.7
        )
    )
)
```

## Implementation Considerations

### Vector Generation

1. **Agent-Level Vectors**: Generated from agent description, skills, and overall competencies
2. **Extension-Level Vectors**: Generated from extension description and associated competencies
3. **Query Vectors**: Generated on-demand from search queries

### Vector Storage

- Use vector databases like Pinecone, Weaviate, or pgvector
- Store vectors alongside agent metadata
- Implement vector similarity search with configurable thresholds

### Competency Assessment

1. **Self-Assessment**: Agents declare their own competencies
2. **Peer Review**: Community validation of competencies
3. **Automated Assessment**: ML-based competency evaluation
4. **Verified Assessment**: Official verification by trusted authorities

### Performance Optimization

1. **Approximate Search**: Use ANN algorithms for large-scale vector search
2. **Caching**: Cache frequently accessed vectors and search results
3. **Indexing**: Maintain efficient indexes for competency and vector queries
4. **Pagination**: Support pagination for large result sets

## Migration Strategy

### Backward Compatibility

- All new fields are optional
- Existing agents without competencies continue to work
- Vector search is opt-in
- Default search mode remains "keyword"

### Gradual Rollout

1. **Phase 1**: Add competency support to registry metadata
2. **Phase 2**: Implement vector generation and storage
3. **Phase 3**: Enable semantic search capabilities
4. **Phase 4**: Add hybrid search and advanced filtering

## Security and Privacy

### Vector Privacy

- Vectors may contain sensitive information about agent capabilities
- Implement access controls for vector data
- Consider encryption for stored vectors
- Audit vector access and usage

### Competency Verification

- Implement verification workflows for competency claims
- Support different trust levels for competency sources
- Allow agents to challenge or dispute competency assessments
- Maintain audit trails for competency changes

## Future Enhancements

### Advanced Features

1. **Competency Evolution**: Track competency changes over time
2. **Skill Gap Analysis**: Identify missing competencies for specific tasks
3. **Competency Recommendations**: Suggest relevant competencies for agents
4. **Multi-Modal Vectors**: Support for image, audio, and other modalities
5. **Federated Search**: Search across multiple registry instances

### Integration Opportunities

1. **MCP Extensions**: Integrate with MCP protocol extensions
2. **Agent Marketplaces**: Support for agent discovery platforms
3. **Workflow Orchestration**: Competency-aware task routing
4. **Performance Analytics**: Track agent performance against competencies 