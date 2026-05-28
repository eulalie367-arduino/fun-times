# Aider Research - Autonomous Research & Integration Skill

Autonomously research current information, best practices, and latest technologies, then integrate findings directly into projects.

## Overview

```
Research Query
    ↓
Web Search + Doc Fetch (Parallel)
    ↓
Analyze & Synthesize
    ↓
Create Research Report
    ↓
Suggest Implementation
    ↓
Auto-integrate with aider
    ↓
Project Updated
```

## Features

- 🔍 **Parallel Research**: Multiple sources searched simultaneously
- 📚 **Auto-fetch**: Documentation, GitHub, StackOverflow, official sources
- 🤖 **Intelligent Synthesis**: AI analysis of findings
- 📝 **Research Reports**: Comprehensive documentation of findings
- 💡 **Smart Suggestions**: Implementation recommendations
- 🔧 **Auto-integration**: Use aider to integrate findings into code
- 📊 **Source Tracking**: Citations and references included
- ⏰ **Real-time Data**: Latest versions, frameworks, best practices

## Usage

### Basic Research

```bash
/aider-research "What's the latest in vector databases for RAG?"
```

### Research + Integration

```bash
/aider-research "Update RAG pipeline with latest ChromaDB features"
```

### Research Specific Topic

```bash
/aider-research --topic "Claude API" --depth full --project .
```

### Save Research Report

```bash
/aider-research "LLM orchestration frameworks" --save-report
```

## How It Works

### Phase 1: Research Planning
- Parse research query
- Identify key topics
- Plan search strategy
- Determine authoritative sources

### Phase 2: Parallel Research Gathering
Search multiple sources simultaneously:
- Web search (Google, Bing)
- GitHub repositories
- Official documentation
- Stack Overflow
- Academic papers
- GitHub discussions
- YouTube tutorials

### Phase 3: Content Analysis
- Extract key information
- Identify version numbers
- Find best practices
- Detect breaking changes
- Summarize findings

### Phase 4: Research Report Generation
Create comprehensive report with:
- Summary of findings
- Latest versions/releases
- Best practices
- Code examples
- Performance metrics
- Comparison tables
- Source citations

### Phase 5: Implementation Suggestions
Recommend:
- Libraries/frameworks
- Code patterns
- Configuration options
- Performance optimizations
- Security considerations

### Phase 6: Auto-Integration with Aider
Use aider to:
- Update dependencies
- Implement best practices
- Add new features
- Refactor code
- Add documentation
- Create examples

### Phase 7: Commit & Document
- Create commits with research findings
- Add research notes to project
- Update README/docs
- Reference sources

## Usage Examples

### Example 1: Research Latest Vector DB

```bash
/aider-research "Latest vector databases for production RAG systems"
```

**Output:**
```
🔍 AIDER RESEARCH: Vector Databases for RAG

Search Strategy: Parallel multi-source
Sources: 12 (GitHub, Docs, Papers, Discussions)
Time: 45 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 KEY FINDINGS

1. ChromaDB v0.4.x (Latest: 0.4.24)
   ✅ SQLite storage, Python-first
   ✅ In-memory + persistent modes
   ✅ 10x faster with new chunking

2. Pinecone (Fully Managed)
   ✅ $0.25/1M vectors
   ✅ Serverless architecture
   ✅ Built-in metadata filtering

3. Milvus 2.4
   ✅ Distributed architecture
   ✅ GPU acceleration
   ✅ Kubernetes-native

4. Weaviate 1.25
   ✅ Modular architecture
   ✅ GraphQL API
   ✅ Built-in LLM modules

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 PERFORMANCE COMPARISON

| DB | Latency | Scale | Cost |
|----|---------|-------|------|
| ChromaDB | 50-200ms | Millions | Free |
| Pinecone | 100-500ms | Billions | $$ |
| Milvus | 50-100ms | Trillions | Free |
| Weaviate | 100-300ms | Billions | $ |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RECOMMENDATIONS

For RAG systems:
1. Small-Medium (< 1M vectors): ChromaDB ✅
2. Large-Scale (> 1M vectors): Pinecone or Milvus
3. Self-Hosted: Milvus + Kubernetes
4. Managed: Pinecone (easiest)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 RESOURCES

- ChromaDB Docs: https://docs.trychroma.com
- Pinecone Guide: https://docs.pinecone.io
- Milvus Tutorials: https://milvus.io/docs
- Comparison: Vector DB Benchmarks 2024

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to integrate findings? Run:
/aider-research --integrate "Add Milvus vector store option"
```

### Example 2: Research + Auto-integrate

```bash
/aider-research "Update to latest Claude API with streaming support"
```

**Automatically:**
1. Fetches Claude API docs (latest version)
2. Finds streaming examples
3. Researches best practices
4. Generates research report
5. Uses aider to update code with streaming
6. Tests changes
7. Creates commit with research notes

### Example 3: Research Best Practices

```bash
/aider-research --topic "RAG system best practices 2024" --depth full --save-report
```

**Outputs:**
- Comprehensive research report (PDF)
- Best practices checklist
- Implementation examples
- Code snippets
- Configuration recommendations

### Example 4: Compare Frameworks

```bash
/aider-research "Compare vector DB frameworks: ChromaDB vs Milvus vs Weaviate"
```

**Generates:**
- Feature comparison matrix
- Performance benchmarks
- Cost analysis
- Use case recommendations
- Migration guide

## Configuration

Create `.aider-research.config`:

```yaml
# Research depth
research_depth: full      # quick, medium, full

# Source preferences
sources:
  web_search: true
  github: true
  documentation: true
  stackoverflow: true
  academic: false
  youtube: false

# Output preferences
save_report: true
report_format: markdown   # markdown, pdf, html
citation_style: mla       # mla, apa, chicago

# Integration preferences
auto_integrate: false
integration_depth: medium # light, medium, full

# Parallel processing
parallel_sources: 6
timeout_per_source: 30s

# Research history
cache_results: true
cache_duration: 7d        # Cache for 7 days
```

## Advanced Features

### 1. Continuous Research Mode

```bash
/aider-research --watch "Claude API updates" --interval daily
```

Automatically monitors topic and alerts on changes.

### 2. Multi-Topic Research

```bash
/aider-research \
  --topic "Vector databases" \
  --topic "LLM orchestration" \
  --topic "RAG patterns" \
  --combine-findings
```

Research multiple topics and create unified report.

### 3. Research + Implementation

```bash
/aider-research "Add Langchain to project" \
  --auto-implement \
  --create-examples \
  --add-tests
```

Full implementation with examples and tests.

### 4. Competitive Analysis

```bash
/aider-research "Compare RAG frameworks" \
  --create-comparison-table \
  --performance-benchmarks \
  --cost-analysis
```

Detailed competitive analysis.

## Output Formats

### Quick Output (5 min)
- Key findings summary
- Top 3 resources
- One recommendation

### Medium Output (15 min)
- Comprehensive findings
- Feature comparison
- Best practices
- Code examples
- Resource links

### Full Output (30-45 min)
- Complete research report
- Benchmarks and metrics
- Implementation guide
- Use case analysis
- Migration path
- Cost comparison

## Integration Examples

### With aider-pipeline

```bash
TASK=$(aider-pipeline create feature "Research and upgrade RAG")
aider-pipeline add-step $TASK "Research latest RAG frameworks" "research" \
  --topic "RAG" --depth full
aider-pipeline add-step $TASK "Integrate findings" "aider-research-integrate"
aider-pipeline run $TASK
```

### With aider-scientist

```bash
# Research issue
/aider-research "Why is our RAG latency high?" --analyze-performance

# Then fix it
/aider-scientist "Optimize RAG based on research findings"
```

## Architecture

```
Research Query
    ↓ (Parallel 6 workers)
├─ Web Search
├─ GitHub API
├─ Doc Fetch
├─ StackOverflow
├─ Benchmarks
└─ Best Practices DB
    ↓
Content Analysis (AI)
    ↓
Report Generation
    ↓
Suggestion Engine
    ↓
Integration Prep
    ↓ (aider)
Code Changes
    ↓
Test & Validate
```

## Performance

| Mode | Time | Sources | Output |
|------|------|---------|--------|
| Quick | 5 min | 3-4 | Summary |
| Medium | 15 min | 8-10 | Report |
| Full | 30-45 min | 15+ | Complete |

## Requirements

- **Bash 4.0+**
- **Git 2.30+**
- **curl** (web fetching)
- **aider** (integration)
- **Web access** (research)

## Status

✅ **Production Ready**
- Full research pipeline
- Parallel source fetching
- Intelligent analysis
- Auto-integration
- Report generation

## Related Skills

- `/aider-plan` - Plan implementation based on research
- `/aider-scientist` - Fix issues discovered in research
- `/aider-pipeline` - Execute research-based implementations
- `/gemini-enhance-pr` - Review research findings PR

---

**Always current. Always research-backed.** 🔬
