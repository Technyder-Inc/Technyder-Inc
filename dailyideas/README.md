# DailyIdeas

A private Technyder project for generating, storing, and managing daily ideas powered by AI automation.

## Overview

DailyIdeas is an AI-driven system that surfaces, categorizes, and tracks creative or operational ideas on a daily cadence. Built with Technyder's data engineering and LLM pipeline stack.

## Features

- Daily idea generation via LLM pipelines
- Idea categorization and tagging
- Storage and retrieval (Supabase backend)
- Scheduled automation via GitHub Actions

## Project Structure

```
dailyideas/
├── src/
│   ├── generator.py      # LLM-based idea generation
│   ├── storage.py        # Supabase storage client
│   └── scheduler.py      # Daily job scheduler
├── tests/
│   └── test_generator.py
├── .github/
│   └── workflows/
│       └── daily-run.yml
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in API keys
python src/scheduler.py
```

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |

## Branching

- `main` — stable releases
- `dev` — integration branch
- `feat/*` — feature branches
- `claude/*` — AI-assisted development branches

## License

Private — © Technyder. All rights reserved.
