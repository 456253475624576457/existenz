# ExistenZ

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)](tests/)

**Claude Code doesn't remember. ExistenZ does.**

Every decision you made. Every bug you fixed. Every conversation you had. All of it — searchable, reconstructable, permanent. ExistenZ is persistent memory for Claude Code.

```
$ existenz "why did we change the deployment config" --hybrid

[HYBRID] 3 results in 0.31s

  [1] 2026-03-24  edge-seo-worker  abc1234
      "KV key used filename instead of hostname — caused silent deploy failures"
      → read-session abc1234 --last 5

  [2] 2026-03-20  cf-proxy-setup   def5678
      "staging.enabled: true blocked production — only discovered after 3 days"
      → read-session def5678 --context

  [3] 2026-03-15  infra-review     ghi9012
      "wrangler 4.72.0 had a known deploy regression — pinned to 4.77.0"
      → read-session ghi9012 --last 3
```

---

## The problem

Claude Code is stateless by design. Every session starts fresh. You explain context you've explained before. You rediscover bugs you've already fixed. You lose decisions the moment the conversation ends.

After 500 sessions, you've accumulated thousands of hours of work — and none of it is searchable.

**ExistenZ changes that.**

---

## How it works

ExistenZ hooks into Claude Code's `Stop` event — after every single response, it incrementally indexes the session. Hybrid BM25 + Semantic search across your full history. Everything offline, everything local.

No cloud. No API calls. No data leaving your machine.

---

## Features

- **Hybrid search** — BM25 (exact, instant) + Semantic (understands meaning) fused via Reciprocal Rank Fusion
- **Multilingual** — German/English mixed content, umlauts normalized, CamelCase split
- **Session fingerprinting** — auto-classifies sessions as deploys, milestones, or by topic
- **Continuation mode** — `existenz --continuation "project"` picks up exactly where you left off
- **Conversation reconstruction** — `read-session <id> --last 5` rebuilds exact context to resume work
- **Zero cloud dependency** — ONNX embeddings, everything local, no API calls

---

## vs. Alternatives

| Feature | ExistenZ | [search-sessions](https://github.com/sinzin91/search-sessions) | [cc-conversation-search](https://github.com/akatz-ai/cc-conversation-search) |
|---------|----------|----------------|----------------------|
| Hybrid BM25 + Semantic | ✅ | ❌ ripgrep only | ✅ semantic only |
| Session fingerprinting | ✅ | ❌ | ❌ |
| Continuation / briefing mode | ✅ | ❌ | ❌ |
| Multilingual (DE/EN) | ✅ | ❌ | ❌ |
| Full conversation reconstruction | ✅ | ❌ | ❌ |
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
git clone https://github.com/456253475624576457/existenz
cd existenz
bash install.sh
```

The installer:
1. Installs `fastembed` + `numpy` via `uv` (or `pip` as fallback)
2. Places `existenz` in `~/.claude/scripts/`
3. Places `read-session` in `/usr/local/bin/`
4. Wires a Stop Hook in `~/.claude/settings.json` — auto-indexes after every response
5. Builds the initial search index (downloads ~33MB embedding model on first run)

**Add to PATH if needed:**
```bash
echo 'export PATH="$HOME/.claude/scripts:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

---

## Usage

### Search

```bash
existenz "cloudflare worker"                   # BM25 — fast, exact
existenz "cloudflare worker" --hybrid          # BM25 + Semantic — best quality
existenz "deployment problems" --semantic      # Semantic — finds related concepts
existenz "wrangler deploy release" --any       # OR logic — any term matches
existenz "auth" --since 2026-01-01            # Filter by date
existenz "auth" --deployed                     # Only sessions where you ran a deploy
existenz "feature" --milestone                 # Only completed milestone sessions
existenz "error" --unique                      # One result per session
```

### Resume work

```bash
existenz --continuation "my-project"   # Where was I in the last 48h?
existenz --briefing "my-project"       # Full re-onboarding after a long break
```

### Reconstruct a conversation

```bash
# 1. Find the session
existenz "the bug we fixed last week" --hybrid

# 2. Rebuild context
read-session abc12345 --last 5      # Last 5 message pairs — exact wording
read-session abc12345 --context     # Smart summary — optimized for resuming
read-session abc12345 --full        # Everything, untruncated
```

### Index management

```bash
existenz --index           # Incremental update (runs in <2s)
existenz --index --force   # Full rebuild
existenz --stats           # Index statistics
existenz --fingerprint-all # Classify all sessions
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
        "command": "~/.claude/scripts/existenz --index",
        "run_in_background": true
      }
    ]
  }
}
```

The `Stop` event fires after every Claude Code response. ExistenZ indexes incrementally in the background — typically under 2 seconds, never interrupting your flow.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SSS_DATA_DIR` | `~/.claude` | Base directory for all index files |
| `SSS_SESSIONS_DIR` | `~/.claude/projects` | Where Claude Code stores sessions |
| `SSS_INDEX_DB` | `~/.claude/session-index.db` | SQLite full-text index |
| `SSS_EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model |

### Embedding model options

| Model | Download | Best for |
|-------|----------|----------|
| `BAAI/bge-small-en-v1.5` | 33 MB | English-heavy sessions (default) |
| `intfloat/multilingual-e5-small` | 117 MB | Mixed German/English (recommended) |
| `BAAI/bge-m3` | 568 MB | Maximum multilingual quality |

```bash
SSS_EMBED_MODEL=intfloat/multilingual-e5-small existenz --index --force
```

---

## Index size

| Sessions | Approx. size |
|----------|--------------|
| 100 | ~55 MB |
| 500 | ~285 MB |
| 1,000 | ~570 MB |

~0.4 MB per session. See [PRIVACY.md](PRIVACY.md) for index management and what to never commit to Git.

---

## Privacy

Everything stays on your machine. See [PRIVACY.md](PRIVACY.md).

---

## Built by

[Florian Stangl](https://github.com/456253475624576457) — built and battle-tested across 500+ Claude Code sessions.

---

## License

MIT — see [LICENSE](LICENSE).
