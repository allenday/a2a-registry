#!/usr/bin/env python3
"""
Demo script showing vector generation from agent cards.

This script demonstrates:
1. Loading agent card data
2. Generating vectors from text fields
3. Performing similarity search
4. Vector storage and retrieval
"""

import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from a2a_registry.vector_generator import VectorGenerator


def load_steve_jobs_agent_card():
    """Load the Steve Jobs agent card example."""
    card_path = Path(__file__).parent.parent / "docs" / "documentation" / "steve-jobs-agentcard.json"
    
    if not card_path.exists():
        raise FileNotFoundError(f"Steve Jobs agent card not found at: {card_path}")
    
    with open(card_path, 'r') as f:
        return json.load(f)


def main():
    """Main demo function."""
    print("🤖 A2A Registry Vector Generation Demo")
    print("=" * 50)
    
    try:
        # Initialize vector generator
        print("📡 Initializing vector generator...")
        generator = VectorGenerator("all-MiniLM-L6-v2")
        print(f"✅ Model loaded: {generator.model_name} ({generator.vector_dimensions} dimensions)")
        
        # Load agent card
        print("\n📋 Loading Steve Jobs agent card...")
        agent_card = load_steve_jobs_agent_card()
        print(f"✅ Loaded agent: {agent_card['name']}")
        
        # Generate vectors
        print("\n🔧 Generating vectors from agent card...")
        vectors = generator.generate_agent_vectors(agent_card)
        print(f"✅ Generated {len(vectors)} vectors")
        
        # Display vector information
        print("\n📊 Vector Summary:")
        print("-" * 30)
        
        field_counts = {}
        for vector in vectors:
            field_type = vector.field_path.split('[')[0] if '[' in vector.field_path else vector.field_path
            field_counts[field_type] = field_counts.get(field_type, 0) + 1
        
        for field_type, count in sorted(field_counts.items()):
            print(f"  {field_type}: {count} vectors")
        
        # Show some example vectors
        print("\n🔍 Example Vectors:")
        print("-" * 30)
        
        for i, vector in enumerate(vectors[:5]):  # Show first 5 vectors
            print(f"\n  Vector {i+1}:")
            print(f"    Field: {vector.field_path}")
            print(f"    Content: {vector.field_content[:100]}{'...' if len(vector.field_content) > 100 else ''}")
            print(f"    Dimensions: {len(vector.values)}")
            print(f"    Model: {vector.metadata.fields['model'].string_value}")
        
        # Demonstrate similarity search
        print("\n🔍 Similarity Search Demo:")
        print("-" * 30)
        
        # Test queries
        test_queries = [
            "strategic planning and vision",
            "product innovation and design",
            "leadership and team management",
            "technology and innovation"
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            query_vector = generator.generate_query_vector(query)
            
            # Search for similar vectors
            results = generator.search_similar_vectors(
                query_vector, vectors, threshold=0.3, max_results=3
            )
            
            if results:
                print(f"    Found {len(results)} similar vectors:")
                for j, (result_vector, similarity) in enumerate(results, 1):
                    print(f"      {j}. {result_vector.field_path} (similarity: {similarity:.3f})")
                    print(f"         Content: {result_vector.field_content[:80]}{'...' if len(result_vector.field_content) > 80 else ''}")
            else:
                print("    No similar vectors found above threshold")
        
        # Demonstrate competency extraction
        print("\n🎯 Competency Extraction Demo:")
        print("-" * 30)
        
        competency_vectors = [v for v in vectors if "competency" in v.field_content.lower()]
        if competency_vectors:
            for vector in competency_vectors:
                print(f"\n  Field: {vector.field_path}")
                print(f"  Content: {vector.field_content[:200]}{'...' if len(vector.field_content) > 200 else ''}")
        else:
            print("  No competency-related vectors found")
        
        print("\n✅ Demo completed successfully!")
        
    except ImportError as e:
        print(f"❌ Error: Missing dependencies - {e}")
        print("💡 Install with: pip install sentence-transformers numpy")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())