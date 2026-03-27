# claude-session-search

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)](tests/)

**Hybrid BM25 + Semantic search over your entire Claude Code conversation history. Fully offline.**

Claude Code stores every conversation locally but gives you no way to search them. This tool indexes everything — and auto-updates after every response via a Stop Hook.

```
$ sss "cloudflare deployment failed" --hybrid

[HYBRID] 3 results in 0.31s

  [1] 2026-03-24  edge-seo-worker  abc1234
      "wrangler deploy failed — KV key used filename instead of hostname field"
      → read-session abc1234 --last 5

  [2] 2026-03-20  cf-proxy-setup   def5678
      "staging.enabled: true blocked production — fix: set to false before release"
      → read-session def5678 --context

  [3] 2026-03-15  briefadler       ghi9012
      "wrangler 4.72.0 exit 1 on deploy — resolved by upgrading to 4.77.0"
      → read-session ghi9012 --last 3
```

---

## Features

- **Hybrid search** — BM25 (exact, instant) + Semantic (understands meaning) fused via Reciprocal Rank Fusion
- **Multilingual** — Handles German/English mixed content; umlauts normalized, CamelCase split
- **Session fingerprinting** — auto-classifies sessions as deploys, milestones, or by topic
- **Continuation mode** — `sss --continuation "project"` picks up where you left off
- **Conversation reconstruction** — `read-session <id> --last 5` rebuilds exact context to resume work
- **Zero cloud dependency** — ONNX embeddings, everything local, no API calls

---

## vs. Alternatives

| Feature | this tool | [search-sessions](https://github.com/sinzin91/search-sessions) | [cc-conversation-search](https://github.com/akatz-ai/cc-conversation-search) |
|---------|-----------|----------------|----------------------|
| Hybrid BM25 + Semantic | ✅ | ❌ ripgrep only | ✅ semantic only |
| Session fingerprinting | ✅ | ❌ | ❌ |
| Continuation / briefing mode | ✅ | ❌ | ❌ |
| Multilingual (DE/EN) | ✅ | ❌ | ❌ |
| Read full session context | ✅ `read-session` | ❌ | ❌ |
| Auto-index via Stop Hook | ✅ | manual | manual |
| Offline / no API | ✅ | ✅ | ✅ |

---

## Requirements

- Python 3.10+
- [Claude Code](https://claude.ai/code) installed (`~/.claude/` must exist)
- macOS or Linux (Windows WSL untested but should work)

---

## Installation

```bash
git clone https://github.com/florianstangl/claude-session-search
cd claude-session-search
bash install.sh
```

The installer:
1. Installs `fastembed` + `numpy` via `uv` (or `pip` as fallback)
2. Places `sss` in `~/.claude/scripts/`
3. Places `read-session` in `/usr/local/bin/`
4. Wires a Stop Hook in `~/.claude/settings.json` — auto-indexes after every response
5. Builds the initial search index (downloads ~33MB embedding model on first run)

**Add to PATH if needed:**
```bash
echo 'export PATH="$HOME/.claude/scripts:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

**Upgrade:**
```bash
bash install.sh --upgrade
```

**Remove:**
```bash
bash install.sh --uninstall
```

---

## Usage

### Search

```bash
sss "cloudflare worker"                    # BM25 — fast, exact
sss "cloudflare worker" --hybrid           # BM25 + Semantic — best quality
sss "deployment problems" --semantic       # Semantic only — finds related concepts
sss "wrangler deploy release" --any        # OR logic — any term matches
sss "auth" --since 2026-01-01             # Filter by date
sss "auth" --deployed                      # Only sessions where you ran a deploy
sss "feature" --milestone                  # Only sessions with a completed milestone
sss "error" --unique                       # One result per session (deduplicated)
```

### Resume work

```bash
sss --continuation "my-project"   # Where was I in the last 48h?
sss --briefing "my-project"       # Full re-onboarding after a long break
```

### Reconstruct a conversation

```bash
# 1. Find the session
sss "the bug we fixed last week" --hybrid

# 2. Reconstruct context (pick one)
read-session abc12345 --last 5      # Last 5 message pairs — exact wording
read-session abc12345 --context     # Smart summary (~5-8k tokens) — for resuming
read-session abc12345 --full        # Everything, untruncated
```

### Index management

```bash
sss --index              # Incremental update (new sessions only, runs in <2s)
sss --index --force      # Full rebuild
sss --stats              # Index statistics
sss --fingerprint-all    # Classify all sessions (idempotent, safe to re-run)
```

---

## How the Stop Hook works

`install.sh` adds this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "~/.claude/scripts/sss --index",
        "run_in_background": true
      }
    ]
  }
}
```

The `Stop` event fires after every Claude Code response. The incremental indexer runs in the background and typically completes in under 2 seconds without interrupting your workflow.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SSS_DATA_DIR` | `~/.claude` | Base directory for all index files |
| `SSS_SESSIONS_DIR` | `~/.claude/projects` | Where Claude Code stores sessions |
| `SSS_INDEX_DB` | `~/.claude/session-index.db` | SQLite full-text index |
| `SSS_EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model (see below) |

### Embedding model options

| Model | Download | Best for |
|-------|----------|----------|
| `BAAI/bge-small-en-v1.5` | 33 MB | English-heavy sessions (default, fast) |
| `intfloat/multilingual-e5-small` | 117 MB | Mixed German/English (recommended upgrade) |
| `BAAI/bge-m3` | 568 MB | Maximum multilingual quality |

Switch model (rebuilds embeddings, one-time):
```bash
SSS_EMBED_MODEL=intfloat/multilingual-e5-small sss --index --force
```

---

## Index size

| Sessions | Approx. total size |
|----------|--------------------|
| 100 | ~55 MB |
| 500 | ~285 MB |
| 1,000 | ~570 MB |

~0.4 MB per session. No automatic pruning. See [PRIVACY.md](PRIVACY.md) for how to manage index size and what the index contains.

---

## Privacy

Everything stays on your machine. The index contains your full conversation history. See [PRIVACY.md](PRIVACY.md) — especially the section on what to never commit to Git.

---

## Author

Built by [Florian Stangl](https://github.com/florianstangl) — originally developed as part of a long-running Claude Code workflow spanning 500+ sessions.

---

## License

MIT — see [LICENSE](LICENSE).
