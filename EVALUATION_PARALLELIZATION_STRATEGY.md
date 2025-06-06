# Evaluation Parallelization Strategy: Sequence-Level Concurrency

## Current Architecture Analysis

**Current Execution Pattern:**
```
For each model:
  For each sequence (1, 2, 3...):
    For each run (1, 2, 3):
      For each prompt in sequence (A, B, C):
        - Execute prompt with accumulated context
        - Add response to context history
      - Reset context between sequences
```

**Context Isolation Requirements:**
- ✅ **Within Sequence**: Context must accumulate (A → A+B → A+B+C)
- ✅ **Between Sequences**: Context must reset (Seq1 → RESET → Seq2)
- ✅ **Between Runs**: Context must reset (Run1 → RESET → Run2)
- ✅ **Between Models**: Independent evaluators, natural isolation

## Proposed Parallelization Strategy

### **Level 1: Sequence-Level Parallelization** 
*Safe, high-impact optimization*

**Execution Pattern:**
```
For each model:
  Parallel execution of:
    - Sequence 1 (all runs)
    - Sequence 2 (all runs)  
    - Sequence 3 (all runs)
    - ... (continue for all sequences)
```

**Benefits:**
- **3x-15x speedup** (depending on number of sequences)
- **Natural isolation**: Each sequence worker maintains its own context
- **API efficiency**: Multiple concurrent API connections per model
- **Safe implementation**: No cross-sequence dependencies

### **Level 2: Model-Level Parallelization**
*Maximum performance for multi-model evaluations*

**Execution Pattern:**
```
Parallel execution of:
  Model 1: Parallel sequences
  Model 2: Parallel sequences
  Model 3: Parallel sequences
```

**Benefits:**
- **Additional 3x-10x speedup** (depending on number of models)
- **Provider diversity**: Can mix different API providers simultaneously
- **Resource utilization**: Maximize API rate limits across providers

## Implementation Design

### **Sequence Worker Architecture**

Each sequence worker would be responsible for:
1. **Context Management**: Maintain sequence-specific context state
2. **Run Execution**: Execute all runs for assigned sequence
3. **Error Handling**: Isolated failure handling per sequence
4. **Progress Reporting**: Thread-safe progress updates

### **Concurrency Controls**

1. **Rate Limiting**: Respect API provider rate limits
   - OpenAI: 10,000 RPM → Allow 10-20 concurrent sequences
   - Anthropic: 4,000 RPM → Allow 8-15 concurrent sequences
   - Local models: CPU/GPU bound → 2-4 concurrent sequences

2. **Resource Management**: 
   - Memory usage per sequence context
   - Database connection pooling
   - Error circuit breakers per sequence

3. **Progress Synchronization**:
   - Thread-safe progress aggregation
   - Atomic database updates
   - Coordinated checkpoint creation

## Risk Analysis & Mitigation

### **Low Risk Areas** ✅
- **Context isolation**: Natural boundaries between sequences
- **Database operations**: Already atomic with our optimizations
- **API calls**: Stateless, naturally parallelizable
- **Error handling**: Can be isolated per sequence

### **Medium Risk Areas** ⚠️
- **Rate limiting**: Need sophisticated rate limit management
- **Memory usage**: Multiple context states in memory
- **Progress tracking**: Coordination complexity
- **Resume functionality**: More complex checkpoint state

### **Mitigation Strategies**
1. **Conservative start**: Begin with 3-5 concurrent sequences
2. **Adaptive concurrency**: Adjust based on API response times
3. **Graceful degradation**: Fall back to serial execution on errors
4. **Comprehensive monitoring**: Track per-sequence performance

## Expected Performance Gains

### **Conservative Estimate** (3 sequences, 3 models)
- **Current**: 45 prompts × 3 models = 135 sequential API calls
- **Parallel**: 3 concurrent sequences = ~3x speedup
- **Total improvement**: 7-8 hours → 2.5-3 hours

### **Aggressive Estimate** (15 sequences, 5 models)  
- **Current**: 225 sequential API calls
- **Parallel**: 15 concurrent sequences × 5 models = ~15x speedup
- **Total improvement**: 7-8 hours → 30-40 minutes

## Implementation Priority

This optimization should be considered for **Phase 2** after completing Phase 1, as it:
- **Builds on Phase 1 optimizations** (database performance, context management)
- **Requires significant architectural changes** (concurrency management)
- **Has high impact** but also **higher complexity**
- **Benefits from proven Phase 1 stability** before adding concurrency

## Recommendation

**For immediate impact**: Complete Phase 1.3 (API retry logic) first to ensure reliability.

**For maximum performance**: Add this as Phase 2.0 (Sequence-level parallelization).

The combination of Phase 1 optimizations + sequence parallelization could reduce your 7-8 hour evaluation cycles to **under 1 hour** for typical workloads.
