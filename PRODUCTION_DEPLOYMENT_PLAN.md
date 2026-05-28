# Phase 4 Production Deployment Plan
**Status:** INITIATED
**Date:** 2026-05-28

## Deployment Timeline

### Week 1: Phase 4A (LEAN Optimization)
**Target:** Reduce memory footprint to <1.4GB, latency p95 <900ms

**Monday-Tuesday: Canary Deploy (5% traffic)**
- Deploy to 1 canary instance
- Monitor memory, latency, error rates
- Success criteria: memory <1.5GB, latency increase <5%

**Wednesday-Thursday: Rolling Deploy (25% traffic)**
- Deploy to additional 4 instances
- Validate cross-instance memory behavior
- Check cache coherency

**Friday: Full Deploy (100% traffic)**
- Roll out to all production instances
- Monitor continuous metrics
- Maintain rollback readiness

**Monitoring:**
```
Memory: baseline (2.1GB) → target (1.4GB) = 33% reduction
Latency P95: baseline (850ms) → target (<900ms)
Cache Hit Rate: target >75%
Quantization Accuracy Loss: <1% error
```

---

### Week 2: Phase 4B (SEARCHABLE System)
**Target:** <100ms search latency, scale to 1M+ documents

**Monday-Tuesday: Canary Deploy**
- Deploy search indices to parallel infrastructure
- Benchmark BM25 + faceted search
- Validate index compression

**Wednesday-Thursday: Rolling Deploy (25% traffic)**
- Migrate search queries gradually
- Monitor query parsing overhead
- Track ranking model performance

**Friday: Full Deploy (100% traffic)**
- Complete search system takeover
- Archive old search infrastructure
- Monitor query diversity and coverage

**Monitoring:**
```
Search Latency P95: target <100ms
Query Parsing: target <5ms
Index Size: baseline 800MB → target <600MB (compression)
Facet Performance: <20ms per facet
Autocomplete: <50ms suggestions
```

---

### Week 3: Phase 4C (CORRELATION Engine)
**Target:** Entity accuracy >95%, KG queries <100ms

**Monday-Tuesday: Canary Deploy**
- Deploy NER + entity linker to sample documents
- Validate entity extraction quality
- Check knowledge graph construction

**Wednesday-Thursday: Rolling Deploy (25% traffic)**
- Build knowledge graph on larger dataset
- Validate relationship extraction
- Test graph traversal performance

**Friday: Full Deploy (100% traffic)**
- Activate correlation features in discovery pipeline
- Enable timeline building
- Activate co-occurrence analysis

**Monitoring:**
```
Entity Extraction Accuracy: target >95%
Entity Linking F1: target >90%
KG Query Latency: target <100ms
Timeline Build Time: target <500ms per query
Correlation Significance: PMI threshold = 10
```

---

## Rollback Plan

If any phase fails deployment metrics:

1. **Canary Phase (Day 1-2):**
   - Blue-Green switch back to previous version
   - Zero-downtime cutover
   - Full data consistency check

2. **Rolling Phase (Day 3-4):**
   - Gradual drain of affected instances
   - Drain timeout: 60 seconds
   - Connection limit: graceful degradation

3. **Full Phase (Day 5):**
   - Database snapshot restoration if needed
   - Cache invalidation and rebuild
   - Performance baseline re-validation

## Deployment Configuration

### Phase 4A Deployment (`deploy/phase4a-config.yml`)
```yaml
deployment:
  canary_percent: 5
  canary_duration_hours: 48
  rolling_percent: 25
  rolling_duration_hours: 48

modules:
  - memory_profiler
  - quantizer
  - cache_optimizer
  - batch_processor
  - index_compressor

metrics:
  memory_threshold: 1.5GB
  latency_threshold_p95: 900ms
  error_rate_threshold: 0.1%
```

### Phase 4B Deployment (`deploy/phase4b-config.yml`)
```yaml
deployment:
  parallel_indexing: true
  batch_size: 1000
  index_threads: 8

modules:
  - full_text_index
  - faceted_search
  - rank_model
  - query_parser
  - suggestion_engine
  - analytics

metrics:
  search_latency_p95: 100ms
  index_compression_ratio: 0.75
  query_parsing_latency: 5ms
```

### Phase 4C Deployment (`deploy/phase4c-config.yml`)
```yaml
deployment:
  ner_batch_size: 500
  kg_build_threads: 4
  timeline_window: 3600s

modules:
  - ner_model
  - entity_linker
  - relationship_extractor
  - knowledge_graph
  - correlation_engine
  - timeline_builder

metrics:
  entity_accuracy: 0.95
  entity_linking_f1: 0.90
  kg_query_latency: 100ms
```

## Health Checks

```python
# Phase 4A Health Check
def check_phase4a_health():
    checks = {
        'memory_usage': get_memory_usage() < 1.5GB,
        'cache_hit_rate': get_cache_stats()['hit_rate'] > 0.75,
        'quantization_accuracy': test_quantization_error() < 0.01,
        'latency_p95': get_latency_percentile(95) < 900,
    }
    return all(checks.values())

# Phase 4B Health Check
def check_phase4b_health():
    checks = {
        'search_latency': get_search_latency_p95() < 100,
        'index_compression': get_compression_ratio() > 0.75,
        'query_parsing': get_query_parse_time() < 5,
        'facet_performance': get_facet_time() < 20,
    }
    return all(checks.values())

# Phase 4C Health Check
def check_phase4c_health():
    checks = {
        'entity_accuracy': get_entity_accuracy() > 0.95,
        'entity_linking_f1': get_entity_linking_f1() > 0.90,
        'kg_query_latency': get_kg_query_time() < 100,
        'timeline_build_time': get_timeline_build_time() < 500,
    }
    return all(checks.values())
```

## Success Criteria

### Phase 4A Success
- ✅ Memory reduction: 2.1GB → <1.4GB (>33% improvement)
- ✅ Latency stable: p95 <900ms
- ✅ Cache hit rate: >75%
- ✅ No error rate increase
- ✅ Quantization: <1% accuracy loss

### Phase 4B Success
- ✅ Search latency: p95 <100ms
- ✅ Index compression: >25% reduction
- ✅ Faceted search: <20ms per facet
- ✅ Autocomplete: <50ms response time
- ✅ Scale to 1M+ documents

### Phase 4C Success
- ✅ Entity extraction accuracy: >95%
- ✅ Entity linking F1: >90%
- ✅ Knowledge graph queries: <100ms
- ✅ Timeline building: <500ms per query
- ✅ No external service timeouts

## Post-Deployment

After full Phase 4 deployment:

1. **Week 4: Optimization Phase**
   - Fine-tune weights and thresholds
   - Gather user feedback
   - Analyze performance data
   - Document learnings

2. **Week 5: Enhancement Phase**
   - Implement Phase 5 features:
     - GPU acceleration for quantization
     - Neo4j knowledge graph backend
     - Learning-to-rank optimization
     - Semantic entity linking improvements

3. **Ongoing: Monitoring**
   - Real-time metrics dashboard
   - Weekly performance reports
   - Monthly optimization reviews
   - Quarterly architecture assessments

---

**Next Action:** Begin Phase 4A canary deployment (Monday)
