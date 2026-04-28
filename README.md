# LPN Generator (Web App)

A password-protected Streamlit web app that generates unique 10-digit License Plate Numbers and renders 4×6 thermal labels (Rollo) as a downloadable PDF.

- **Persistence:** Supabase (Postgres) — every issued LPN is stored with a UNIQUE constraint, so duplicate LPNs are impossible across all users, devices, and sessions.
- **Auth:** shared password via Streamlit secrets.
- **Hosting:** [Streamlit Community Cloud](https://share.streamlit.io) (free).

## Label format

- 6"×4" landscape page, one label per PDF page
- Header: `Client: <name>` (left), `Date: MM/DD/YY` (right)
- Big bold 10-digit LPN, last 3 digits in larger font
- Code 128 barcode encoding only the LPN (no GS1/SSCC)
- Human-readable LPN under the barcode

## Setup (one time, ~10 min)

### 1. Supabase

1. Create a free account at [supabase.com](https://supabase.com) and click **New project**.
2. Pick any name/region. Save the database password somewhere (you won't need it again unless you do raw DB stuff).
3. In your project, go to **SQL Editor** → **New query**, paste the contents of `supabase_schema.sql`, and click **Run**. This creates the `lpns` table.
4. Go to **Project Settings** → **API**. You'll need:
   - **Project URL** (e.g. `https://abc123.supabase.co`)
   - **anon public** key (or the **service_role** key for server-side use — both work for this app since the app is the only writer)

### 2. GitHub

1. Create a new repo (e.g. `nominal-lpn-generator`) — can be private.
2. Push the contents of this folder. **Do NOT commit `.streamlit/secrets.toml`** if you create one locally.

### 3. Streamlit Community Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
2. Click **New app**, pick the repo, branch `main`, and main file `app.py`.
3. Open **Advanced settings** → **Secrets** and paste:
   ```toml
   app_password = "your-strong-password"
   supabase_url = "https://YOUR-PROJECT-REF.supabase.co"
   supabase_key = "YOUR-ANON-OR-SERVICE-ROLE-KEY"
   ```
4. Click **Deploy**. You'll get a public URL like `nominal-lpn.streamlit.app`.

Share the URL + password with anyone who needs to print labels.

## Local dev

```bash
pip install -r requirements.txt
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml with your password + Supabase keys
streamlit run app.py
```

## How uniqueness works

Each LPN is 9 random digits + a mod-10 check digit (10 digits total). Random space is ~10 billion, so collision chance is vanishingly small — but the Supabase `lpns.lpn` column has a `UNIQUE` constraint, so even in the unlikely event of a collision, the insert fails and the app retries with a new random number. Result: **no duplicate LPN can ever be issued, even across every user, device, and session.**

## Files

- `app.py` — the Streamlit app
- `requirements.txt` — Python deps
- `supabase_schema.sql` — one-time DB setup
- `.streamlit/secrets.toml.example` — secrets template
- `.gitignore` — ignores secrets, PDFs, caches
