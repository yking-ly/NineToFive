"""
Test script to demonstrate smart retrieval capabilities
"""

import sys
import os

# Add backend to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from retrieval import analyze_query_complexity, determine_chunk_count, generate_query_expansions

def test_query(query, tag=None):
    """Test a single query and display analysis"""
    print("\n" + "=" * 70)
    print(f"QUERY: {query}")
    if tag:
        print(f"TAG: {tag}")
    print("=" * 70)
    
    # Analyze complexity
    complexity = analyze_query_complexity(query)
    print(f"\n📊 Analysis:")
    print(f"   Type: {complexity['type'].upper()}")
    print(f"   Confidence: {complexity['confidence']:.2f}")
    print(f"   Word Count: {complexity['word_count']}")
    if complexity['keywords']:
        print(f"   Legal Terms: {', '.join(complexity['keywords'])}")
    
    # Determine chunks
    chunks = determine_chunk_count(complexity, tag)
    print(f"\n📦 Retrieval Strategy:")
    print(f"   Chunks to retrieve: {chunks}")
    
    # Generate expansions
    if complexity['type'] in ['complex', 'comparative']:
        expansions = generate_query_expansions(query, complexity)
        if expansions:
            print(f"   Query expansions:")
            for i, exp in enumerate(expansions, 1):
                print(f"      {i}. {exp}")
    
    print()

def main():
    print("\n" + "=" * 70)
    print("SMART RETRIEVAL SYSTEM - TEST SUITE")
    print("=" * 70)
    
    # Test cases
    test_cases = [
        # Simple queries
        ("What is Section 302 IPC?", None),
        ("Define murder", None),
        ("Punishment for theft", "ipc"),
        
        # Complex queries
        ("Explain the implications of Section 420 IPC on fraud cases", None),
        ("Why is mens rea important in determining criminal liability?", None),
        ("Discuss the relationship between IPC and BNS", None),
        
        # Comparative queries
        ("Compare IPC Section 302 and BNS Section 103", None),
        ("What is the difference between theft and robbery?", "ipc"),
        ("IPC vs BNS: What are the major changes?", None),
        
        # Procedural queries
        ("How to file an FIR?", None),
        ("Steps to register a complaint under Section 498A", "ipc"),
        ("Procedure for bail application in criminal cases", None),
    ]
    
    for query, tag in test_cases:
        test_query(query, tag)
    
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\n💡 Observations:")
    print("   • Simple queries use fewer chunks (3)")
    print("   • Complex queries use more chunks (6-7)")
    print("   • Comparative queries use the most chunks (7-8)")
    print("   • Tags reduce chunk count (more focused)")
    print("   • Complex queries get query expansions")
    print()

if __name__ == "__main__":
    main()
