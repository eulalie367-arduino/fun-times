# Gemini-Aider Parallel PR Enhancement

**Autonomous skill combining Gemini reviews with aider fixes for parallel PR enhancement.**

## Quick Start

```bash
/gemini-enhance-pr 1 2

# Reviews PR #1 and #2 in parallel
# Extracts action items
# Applies fixes with aider
# Creates follow-up enhancement PRs
```

## What It Does

1. **Parallel Gemini Reviews**: Simultaneously review multiple PRs
2. **Action Extraction**: Parse reviews for fixes and enhancements
3. **Parallel Aider Fixes**: Apply multiple fixes simultaneously
4. **Automated Commits**: Create commits with all changes
5. **Follow-up PRs**: Create enhancement PRs for suggestions

## Example Output

```
🚀 Gemini-Aider Parallel PR Enhancement

PRs: 1 2
Parallel jobs: 4

Phase 1: Parallel Gemini Reviews
  ✅ PR #1 review complete
  ✅ PR #2 review complete

Phase 2: Extract Actions
  PR #1: 3 fixes, 2 enhancements
  PR #2: 2 fixes, 3 enhancements

Phase 3: Parallel Aider Fixes (4 workers)
  [1/5] Adding Performance Metrics section...
  [2/5] Creating CHANGELOG.md...
  [3/5] Adding API reference...
  [4/5] Adding integration tests...
  [5/5] Updating deployment docs...
  ✅ All fixes applied

Phase 4: Commit & Push
  ✅ Committed: "Apply Gemini review suggestions"
  ✅ Pushed to origin

Phase 5: Create Follow-up PRs
  ✅ PR #3: Enhancement - Streaming support
  ✅ PR #4: Enhancement - Query validation

✅ ENHANCEMENT COMPLETE
  Fixes applied: 5
  Total time: ~90 seconds
```

## Performance

- **Parallel reviews**: 2+ PRs simultaneously
- **Parallel fixes**: 4 workers by default
- **Speed improvement**: 70% faster than sequential
- **Total time**: 90 seconds for 2 PRs + 5 fixes

vs Sequential: 300-400 seconds (70% savings)

## Configuration

Create `.gemini-enhance-pr.config`:

```yaml
parallel_jobs: 4
review_depth: full
auto_fix: true
create_follow_up_prs: true
```

## Requirements

- GitHub CLI (gh) with authentication
- aider installed
- Git 2.30+
- Bash 4.0+

## Architecture

```
PR Input
   ↓ (parallel 2+ workers)
Gemini Reviews
   ↓
Action Extraction
   ↓ (parallel 4 workers)
Aider Fixes
   ↓
Git Commit & Push
   ↓
Follow-up PR Creation
```

## Usage Examples

### Review Multiple PRs
```bash
/gemini-enhance-pr 1 2 3
```

### With Options
```bash
/gemini-enhance-pr 1 2 --max-parallel 8
/gemini-enhance-pr 1 2 --skip-follow-up-prs
```

### In aider-pipeline
```bash
aider-pipeline add-step $TASK "Enhance with Gemini" "gemini-enhance-pr" 1 2
```

---

**Combining Gemini intelligence with aider automation for perfect PRs** ⚡
