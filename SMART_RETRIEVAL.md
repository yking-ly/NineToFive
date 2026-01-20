# Smart Retrieval System Documentation

## Overview
The intelligent retrieval system analyzes user queries to determine their complexity and automatically adjusts the retrieval strategy for optimal context gathering.

## Key Features

### 1. **Query Complexity Analysis**
The system classifies queries into four types:

#### **Simple Queries** (3 chunks)
- Factual questions with clear answers
- Examples:
  - "What is Section 302 IPC?"
  - "Define murder"
  - "Punishment for theft"

#### **Complex Queries** (6 chunks)
- Analytical questions requiring deeper context
- Examples:
  - "Explain the implications of Section 420"
  - "Why is mens rea important in criminal law?"
  - "Discuss the relationship between IPC and BNS"

#### **Comparative Queries** (8 chunks)
- Questions comparing multiple concepts
- Examples:
  - "Compare IPC Section 302 and BNS Section 103"
  - "Difference between theft and robbery"
  - "IPC vs BNS: What changed?"

#### **Procedural Queries** (5 chunks)
- Process-oriented questions
- Examples:
  - "How to file an FIR?"
  - "Steps to register a complaint"
  - "Procedure for bail application"

### 2. **Dynamic Chunk Retrieval**
- **Adaptive Sizing**: Automatically adjusts number of chunks based on query type
- **Confidence-Based**: Increases chunks for high-confidence complex queries
- **Tag-Aware**: Reduces chunks when category tag is specified (more focused search)

### 3. **Multi-Strategy Search**

#### **Strategy 1: Direct Similarity Search**
- Primary vector similarity search across all shards
- Parallel execution for speed

#### **Strategy 2: Query Expansion** (for complex/comparative queries)
- Breaks down complex queries into sub-queries
- Searches for component parts separately
- Example: "Compare IPC and BNS" → searches for "IPC" and "BNS" separately

### 4. **Smart Filtering**

#### **Deduplication**
- Removes duplicate chunks based on content similarity
- Uses content hashing to identify near-duplicates

#### **Relevance Thresholding**
- Applies query-type-specific relevance thresholds
- Simple queries: Strict threshold (1.2) - exact matches only
- Complex queries: Lenient threshold (1.8) - broader context
- Comparative queries: Very lenient (2.0) - diverse sources
- Procedural queries: Moderate (1.5) - step-by-step info

### 5. **Legal Term Extraction**
- Automatically identifies legal references (sections, articles, clauses)
- Uses these for targeted sub-queries
- Pattern: `section 302`, `article 21`, `clause 5`, etc.

## How It Works

```
User Query
    ↓
1. Analyze Complexity
    ↓
2. Determine Chunk Count
    ↓
3. Check Cache
    ↓
4. Multi-Strategy Search
    ├─ Direct Similarity
    └─ Query Expansion (if complex)
    ↓
5. Deduplicate Results
    ↓
6. Apply Relevance Threshold
    ↓
7. Select Top K Chunks
    ↓
8. Generate Answer
```

## Examples

### Example 1: Simple Query
```
Query: "What is Section 302 IPC?"
Analysis: Simple (confidence: 0.8)
Chunks: 3
Strategy: Direct search only
Threshold: 1.2 (strict)
Result: Precise answer about Section 302
```

### Example 2: Complex Query
```
Query: "Explain the difference between culpable homicide and murder"
Analysis: Complex (confidence: 0.85)
Chunks: 7 (6 base + 1 for high confidence)
Strategy: Direct + Expanded
Expansions: ["culpable homicide", "murder"]
Threshold: 1.8 (lenient)
Result: Comprehensive comparison with examples
```

### Example 3: Comparative Query with Tag
```
Query: "Compare Section 302 and Section 304"
Tag: IPC
Analysis: Comparative (confidence: 0.9)
Chunks: 7 (8 base - 1 for tag)
Strategy: Direct + Expanded
Expansions: ["Section 302", "Section 304"]
Threshold: 2.0 (very lenient)
Result: Detailed comparison focused on IPC
```

## Benefits

✅ **Better Context**: More relevant chunks for complex questions
✅ **Efficiency**: Fewer chunks for simple questions (faster responses)
✅ **Accuracy**: Relevance filtering ensures quality over quantity
✅ **Coverage**: Query expansion catches related information
✅ **Adaptability**: Automatically adjusts to query characteristics

## Configuration

### Chunk Count Ranges
- Minimum: 3 chunks (simple queries)
- Maximum: 10 chunks (capped for performance)
- Default: 4 chunks (unknown query type)

### Relevance Thresholds
- Simple: 1.2 (L2 distance)
- Complex: 1.8
- Comparative: 2.0
- Procedural: 1.5

### Query Expansion Limits
- Maximum 3 expanded queries
- Only for complex/comparative types
- 2 chunks per expansion

## Performance Impact

### Speed
- Simple queries: **Faster** (fewer chunks)
- Complex queries: **Slightly slower** (query expansion)
- Overall: **Optimized** (parallel search, smart caching)

### Quality
- Simple queries: **Higher precision** (strict threshold)
- Complex queries: **Higher recall** (more chunks, expansions)
- Overall: **Better relevance** (type-aware retrieval)

## Future Enhancements

- [ ] Machine learning-based complexity classification
- [ ] User feedback loop for threshold tuning
- [ ] Semantic query rewriting
- [ ] Cross-document relationship detection
- [ ] Temporal relevance (newer laws prioritized)
- [ ] Citation graph analysis
