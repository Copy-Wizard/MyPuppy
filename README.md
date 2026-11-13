# MyPuppy website

A static site: `index.html` is the sales page, `app/` is the MyPuppy app. Accounts and saved progress use Supabase. Checkout uses Gumroad.

With `config.js` left empty, the app runs on one device only, with testing tools in the Help tab. Fill in `config.js` to turn on accounts and checkout.

## Files

| File | What it is |
|---|---|
| `index.html` | Sales page |
| `app/index.html` | The app (built from `tools/prototype.html` by `tools/build_app.py`) |
| `config.js` | Your Supabase and Gumroad settings |
| `supabase/schema.sql` | Database tables and security rules |
| `supabase/functions/gumroad-ping/` | Unlocks an account when Gumroad reports a sale |
| `tools/test.mjs` | Browser tests |

## Setup

### 1. Supabase (database and accounts)
1. Create a project at supabase.com (name `mypuppy`, region East US).
2. Open **SQL Editor**, paste all of `supabase/schema.sql`, and run it.
3. Open **Authentication > Sign In / Providers > Email**. To let people start right away, turn off "Confirm email". (You can turn it back on once email sending from your domain is set up.)
4. Open **Project Settings > API**. Copy the **Project URL** and the **anon public** key into `config.js`.

### 2. Gumroad (checkout)
1. Create a product for the 90-Day Pass at $29. Paste its link into `config.js` under `gumroad.pass`. Lifetime and Monthly are optional.
2. Deploy the payment function. In Supabase: **Edge Functions > Deploy a new function**, name it `gumroad-ping`, paste `supabase/functions/gumroad-ping/index.ts`.
3. In **Edge Functions > Secrets**, add `PING_SECRET` with a long random value. Turn off "Verify JWT" for this function, since Gumroad cannot send a Supabase login.
4. In Gumroad: **Settings > Advanced > Ping**, set the URL to
   `https://<your-project>.supabase.co/functions/v1/gumroad-ping?secret=<PING_SECRET>`
5. Use Gumroad's "Send test ping" button, then check the `purchases` table in Supabase for a new row.

Buyers must pay with the same email as their MyPuppy account. The checkout link fills it in for them.

Refunds: the basic Ping fires on sales only. After refunding someone in Gumroad, set `unlocked` to false on their row in the `profiles` table.

### 3. Hosting and domain (GitHub Pages)
1. Put these files in a GitHub repository.
2. In the repository: **Settings > Pages**, deploy from the main branch, root folder.
3. Add your domain under **Custom domain** and create the DNS records GitHub shows you at your registrar.

## Not built yet
- Daily reminder emails (needs your domain and an email-sending service).
- Usage tracking (which day people drop off).

## Rebuild the app after editing the prototype
    python3 tools/build_app.py tools/prototype.html
