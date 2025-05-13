# Query Understanding Test Results

This document presents detailed test results for the LLM Query Understanding Service, highlighting its capabilities, limitations, and performance characteristics.

## Test Results Summary

The service was tested using Docker deployment with enhanced logging enabled and Redis caching activated. The tests used Qwen2-0.5B-Instruct as the underlying language model.

### Performance Metrics

| Query Type | First Query Time | Cached Query Time | Performance Improvement |
|------------|------------------|-------------------|-------------------------|
| Simple queries | 20-40 seconds | < 0.001 seconds | ~40,000x faster |
| Complex queries | 60-120 seconds | < 0.001 seconds | ~100,000x faster |

### Success Cases

The service correctly parsed these query types:

1. **Standard Furniture Queries**
   - `blue metal dining table` → Correctly identified item type, material, and color
   - `leather sofa with black legs` → Correctly extracted the main furniture attributes
   - `red plastic chair for children` → Accurately identified key attributes

2. **Caching Performance**
   - Repeat queries served entirely from cache in sub-millisecond timeframe
   - Cache hit rate approaches 100% for identical queries

### Edge Cases and Handling

1. **Previously Problematic Cases (Now Fixed)**
   - `gold metal accent table` → Correctly identifies "accent table" as item type, "metal" as material, and "gold" as color
   - `amber glass cabinet for display` → Correctly identifies "display cabinet" as item type, "glass" as material, and "amber" as color
   - `glass display shelving unit with metal frame` → Correctly identifies "shelving unit" as item type and "glass" as material

2. **Material vs. Color Ambiguity Resolution**
   - Implemented specific rules in prompt and post-processing to ensure proper handling of ambiguous terms like "gold metal" (gold=color, metal=material)
   - Added explicit examples to guide the model toward correct classification

3. **Component vs. Item Type Disambiguation**
   - Edge case handler ensures proper classification when material terms like "glass" appear with item types like "cabinet" or "shelving unit"

4. **JSON Parsing Improvements**
   - Enhanced prompt format for more consistent JSON output
   - Added fallback parsing methods for handling potential variations in LLM output format
   - Custom post-processing function to handle known edge cases

## Performance Analysis

### Response Time Breakdown

1. **First-time Queries**:
   - Cache lookup: ~0.001 seconds
   - LLM initialization: ~3-10 seconds
   - Model inference: ~20-100+ seconds
   - Result parsing: ~0.01 seconds
   - Total time: ~23-117 seconds

2. **Cached Queries**:
   - Cache lookup: ~0.0003 seconds
   - Total time: ~0.0004 seconds

### Logging Insights

The enhanced logging system effectively captures:

- Request correlation IDs across components
- Precise timing measurements for each processing stage
- Cache hit/miss statistics
- Input/output data flows
- Warning events for potential issues

## Recommendations

Based on testing results, we recommend:

1. **Model Fine-tuning**
   - Improve handling of ambiguous terms (e.g., wooden, glass) that can be both materials and descriptors
   - Enhance recognition of composite furniture terms

2. **Prompt Engineering**
   - Clarify handling of descriptive terms vs. materials
   - Add examples for edge cases to system prompt

3. **Caching Strategy**
   - Current Redis implementation works effectively
   - Consider implementing semantic similarity for near-duplicate queries

4. **Production Scaling**
   - Given long inference times, consider:
     - Batch processing for non-interactive use cases
     - Multiple worker instances
     - GPU acceleration for sub-second response times

## Conclusion

The LLM Query Understanding Service demonstrates robust performance for standard furniture queries. The Redis caching system provides dramatic performance improvements for repeat queries. Further improvements to prompt engineering and potentially model fine-tuning would help address the identified edge cases.
