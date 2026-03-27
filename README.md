<div align="center">

# ExistenZ

### Claude Code doesn't remember. ExistenZ does.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-15%20passed-22c55e?style=flat-square)](tests/)
[![Battle-tested](https://img.shields.io/badge/battle--tested-500%2B%20sessions-8b5cf6?style=flat-square)](#)
[![Offline](https://img.shields.io/badge/100%25%20offline-no%20API%20calls-0ea5e9?style=flat-square)](#)

</div>

---

## The problem

Claude Code is stateless. Every session starts fresh — by design.

This is one of the most discussed frustrations in the Claude Code community, and it affects every kind of work: code, writing, research, strategy, client projects, SEO, content. You build up knowledge across hundreds of sessions. You make decisions, develop approaches, reach conclusions. Then the session ends — and the next time you open Claude Code, all of that is gone.

The knowledge still exists. It lives in session files on your disk. But there's no way to get back to it.

So you re-explain context you've already explained. You re-discover things you already figured out. You start conversations that should take 5 minutes from scratch because you can't find the thread.

**After 100 sessions, this is annoying. After 500 sessions, it's a serious productivity problem.**

The existing tools help at the margins — basic keyword search, or semantic search, each on its own. But none of them offer the full picture: no hybrid search that combines both, no session fingerprinting, no continuation mode, no conversation reconstruction.

ExistenZ is the version that actually solves it.

---

## What ExistenZ does

ExistenZ runs silently in the background. After every single Claude Code response, a hook automatically indexes the session — incrementally, in under two seconds, without interrupting anything.

The result is a searchable archive of your entire Claude Code history. Hybrid search combines exact text matching with semantic understanding, so you find what you're looking for even when you don't remember the precise words. Session fingerprinting classifies every session by type and topic. And when you find what you need, you can reconstruct the full conversation context and paste it directly into a new session.

Everything runs locally. No cloud, no API calls, no data leaving your machine.

---

## Who it's for

ExistenZ works for anyone who uses Claude Code for ongoing, complex work — not just developers.

| Domain | What becomes searchable |
|---|---|
| **Development** | Architecture decisions, bug fixes, code patterns, deployment history |
| **Content & writing** | Tone guidelines, approved drafts, client feedback, style decisions |
| **SEO & marketing** | Keyword strategies, competitor analyses, campaign decisions |
| **Research & analysis** | Findings, source lists, conclusions, methodology decisions |
| **Strategy & consulting** | Client briefs, recommendations, decisions, open questions |
| **Any project work** | What was discussed, what was delivered, what's still open |

---

## How it looks

```
$ existenz "what tone did we agree on for the newsletter" --hybrid

  ExistenZ  ·  HYBRID (BM25 + Semantic)  ·  0.24s

  [1] 2026-03-18  client-project  7f2b1c9a
      "agreed: direct, no corporate language, max 3 paragraphs per section,
       always end with one concrete next step — no vague CTAs"
      → read-session 7f2b1c9a --last 5

  [2] 2026-03-04  content-strategy  4d8e3f11
      "client rejected formal tone in v2 — wants conversational, first person,
       short sentences. Reference: the onboarding email they sent us."
      → read-session 4d8e3f11 --context
```

The session IDs lead directly to the full conversation. `read-session 7f2b1c9a --last 5` gives you the exact last 5 message pairs — word for word — ready to paste as context into a new session.

---

## Use cases

### Pick up where you left off

You were deep in a project yesterday — a client brief, a piece of research, a refactor, a content strategy. Today you open a new session with zero context.

`existenz --continuation "project-name"` finds your most recent sessions, shows their topics, the open threads, and the exact last message. You call `read-session` on the most relevant one and paste the context into the new session. You're back in 10 seconds instead of 10 minutes.

---

### Recover a decision

Something comes up that you know you've worked through before — a client preference, a pricing decision, an architectural tradeoff, a writing guideline. You know the answer is in there somewhere.

`existenz "what we decided about X" --hybrid` combines exact and semantic search to find it even if you don't remember the precise words used. The result shows you the session, the project, and the relevant excerpt — with a direct pointer to read the full context.

---

### Reconstruct a client brief

You're starting a new piece of work and want to go back to the original briefing. What was the target audience? What tone did they ask for? What were the constraints?

`existenz "briefing target audience brand voice" --semantic` finds conceptually related sessions even if those exact words weren't used. The semantic engine understands what you mean, not just what you typed.

---

### See everything that's been completed

You need a full picture of what's been finished — for a retrospective, a client report, or just to know where things stand across a project.

`existenz --milestone` lists all sessions where a meaningful completion was detected: a delivery approved, content published, a feature shipped, a report sent. Filtered by project or date as needed.

---

### Re-onboard after a break

Coming back after two weeks away from a project. Before touching anything, you need the full picture — current state, what's complete, what's still open, which threads need to be picked up.

`existenz --briefing "project-name"` generates a structured project overview: session count, completed milestones, in-progress items, and direct pointers to the most relevant sessions to read for context.

---

### Pull a specific fact or quote

You remember Claude gave you a specific benchmark, recommendation, or source reference weeks ago — and you need it now.

`existenz "conversion rate benchmark ecommerce" --hybrid` finds it. Exact results, exact session, exact context. No re-researching what you've already researched.

---

### For developers: find the fix

A problem that looks familiar. You're sure you've solved something similar before, on a different project or three months ago.

`existenz "CORS 403 on POST requests" --hybrid` finds the session, the diagnosis, and the exact fix. The fix that took two hours the first time takes two minutes the second.

---

## Architecture

### Indexing — runs after every response

```mermaid
flowchart LR
    A([Claude Code\nSession]) -->|Stop event| B[ExistenZ\nHook]
    B -->|background\n~2 seconds| C{Incremental\nIndexer}
    C --> D[(SQLite\nFTS5\nfull-text)]
    C --> E[(ONNX\nEmbeddings)]
    C --> F[(Session\nMetadata +\nFingerprint)]

    style A fill:#1e1e2e,color:#cdd6f4,stroke:#45475a
    style D fill:#1e3a5f,color:#cdd6f4,stroke:#45475a
    style E fill:#1e3a5f,color:#cdd6f4,stroke:#45475a
    style F fill:#1e3a5f,color:#cdd6f4,stroke:#45475a
```

### Search — two engines, one result

```mermaid
flowchart LR
    Q([Your query]) --> B[BM25\nexact match]
    Q --> S[Semantic\nmeaning match]
    B --> R[Reciprocal\nRank Fusion]
    S --> R
    R --> OUT([Ranked\nresults])

    style Q fill:#1e1e2e,color:#cdd6f4,stroke:#45475a
    style OUT fill:#1e1e2e,color:#cdd6f4,stroke:#45475a
    style R fill:#2d1b4e,color:#cdd6f4,stroke:#45475a
```

**BM25** (SQLite FTS5) matches your exact words — fast and precise.
**Semantic search** (ONNX embeddings, runs locally) matches your meaning — finds results even when the words differ.
**Reciprocal Rank Fusion** merges both result lists into a single ranking that consistently outperforms either approach alone.

### Reconstruction — three modes

Once you have a session ID, `read-session` gives you the conversation back in whatever form you need:

- `--last 5` — the last 5 message pairs, exact wording, ready to paste as context
- `--context` — a smart summary (~5–8k tokens) optimized for resuming work in a new session
- `--full` — the complete session, untruncated

---

## Features

| Feature | What it means in practice |
|---|---|
| **Hybrid search** | Finds what you searched for *and* what you meant — BM25 + Semantic via RRF |
| **Session fingerprinting** | Every session auto-tagged: deploy, milestone, or topic cluster |
| **Continuation mode** | One command to see where you left off, across any project |
| **Project briefing** | Full project re-onboarding: completed, in-progress, open threads |
| **Conversation reconstruction** | Read back any session — last N messages, smart summary, or complete |
| **Multilingual** | German/English mixed content, umlauts normalized, CamelCase split |
| **100% offline** | ONNX embeddings run locally — nothing leaves your machine, ever |
| **Zero-maintenance indexing** | Stop Hook indexes every response in the background automatically |

---

## vs. Alternatives

| | ExistenZ | [search-sessions](https://github.com/sinzin91/search-sessions) | [cc-conversation-search](https://github.com/akatz-ai/cc-conversation-search) |
|---|:---:|:---:|:---:|
| Hybrid BM25 + Semantic | ✅ | ❌ | ✅ |
| Session fingerprinting | ✅ | ❌ | ❌ |
| Continuation / briefing mode | ✅ | ❌ | ❌ |
| Conversation reconstruction | ✅ | ❌ | ❌ |
| Multilingual | ✅ | ❌ | ❌ |
| Auto-index via hook | ✅ | manual | manual |
| Fully offline | ✅ | ✅ | ✅ |

---

## Requirements

- Python 3.10+
- [Claude Code](https://claude.ai/code) installed (`~/.claude/` must exist)
- macOS or Linux

---

## Installation

```bash
git clone https://github.com/456253475624576457/existenz
cd existenz
bash install.sh
```

The installer handles everything in one step: installs dependencies, places the scripts, wires the Stop Hook into `~/.claude/settings.json`, and builds the initial index. The first run downloads the embedding model (~33 MB, one-time).

```bash
# Add to PATH if needed
echo 'export PATH="$HOME/.claude/scripts:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

```bash
bash install.sh --upgrade    # Re-install over existing
bash install.sh --uninstall  # Remove scripts and hook
```

---

## Commands

```bash
# Search
existenz "query"                        # Exact match (BM25)
existenz "query" --hybrid               # Exact + semantic — best quality
existenz "query" --semantic             # Semantic only — finds related concepts
existenz "term1 term2" --any            # OR logic
existenz "query" --since 2026-01-01    # Filter by date
existenz "query" --deployed             # Only sessions with a deploy
existenz "query" --milestone            # Only completed milestone sessions
existenz "query" --unique               # One result per session
existenz "query" --project "name"       # Limit to one project

# Resume
existenz --continuation "project"       # Where was I in the last 48h?
existenz --briefing "project"           # Full project re-onboarding

# Reconstruct
read-session <id> --last 5              # Last N message pairs, exact wording
read-session <id> --context             # Smart summary, optimized to resume
read-session <id> --full                # Complete session, untruncated

# Index
existenz --index                        # Incremental update (auto-runs via hook)
existenz --index --force                # Full rebuild
existenz --stats                        # Statistics
existenz --fingerprint-all              # Classify all sessions
```

---

## Configuration

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `EXISTENZ_DATA_DIR` | `~/.claude` | Base directory for index files |
| `EXISTENZ_SESSIONS_DIR` | `~/.claude/projects` | Claude Code session storage |
| `EXISTENZ_INDEX_DB` | `~/.claude/session-index.db` | SQLite full-text index |
| `EXISTENZ_EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model |

Legacy `SSS_*` variables are still accepted.

### Embedding models

| Model | Size | Recommended for |
|---|---|---|
| `BAAI/bge-small-en-v1.5` | 33 MB | English-only sessions (default) |
| `intfloat/multilingual-e5-small` | 117 MB | **Mixed-language sessions** |
| `BAAI/bge-m3` | 568 MB | Maximum multilingual quality |

```bash
EXISTENZ_EMBED_MODEL=intfloat/multilingual-e5-small existenz --index --force
```

Index size: ~0.4 MB per session (~285 MB at 500 sessions). See [PRIVACY.md](PRIVACY.md).

---

## Privacy

All data stays on your machine. Your session index contains your full conversation history — treat it accordingly. See [PRIVACY.md](PRIVACY.md) for what the index contains, how to move it to an encrypted volume, and how to delete it cleanly. The `.gitignore` in this repo excludes all index files by default.

---

## Built by

Florian Stangl — built out of necessity after 500+ Claude Code sessions across development, SEO, content strategy, and client work. The session history was always there. Getting back to it wasn't.

---

## License

MIT — see [LICENSE](LICENSE).
