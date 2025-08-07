#!/usr/bin/env python3
"""Integration test to reproduce and verify fix for identical similarity scores bug."""

import asyncio
import json
import logging
import pytest
from pathlib import Path

from a2a_registry.vector_enhanced_storage import VectorEnhancedStorage
from a2a_registry.storage import InMemoryStorage

logger = logging.getLogger(__name__)


class TestVectorSearchBugReproduction:
    """Test class to reproduce the identical similarity scores bug with real agent data."""

    @pytest.fixture
    async def storage_with_agents(self):
        """Set up vector storage with test agents loaded."""
        # Create storage
        backend = InMemoryStorage()
        storage = VectorEnhancedStorage(backend)
        
        # Load test agents
        fixtures_dir = Path(__file__).parent / "fixtures"
        agent_files = [
            "alexander_hamilton.json",
            "benjamin_franklin.json", 
            "constantine.json",
            "cyrus_the_great.json",
            "deng_xiaoping.json",
            "george_washington.json",
            "lorenzo_de_medici.json",
            "martin_luther.json"
        ]
        
        registered_agents = []
        for filename in agent_files:
            file_path = fixtures_dir / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    agent_card = data.get('agent_card')
                    if agent_card:
                        success = await storage.register_agent(agent_card)
                        if success:
                            registered_agents.append(agent_card)
                            logger.info(f"Registered agent: {agent_card.get('name', 'Unknown')}")
        
        logger.info(f"Total agents registered: {len(registered_agents)}")
        
        # Verify vectors were generated
        stats = storage.get_vector_stats()
        logger.info(f"Vector stats: {stats}")
        
        return storage, registered_agents

    @pytest.mark.asyncio
    async def test_reproduce_identical_similarity_scores_bug(self, storage_with_agents):
        """Test that reproduces the bug where all agents get identical similarity scores."""
        storage, agents = storage_with_agents
        
        # Skip if no agents were loaded
        if len(agents) < 2:
            pytest.skip("Need at least 2 agents to test similarity score distribution")
        
        # Test the problematic query that causes identical scores
        problematic_query = "long term thinking and strategy"
        
        results = await storage.search_agents_vector(
            query=problematic_query,
            similarity_threshold=0.3,  # Lower threshold to get more results
            max_results=len(agents)
        )
        
        print(f"\n=== Results for '{problematic_query}' ===")
        print(f"Found {len(results)} results:")
        
        scores = []
        for i, (agent, score) in enumerate(results):
            agent_name = agent.get('name', f'Agent_{i}')
            print(f"  {i+1}. {agent_name:25s}: {score:.10f}")
            scores.append(score)
        
        # Analyze score distribution
        unique_scores = set(scores)
        print(f"\nScore Analysis:")
        print(f"  Total results: {len(scores)}")
        print(f"  Unique scores: {len(unique_scores)}")
        print(f"  Unique score values: {sorted(unique_scores)}")
        
        # The bug: all scores are identical
        if len(unique_scores) == 1 and len(scores) > 1:
            print("❌ BUG CONFIRMED: All agents have identical similarity scores!")
            
            # Additional debugging
            print(f"\nDEBUG INFO:")
            print(f"  Identical score value: {list(unique_scores)[0]}")
            
            # Check if this is a specific mathematical constant
            identical_score = list(unique_scores)[0]
            print(f"  Score as float: {identical_score}")
            print(f"  Score precision: {identical_score:.15f}")
            
        else:
            print("✅ SCORES VARY: Different agents have different similarity scores")
        
        # Test with a different query to confirm vector search works for other queries
        working_query = "financial systems and institutions"
        
        results2 = await storage.search_agents_vector(
            query=working_query,
            similarity_threshold=0.3,
            max_results=len(agents)
        )
        
        print(f"\n=== Results for '{working_query}' (comparison) ===")
        print(f"Found {len(results2)} results:")
        
        scores2 = []
        for i, (agent, score) in enumerate(results2):
            agent_name = agent.get('name', f'Agent_{i}')
            print(f"  {i+1}. {agent_name:25s}: {score:.10f}")
            scores2.append(score)
        
        unique_scores2 = set(scores2)
        print(f"\nComparison Query Score Analysis:")
        print(f"  Total results: {len(scores2)}")
        print(f"  Unique scores: {len(unique_scores2)}")
        
        # Assert the bug exists for the problematic query
        # (This test is meant to FAIL initially to confirm the bug, then PASS after fix)
        assert len(unique_scores) > 1 or len(scores) <= 1, \
            f"BUG DETECTED: All {len(scores)} agents returned identical similarity score {list(unique_scores)[0]}"

    @pytest.mark.asyncio
    async def test_vector_search_score_distribution(self, storage_with_agents):
        """Test that different agents should have different similarity scores for different queries."""
        storage, agents = storage_with_agents
        
        if len(agents) < 3:
            pytest.skip("Need at least 3 agents to test score distribution")
        
        test_queries = [
            "strategic planning and vision",
            "financial architecture", 
            "civic institutions and democracy",
            "military leadership and conquest",
            "economic transformation",
            "political philosophy"
        ]
        
        for query in test_queries:
            print(f"\n=== Testing query: '{query}' ===")
            
            results = await storage.search_agents_vector(
                query=query,
                similarity_threshold=0.2,
                max_results=len(agents)
            )
            
            if len(results) < 2:
                print(f"  Only {len(results)} results, skipping distribution test")
                continue
            
            scores = [score for _, score in results]
            unique_scores = set(scores)
            
            print(f"  Results: {len(results)}")
            print(f"  Unique scores: {len(unique_scores)}")
            print(f"  Score range: {min(scores):.4f} - {max(scores):.4f}")
            
            # Print top results
            for i, (agent, score) in enumerate(results[:5]):
                agent_name = agent.get('name', f'Agent_{i}')
                print(f"    {i+1}. {agent_name:20s}: {score:.6f}")
            
            # Healthy vector search should produce varied scores
            # Allow some identical scores but not ALL identical
            max_identical_ratio = 0.8  # At most 80% of results can have same score
            most_common_score_count = max(scores.count(score) for score in unique_scores)
            identical_ratio = most_common_score_count / len(scores)
            
            print(f"  Most common score appears {most_common_score_count}/{len(scores)} times ({identical_ratio:.1%})")
            
            # This should pass when the bug is fixed
            assert identical_ratio < max_identical_ratio, \
                f"Too many identical scores for query '{query}': {most_common_score_count}/{len(scores)} agents have the same score"

    @pytest.mark.asyncio 
    async def test_vector_generation_sanity_check(self, storage_with_agents):
        """Verify that vector generation is working and producing different vectors for different agents."""
        storage, agents = storage_with_agents
        
        if len(agents) < 2:
            pytest.skip("Need at least 2 agents to compare vectors")
        
        # Get vectors for first two agents
        agent1_name = agents[0].get('name', 'Agent1')
        agent2_name = agents[1].get('name', 'Agent2') 
        
        vectors1 = await storage.get_agent_vectors(agent1_name)
        vectors2 = await storage.get_agent_vectors(agent2_name)
        
        print(f"\nVector Generation Check:")
        print(f"  {agent1_name}: {len(vectors1)} vectors")
        print(f"  {agent2_name}: {len(vectors2)} vectors")
        
        assert len(vectors1) > 0, f"No vectors generated for {agent1_name}"
        assert len(vectors2) > 0, f"No vectors generated for {agent2_name}"
        
        # Compare first vectors to ensure they're different
        if vectors1 and vectors2:
            v1_values = vectors1[0].values
            v2_values = vectors2[0].values
            
            print(f"  {agent1_name} first vector: {len(v1_values)} dimensions")
            print(f"  {agent2_name} first vector: {len(v2_values)} dimensions") 
            print(f"  First 5 values of {agent1_name}: {v1_values[:5]}")
            print(f"  First 5 values of {agent2_name}: {v2_values[:5]}")
            
            # Vectors should be different
            import numpy as np
            are_identical = np.allclose(v1_values, v2_values, atol=1e-6)
            print(f"  Vectors identical: {are_identical}")
            
            assert not are_identical, "Different agents should not have identical vectors"

    @pytest.mark.asyncio
    async def test_manual_similarity_calculation(self, storage_with_agents):
        """Manually test similarity calculation to isolate where the bug occurs."""
        storage, agents = storage_with_agents
        
        if len(agents) < 2:
            pytest.skip("Need at least 2 agents for manual similarity test")
        
        # Generate query vector
        test_query = "long term thinking and strategy"
        query_vector = storage.vector_generator.generate_query_vector(test_query)
        
        print(f"\nManual Similarity Calculation Test:")
        print(f"Query: '{test_query}'")
        print(f"Query vector dimensions: {len(query_vector.values)}")
        print(f"Query vector (first 5): {query_vector.values[:5]}")
        
        # Get vectors for first few agents and manually calculate similarities
        manual_similarities = []
        
        for i, agent in enumerate(agents[:3]):  # Test first 3 agents
            agent_name = agent.get('name', f'Agent_{i}')
            agent_vectors = await storage.get_agent_vectors(agent_name)
            
            if agent_vectors:
                # Calculate similarity with first vector of this agent
                first_vector = agent_vectors[0]
                similarity = storage.vector_generator.calculate_similarity(query_vector, first_vector)
                manual_similarities.append((agent_name, similarity))
                
                print(f"  {agent_name}:")
                print(f"    Vector count: {len(agent_vectors)}")
                print(f"    First vector field: {first_vector.field_path}")
                print(f"    Manual similarity: {similarity:.10f}")
        
        # Check if manual calculations also show identical scores
        manual_scores = [sim for _, sim in manual_similarities]
        unique_manual_scores = set(manual_scores)
        
        print(f"\nManual calculation results:")
        print(f"  Unique scores: {len(unique_manual_scores)}")
        print(f"  Score values: {list(unique_manual_scores)}")
        
        if len(unique_manual_scores) == 1 and len(manual_scores) > 1:
            print("❌ BUG CONFIRMED: Even manual similarity calculation produces identical scores!")
        else:
            print("✅ Manual calculation produces varied scores")

if __name__ == "__main__":
    # Run the test directly for debugging
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    async def main():
        test_instance = TestVectorSearchBugReproduction()
        
        # Setup storage with agents
        storage, agents = await test_instance.storage_with_agents()
        
        # Run the bug reproduction test
        print("Running vector search bug reproduction test...")
        try:
            await test_instance.test_reproduce_identical_similarity_scores_bug((storage, agents))
        except AssertionError as e:
            print(f"Test failed as expected (bug confirmed): {e}")
        
        # Run manual similarity test
        print("\nRunning manual similarity calculation test...")
        await test_instance.test_manual_similarity_calculation((storage, agents))
    
    asyncio.run(main())