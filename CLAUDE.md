# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small Flask app that copies secrets from a Clavis Secret Server (Thycotic/Delinea, Oxford University on-prem) into a 1Password vault through a 1Password Connect server. See README.md for the user-facing flow and the Kubernetes deployment notes.

## Commands

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_SECRET_KEY="$(openssl rand -hex 32)"
python app.py                      # Flask dev server, debug=True, http://localhost:5000

docker build -t clavis1passsync .
docker run -p 5000:5000 -e FLASK_SECRET_KEY=... clavis1passsync   # uWSGI via uwsgi.ini
```

There is no test suite, linter config, or build step. `requirements.txt` includes `uwsgi`, which does not build on native Windows. To run locally on Windows, install `flask` and `requests` only, or use Docker/WSL.

To exercise anything past the start page you need a real, reachable Clavis server and 1Password Connect server plus API tokens. The app has no mocks or offline mode.

## Architecture

**No server-side state.** The Clavis FQDN/token and the 1Password Connect FQDN/token live only in Flask's signed session cookie, set by `POST /connect` after both connections are checked. Every route reads its credentials from `session`. So `FLASK_SECRET_KEY` has to be the same across uWSGI workers and replicas. The app sits behind one proxy hop (`ProxyFix`), and `SESSION_COOKIE_SECURE` is controlled by an env var.

**Request flow.** The server renders `/`, `/dashboard` and `/tree`. The `/tree` page (`templates/tree.html`) then runs client-side JS that calls three JSON endpoints:
- `GET /op/items/<vault_id>` lists the items in the chosen vault.
- `POST /op/match` with `{vault_id, clavis_ids}` returns which IDs already exist, for the preview ("Apply").
- `POST /sync` with `{vault_id, clavis_ids}` does the real create/update and returns per-item results.

**The identity link between the two systems is a tag.** Every item written to 1Password gets a `clavisId:<id>` tag (`CLAVIS_TAG_PREFIX` in `classes.py`). `onepass_functions.mapExistingSecrets` scans a vault's item tags to build a `clavisId -> 1Password item id` map. `createUpdateOPSecret` uses that map to choose between PUT (update) and POST (create). Syncing depends on this tag convention, so don't change it. `createUpdateOPSecret` rebuilds the map for every secret, which means each sync fetches the vault's item list once per item.

**Clavis folders become 1Password tags.** 1Password has no folders, so `secret.buildTags()` splits the Clavis `folderPath` on `\` into separate tags and appends the `clavisId:` tag.

**Building 1Password items** happens in `clavis_functions.buildClavisSecretForOnePass`, which branches on the Clavis secret template:
- Normal secrets become a `LOGIN` item. The `resource`, `username`, `password` and `notes` slugs map to 1Password URL, username, password and notes fields.
- `Certificate` template secrets become a `SECURE_NOTE` item. File fields (cert, private key, bundle) aren't included in the detail response, so each one is downloaded separately from `/api/v1/secrets/<id>/fields/<slug>`, and only when `fileAttachmentId` is set (empty file fields return 404). File content is stored as UTF-8 text, or as base64 with the label suffix `(base64)` if it isn't valid UTF-8. Password fields here must keep `purpose=''`, because 1Password Connect rejects a SECURE_NOTE that has a PASSWORD-purpose field.

**API clients** (`clavis_functions.py`, `onepass_functions.py`) are plain `requests` calls that build their own Bearer headers against `https://<fqdn>`. Most of them return `None` on a non-200 response and never raise, and callers check for `None`. Clavis list endpoints are paginated with `take`/`skip`. Use the `getAll*` helpers, which page until a short page comes back. The Clavis API mixes `/api/v1` (folders, field downloads) and `/api/v2` (secrets).

`classes.py` holds plain value objects. `secret.toJson()` builds the 1Password Connect item payload from the objects' `__dict__`, so any attribute added to `secretField`, `vault` or `clavisSection` ends up in the API request.

## Style

The code uses camelCase for functions and variables in the API/client modules and snake_case in `app.py` routes and helpers. Follow whichever convention the file you're editing uses.
