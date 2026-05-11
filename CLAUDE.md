# CLAUDE.md — Technyder-Inc Repository

## Repository Overview

This is the **Technyder-Inc** organization repository. All repositories in this organization are **private**.

## Active Projects

### dailyideas
**Branch:** `claude/setup-dailyideas-repo-TiAM0`
**Path:** `./dailyideas/`
**Status:** In active development

An AI-driven daily idea generation and management system. Uses Claude (Anthropic) for LLM-powered idea generation and Supabase for storage.

**Key files:**
- `dailyideas/src/generator.py` — Claude API idea generation
- `dailyideas/src/storage.py` — Supabase read/write
- `dailyideas/src/scheduler.py` — Daily job runner
- `dailyideas/.github/workflows/daily-run.yml` — GitHub Actions schedule

**Setup:**
```bash
cd dailyideas
pip install -r requirements.txt
cp .env.example .env   # fill ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY
python src/scheduler.py
```

**Run tests:**
```bash
cd dailyideas
pytest tests/
```

---

## Repository Settings

- All repos: **Private**
- Default branch: `main`
- Integration branches: `dev`
- Feature branches: `feat/*`
- AI-assisted branches: `claude/*`

## Secrets Required (GitHub Actions)

| Secret | Used By |
|---|---|
| `ANTHROPIC_API_KEY` | dailyideas — Claude API |
| `SUPABASE_URL` | dailyideas — database |
| `SUPABASE_KEY` | dailyideas — database |

## Development Guidelines

- Use `claude/*` branches for AI-assisted changes
- PRs require at least one approval before merging to `main`
- Never commit `.env` files — use `.env.example` as template
- All secrets managed via GitHub Actions secrets

## Contact

**Technyder** · auh@technyder.co · https://technyder.co
