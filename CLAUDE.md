# CLAUDE.md — LPN Generator

This file orients AI agents (Claude Code, Cursor, any other code-writing assistant) working in this repository. Humans should keep it accurate; agents read it on every run.

## Read this first

This Project is licensed under the Suraya Methodology and Platform License (see [LICENSE-suraya.md](LICENSE-suraya.md)). The org-wide engineering charter — roles, stack, branch protection, CODEOWNERS rules, AI agent rules — lives in the canonical Suraya repository:

- `https://github.com/surayainc/suraya/blob/main/ENGINEERING_OPERATING_MODEL.md`

This file (CLAUDE.md) is project-specific context layered on top of that operating model. If something here contradicts the operating model, the operating model wins and this file is the bug.

## What this project is

A password-protected Streamlit web app that generates unique 10-digit License Plate Numbers and renders 4×6 thermal labels (Rollo) as a downloadable PDF.

Owner: @kareem-ynk
Hosting: Streamlit Community Cloud (temporary; subject to migration)
Stack: Streamlit (Python) + Supabase (Postgres) + ReportLab (PDF)

## Conventions specific to this project

- LPNs are 9 random digits + 1 mod-10 check digit. Uniqueness is enforced by a `UNIQUE` constraint on `lpns.lpn`; the app retries on collision.
- The Streamlit app is the **sole writer** to `lpns`. RLS is disabled on that table by design; the rationale is in [supabase_schema.sql](supabase_schema.sql). Treat access control as app-layer, not DB-layer, when modifying anything that writes to this table.
- Secrets live in Streamlit Cloud's app settings (see [README.md](README.md) for the configuration walkthrough). `.streamlit/secrets.toml` is gitignored — never commit.
- End-user setup walkthrough (Supabase + Streamlit Cloud + GitHub) lives in [README.md](README.md). For local dev: `pip install -r requirements.txt && streamlit run app.py` after populating `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example`.
