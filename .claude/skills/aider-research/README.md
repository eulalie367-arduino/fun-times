# Aider Research - Autonomous Research & Integration

**Get up-to-date information, research material, and auto-integrate findings into your project.**

## Quick Start

```bash
/aider-research "What's the latest in vector databases?"
```

Returns comprehensive research with:
- Latest versions and releases
- Best practices
- Performance comparisons
- Code examples
- Resource links

## Key Features

⚡ **Parallel Research**: 6 sources searched simultaneously
📚 **Auto-fetch**: Docs, GitHub, StackOverflow, papers
🤖 **Smart Analysis**: AI synthesis of findings
📝 **Reports**: Comprehensive documentation
💡 **Suggestions**: Implementation recommendations
🔧 **Auto-integration**: Code updates via aider

## Usage Examples

### 1. Simple Research

```bash
/aider-research "Latest Claude API features"
```

### 2. Research + Integration

```bash
/aider-research "Update project to use streaming Claude API"
```

### 3. Comparison Research

```bash
/aider-research "Compare vector databases for RAG"
```

### 4. Topic Deep Dive

```bash
/aider-research --topic "RAG patterns" --depth full --save-report
```

## Research Phases

1. **Planning**: Identify key topics and search strategy
2. **Gathering**: Parallel multi-source research (6 workers)
3. **Analysis**: Extract key information and findings
4. **Report**: Generate comprehensive research document
5. **Suggestions**: Recommend implementations
6. **Integration**: Use aider to update code
7. **Commit**: Document findings in git

## Output Example

```
🔍 AIDER RESEARCH: Vector Databases

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 KEY FINDINGS

ChromaDB v0.4.24
  ✅ Latest: 10x faster chunking
  ✅ 2 persistence modes
  ✅ Production-ready

Pinecone
  ✅ Managed service
  ✅ $0.25/1M vectors
  ✅ Supports 1B+ vectors

Milvus 2.4
  ✅ GPU acceleration
  ✅ Distributed system
  ✅ Kubernetes-native

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 RECOMMENDATION

For RAG: ChromaDB (free, fast) or Pinecone (scale)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 SOURCES

- ChromaDB Docs (official)
- Pinecone Benchmarks
- GitHub trending
- Stack Overflow discussions
```

## Configuration

Create `.aider-research.config`:

```yaml
research_depth: full
sources:
  web_search: true
  github: true
  documentation: true
parallel_sources: 6
save_report: true
auto_integrate: false
```

## Modes

- **Quick**: 5 minutes, 3-4 sources, summary
- **Medium**: 15 minutes, 8-10 sources, report
- **Full**: 30-45 minutes, 15+ sources, complete

## Integration

### With aider-pipeline

```bash
aider-pipeline add-step $TASK "Research topic" "aider-research" \
  --topic "Vector databases" --depth full
```

### With aider-scientist

```bash
# Research why tests are slow
/aider-research "Performance optimization for RAG systems"

# Then fix based on findings
/aider-scientist "Optimize based on research"
```

## Requirements

- Bash 4.0+
- Git 2.30+
- curl (web fetching)
- aider (integration)
- Web access

## Tips

- Use `--save-report` to create research document
- Use `--depth full` for comprehensive analysis
- Use `--topic` for focused research
- Use `--auto-integrate` for code updates

---

**Always research-backed. Always current.** 🔬
