# Aider-Gemini Parallel PR Enhancement Skill

Autonomous skill that runs Gemini reviews on PRs in parallel, extracts action items, and uses aider to apply fixes automatically.

## Overview

```
PR Input → Gemini Review (Parallel) → Parse Outcomes
                                           ↓
                                    Extract Actions
                                           ↓
                                    Aider Fixes (Parallel)
                                           ↓
                                    Commit & Push
                                           ↓
                                    Create Follow-up PRs
```

## Features

- ⚡ **Parallel Reviews**: Multiple PRs reviewed simultaneously
- 🤖 **Gemini Analysis**: AI-powered code review and suggestions
- 🔧 **Aider Integration**: Automatic code fixes with aider
- 📝 **Parallel Fixes**: Apply multiple fixes simultaneously
- 📊 **Action Extraction**: Parse Gemini output for actionable items
- 🔄 **Parallel Commits**: Create commits in parallel

## Usage

### Basic Usage

```bash
/gemini-enhance-pr 1 2

# Reviews PR #1 and #2 in parallel
# Applies Gemini suggestions using aider
# Creates follow-up PRs for enhancements
```

### With Options

```bash
/gemini-enhance-pr 1 2 --auto-merge
# Auto-merge enhancement PRs if all fixes pass

/gemini-enhance-pr 1 2 --max-parallel 4
# Limit parallel jobs to 4

/gemini-enhance-pr 1 2 --skip-merge-requests
# Apply fixes but don't create follow-up PRs
```

## How It Works

### Phase 1: Parallel Review Extraction

For each PR:
1. Get PR details with `gh pr view <NUM>`
2. Extract code/body
3. Send to Gemini for review
4. Parse Gemini response for:
   - Issues (blocking)
   - Suggestions (enhancements)
   - Verdict (approve/reject)

### Phase 2: Action Extraction

Parse Gemini output and create action list:
```json
{
  "pr": 1,
  "verdict": "APPROVED_WITH_FIXES",
  "fixes": [
    {
      "type": "add_section",
      "file": "RAG_PIPELINE_RELEASE.md",
      "section": "Performance Metrics",
      "content": "..."
    },
    {
      "type": "create_file",
      "file": "CHANGELOG.md",
      "content": "..."
    }
  ],
  "enhancements": [
    {
      "type": "code_feature",
      "title": "Add streaming support",
      "description": "Claude API supports streaming...",
      "priority": "medium"
    }
  ]
}
```

### Phase 3: Parallel Aider Fixes

For each fix action:
1. Use aider to modify files
2. Validate changes compile
3. Create commit in parallel
4. Track completion

Example:
```bash
# Parallel job pool (default 4 workers)
aider "Add Performance Metrics section to RAG_PIPELINE_RELEASE.md" &
aider "Create CHANGELOG.md with v1.0.0 entry" &
aider "Add API reference section to documentation" &

wait  # Wait for all to complete
```

### Phase 4: Commit & Push

```bash
# All changes committed to current branch
# Single push with all fixes
git push origin <branch>

# Comment on original PR
gh pr comment <NUM> --body "Applied Gemini review suggestions:
- ✅ Added Performance Metrics section
- ✅ Created CHANGELOG.md
- ✅ Updated API documentation"
```

### Phase 5: Create Follow-up PRs

For enhancement suggestions:
```bash
# Create new branch for enhancements
git checkout -b enhance/streaming-support

# Use aider for enhancement
aider "Add streaming response support to Claude API client"

# Create PR
gh pr create \
  --base main \
  --title "Enhancement: Add streaming support for Claude API" \
  --body "Based on Gemini review suggestion..."
```

## Configuration

Create `.gemini-enhance-pr.config` in project root:

```yaml
# Parallel processing
parallel_jobs: 4
max_pr_batch: 10

# Aider configuration
aider_model: claude-3-5-sonnet
max_file_size: 10000  # Lines

# Review depth
review_depth: full    # quick, medium, full

# Auto-actions
auto_fix: true
auto_merge_enhancements: false
create_follow_up_prs: true

# Notification
slack_webhook: null
comment_on_pr: true
```

## Output

### Console Output

```
🚀 Gemini-Aider Parallel Enhancement

PR Batch: #1, #2

Phase 1: Parallel Gemini Reviews (2 PRs)
  [1/2] Reviewing PR #1: Release v1.0...
  [2/2] Reviewing PR #2: Phase 2 Step 3...
  ✅ Both reviews complete (12s)

Phase 2: Action Extraction
  PR #1: 3 fixes, 2 enhancements
  PR #2: 2 fixes, 3 enhancements
  ✅ Actions extracted (2s)

Phase 3: Parallel Aider Fixes (4 workers)
  [1/5] Adding Performance Metrics section...
  [2/5] Creating CHANGELOG.md...
  [3/5] Adding API reference...
  [4/5] Adding multi-collection test...
  [5/5] Updating deployment docs...
  ✅ All fixes applied (45s)

Phase 4: Commit & Push
  ✅ Committed: "Apply Gemini review suggestions"
  ✅ Pushed to origin/release/rag-pipeline-v1

Phase 5: Create Follow-up PRs
  ✅ PR #3: Enhancement - Streaming support
  ✅ PR #4: Enhancement - Query validation

✅ COMPLETE
  - 5 fixes applied
  - 5 enhancements proposed
  - 2 follow-up PRs created
  - Total time: 90 seconds
```

## Parallel Architecture

### Worker Pool

```
┌─────────────────────────────────────────┐
│  Gemini Review Phase (2 workers)        │
│  ├─ Worker 1: Review PR #1              │
│  ├─ Worker 2: Review PR #2              │
│  └─ Synchronize results                 │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Aider Fixes Phase (4 workers)          │
│  ├─ Worker 1: Fix type:add_section      │
│  ├─ Worker 2: Fix type:create_file      │
│  ├─ Worker 3: Fix type:code_addition    │
│  ├─ Worker 4: Fix type:documentation    │
│  └─ Synchronize all changes             │
└─────────────────────────────────────────┘
```

## Error Handling

### If Gemini Review Fails
- Fallback to Claude review
- Log error with PR number
- Continue with other PRs

### If Aider Fix Fails
- Revert changes to that file
- Log error with fix details
- Continue with other fixes
- Create issue for manual review

### If PR Comment Fails
- Log warning
- Continue with next PR
- Can retry manually

## Performance

- **Gemini Review**: 5-10s per PR
- **Action Extraction**: 1-2s per PR
- **Aider Fixes**: 10-20s per fix (parallel)
- **Commit & Push**: 5-10s
- **Create PRs**: 5s per PR
- **Total (2 PRs, 5 fixes)**: ~60-90 seconds

vs Sequential: ~300-400 seconds (70% faster)

## Integration Examples

### With GitHub Actions

```yaml
- name: Gemini PR Enhancement
  run: |
    /gemini-enhance-pr $(gh pr list --base main -q)
```

### With aider-pipeline

```bash
# In pipeline config
pr_review_enabled: true
pr_review_type: gemini-enhance
pr_review_parallel: 4
```

## Advanced: Custom Action Handlers

Define custom handlers for specific fix types:

```bash
# In .gemini-enhance-pr.config
handlers:
  type:add_section:
    template: "docs_section_template.md"
    validator: "markdown_lint"

  type:create_file:
    template: "file_template.{ext}"
    permissions: "0644"
```

## Requirements

- **Bash 4.0+**
- **GitHub CLI (gh)** with auth
- **aider** installed
- **Gemini API access** (via CLI or curl)
- **Git 2.30+**

## Status

✅ **Production Ready**

## Related Skills

- `/aider-pr` - Perfect PR creation
- `/gemini-review-pr` - Single PR review
- `/aider-pipeline` - Multi-step workflows

---

**Autonomous Gemini + Aider parallel enhancement for perfect PRs** ⚡
