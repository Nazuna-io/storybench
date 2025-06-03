# Storybench v1.5 Implementation Plan
*Based on code review findings and evaluation pipeline analysis*

## Overview
This plan addresses critical issues identified in the code review with focus on:
- **Evaluation Pipeline Fidelity**: Ensuring accurate and reliable creative writing evaluations
- **Performance Optimization**: Reducing 7-8 hour evaluation runtimes
- **Open Source Readiness**: Security and maintainability improvements

## Phase 1: Critical Evaluation Fidelity & Performance (Week 1)

### 1.1 Context Management Reliability ⭐ CRITICAL
**Issue**: Context limit validation scattered across multiple components, risk of silent truncation
**Impact**: Could invalidate entire creative writing evaluation results

**Tasks:**
- [ ] Consolidate all context validation into UnifiedContextManager
- [ ] Remove duplicate context checking from BaseEvaluator and API evaluators  
- [ ] Add context validation logging with prompt fingerprints for traceability
- [ ] Implement pre-evaluation context size checks for entire sequences
- [ ] Add context usage analytics to evaluation reports

**Files to modify:**
- `src/storybench/unified_context_system.py` - Make single source of truth
- `src/storybench/evaluators/base.py` - Remove duplicate validation
- `src/storybench/evaluators/api_evaluator.py` - Defer to unified system
- `src/storybench/evaluators/local_evaluator.py` - Defer to unified system

**Success Criteria:**
- Zero context-related evaluation failures in test runs
- All context validation flows through single code path
- Context usage logged for every evaluation step

**Estimated Effort:** 2-3 days

### 1.2 Database Query Optimization ⚡ PERFORMANCE
**Issue**: N+1 query patterns in progress tracking, repeated count queries
**Impact**: Significant performance degradation in 7-8 hour evaluation runs

**Tasks:**
- [ ] Add MongoDB indexes for frequent queries:
  - `evaluation_id` (single field)
  - `{evaluation_id: 1, model_name: 1}` (compound)
  - `{evaluation_id: 1, sequence: 1, run: 1}` (compound)
- [ ] Implement batch progress updates instead of individual calls
- [ ] Cache evaluation progress in memory during active runs
- [ ] Add query performance monitoring/logging
- [ ] Optimize `count_by_evaluation_id()` with aggregation pipeline

**Files to modify:**
- `src/storybench/database/repositories/response_repo.py` - Add indexing, optimize queries
- `src/storybench/database/services/evaluation_runner.py` - Batch updates, caching
- `src/storybench/database/connection.py` - Index creation on startup
- `src/storybench/database/services/evaluation_service.py` - Progress optimization

**Success Criteria:**
- 25-35% reduction in database query time
- Progress updates batch every 10 responses instead of individual
- Query performance metrics logged

**Estimated Effort:** 2 days

### 1.3 API Retry Logic Standardization 🔄 RELIABILITY
**Issue**: Inconsistent retry patterns across OpenAI, Anthropic, Gemini, DeepInfra
**Impact**: Evaluation failures due to temporary API issues, wasted evaluation time

**Tasks:**
- [ ] Create unified `APIRetryHandler` class with exponential backoff
- [ ] Standardize timeout configurations across all providers
- [ ] Implement circuit breaker pattern for repeated failures
- [ ] Add retry attempt logging and analytics
- [ ] Configure provider-specific retry strategies

**Files to modify:**
- `src/storybench/evaluators/api_evaluator.py` - Unified retry logic
- `src/storybench/utils/` (new) - Create APIRetryHandler class
- Provider-specific sections in api_evaluator.py

**Success Criteria:**
- Consistent retry behavior across all API providers
- 80% reduction in evaluation interruptions due to API issues
- Maximum 3 retries with exponential backoff (1s, 2s, 4s)

**Estimated Effort:** 1-2 days

## Phase 2: System Robustness (Week 2)

### 2.1 Evaluation State Management 💾 RELIABILITY
**Issue**: Resume functionality relies on counting responses, may miss partial work
**Impact**: Resume failures, lost evaluation progress, inaccurate continuation

**Tasks:**
- [ ] Implement atomic evaluation checkpoints at prompt completion
- [ ] Add evaluation state validation on resume
- [ ] Store sequence context accumulation state for proper resume
- [ ] Add checkpoint integrity verification
- [ ] Implement rollback for corrupted evaluation states

**Files to modify:**
- `src/storybench/database/services/evaluation_runner.py` - Checkpoint system
- `src/storybench/database/models.py` - Add checkpoint fields
- `src/storybench/database/services/sequence_evaluation_service.py` - State persistence
- CLI resume functionality

**Success Criteria:**
- 100% successful resume from any interruption point
- No duplicate work on resume operations
- Context continuity maintained across resume

**Estimated Effort:** 3-4 days

### 2.2 Configuration Validation & Consolidation ⚙️ MAINTAINABILITY
**Issue**: Model context limits hardcoded in multiple files, configuration scattered
**Impact**: Context limits out of sync, configuration errors, failed evaluations

**Tasks:**
- [ ] Create single source of truth for model context limits
- [ ] Implement runtime validation of model+context combinations
- [ ] Consolidate configuration validation into startup checks
- [ ] Add fail-fast validation before starting long evaluation runs
- [ ] Create configuration schema with Pydantic validation

**Files to modify:**
- `src/storybench/config/` - Consolidated configuration system
- `src/storybench/evaluators/api_evaluator.py` - Remove hardcoded limits
- `src/storybench/models/config.py` - Enhanced validation
- CLI startup validation

**Success Criteria:**
- All model context limits in single configuration file
- Configuration errors caught before evaluation start
- Validation prevents invalid model+context combinations

**Estimated Effort:** 2-3 days

## Phase 3: Open Source Preparation (Week 3)

### 3.1 Security Hardening 🔒 SECURITY
**Issue**: API keys in logs, internal paths in error messages, hardcoded secrets
**Impact**: Security exposure when open sourced, potential credential leaks

**Tasks:**
- [ ] Audit all logging statements for sensitive data exposure
- [ ] Sanitize error messages to remove internal implementation details
- [ ] Create comprehensive .env.example with all required variables
- [ ] Remove any commented-out code with sensitive information
- [ ] Add credential validation without logging actual values
- [ ] Implement secure error message formatting

**Files to modify:**
- All files with logging statements
- Error handling across the codebase
- `.env.example` creation
- `run_directus_evaluations.py` - Remove API key logging

**Success Criteria:**
- Zero API keys or sensitive data in logs
- Error messages safe for external users
- Complete .env.example for new users

**Estimated Effort:** 1-2 days

### 3.2 Code Quality & Documentation 📚 MAINTAINABILITY
**Issue**: Code duplication, long functions, missing architectural documentation
**Impact**: Reduced development velocity, harder maintenance, contributor barriers

**Tasks:**
- [ ] Document evaluation pipeline architecture with diagrams
- [ ] Create architectural decision records (ADRs) for key design choices
- [ ] Refactor duplicate evaluation model definitions
- [ ] Break down functions >50 lines into smaller components
- [ ] Create troubleshooting guide for common evaluation failures
- [ ] Add inline code documentation for complex logic

**Files to modify:**
- `docs/` directory - Architecture documentation
- `src/storybench/database/models.py` - Reduce duplication
- Long functions across evaluators and services
- README updates for contributors

**Success Criteria:**
- Architecture documentation complete
- No functions >50 lines in core evaluation path
- New contributor guide available

**Estimated Effort:** 3-4 days

### 3.3 Testing & Quality Assurance 🧪 RELIABILITY
**Issue**: Unclear test coverage, potential undertesting of complex evaluation logic
**Impact**: Risk of regressions, confidence issues for open source release

**Tasks:**
- [ ] Add integration tests for full evaluation pipelines
- [ ] Implement contract tests for Directus/MongoDB interactions
- [ ] Create performance regression tests
- [ ] Add chaos testing for API failure scenarios
- [ ] Target 80%+ coverage for evaluation core logic
- [ ] Add automated testing for context management edge cases

**Files to modify:**
- `tests/` directory expansion
- CI/CD pipeline enhancements
- Test fixtures for evaluation scenarios

**Success Criteria:**
- 80% test coverage on core evaluation logic
- Integration tests for all major evaluation paths
- Performance benchmarks established

**Estimated Effort:** 4-5 days

## Success Metrics

### Performance Targets
- **25-35% reduction** in total evaluation runtime (from 7-8 hours)
- **20-30% reduction** in database query time
- **80% reduction** in evaluation interruptions due to API issues

### Reliability Targets
- **Zero context-related** evaluation failures
- **100% successful** resume operations from any interruption point
- **Complete 8-hour evaluations** without manual intervention

### Quality Targets
- **Zero API keys or sensitive data** in logs or error messages
- **80% test coverage** on core evaluation logic
- **Complete documentation** for new contributors

## Implementation Notes

### Development Environment
- Use existing venv: `/home/todd/storybench/venv-storybench`
- Run tests after each phase: `python -m pytest tests/`
- Test with realistic evaluation scenarios, not just unit tests

### Risk Mitigation
- **Backup current working system** before major changes
- **Implement changes incrementally** with testing at each step
- **Keep performance monitoring** active during implementation
- **Test resume functionality** thoroughly before deploying

### Open Source Considerations
- **Security audit** before any public release
- **License compliance** check for all dependencies
- **Contributor guidelines** and code of conduct
- **Issue templates** and PR templates for GitHub

---

## Phase Status Tracking

- [ ] **Phase 1 Complete** - Critical fixes deployed
- [ ] **Phase 2 Complete** - System robustness achieved  
- [ ] **Phase 3 Complete** - Open source ready

*Last Updated: June 3, 2025*
