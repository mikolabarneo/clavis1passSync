# clavis1passSync

A Flask web app that syncs secrets from Oxford University's on-prem **Clavis
Secret Server** (Thycotic/Delinea) into a cloud **1Password** vault via a
1Password Connect server.

It renders the Clavis folder tree, lets you browse a 1Password vault's
existing items side by side, preview which items would be created vs.
updated (matched by a `clavisId:<id>` tag written on every synced item), and
then run the sync for the selected secrets. Both regular login-style secrets
and Clavis "Certificate" secrets (certificate/private key/bundle files,
encryption password) are supported.

## How it works

1. On the start page you enter the Clavis server FQDN + API token and the
   1Password Connect server FQDN + API token. Nothing is persisted to disk -
   the app verifies both connections and keeps the credentials only in your
   signed session cookie for the rest of the browser session.
2. `/tree` shows the Clavis folder structure (checkboxes, cascading
   select/deselect, expand/collapse all) next to a 1Password vault picker
   showing that vault's items and tags (1Password has no folders, so Clavis
   folder paths become tags instead).
3. **Apply** overlays your selected Clavis secrets onto the 1Password list:
   matching items turn yellow ("will be updated"), items with no match turn
   green ("will be created"). **Reset** clears the overlay.
4. **Sync** creates/updates exactly those items in 1Password for real.

## Project layout

- `app.py` - Flask routes and session/request handling.
- `classes.py` - the `secret`/`folder`/`vault`/`secretField` value objects
  sent to 1Password, including tag building (`clavisId:<id>` + folder path).
- `clavis_functions.py` - Clavis Secret Server REST client, plus
  `buildClavisSecretForOnePass()` which turns a Clavis secret (login or
  certificate) into a 1Password item payload.
- `onepass_functions.py` - 1Password Connect REST client
  (`createUpdateOPSecret` decides create vs. update by looking up the
  `clavisId:` tag).
- `templates/` - the four pages (connect form, dashboard, tree/sync view).
- `Dockerfile`, `uwsgi.ini` - production image (uWSGI, non-root user).
- `k8s/full.yaml` - example Namespace/Secret/Deployment/Service/DNSEndpoint/
  Certificate/HTTPProxy manifests for a Contour-fronted cluster.

## Requirements

- Python 3.12+ (developed against 3.14)
- Network access to your Clavis Secret Server and 1Password Connect server
- A running 1Password Connect server and an API token scoped to the vault(s)
  you want to sync into

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export FLASK_SECRET_KEY="$(openssl rand -hex 32)"
python app.py
```

The dev server listens on `http://localhost:5000`. Open it, enter the four
connection values on the start page, and continue from there - no other
configuration is read from the environment.

## Running with Docker

```bash
docker build -t clavis1passsync .
docker run -d -p 5000:5000 \
  -e FLASK_SECRET_KEY="$(openssl rand -hex 32)" \
  clavis1passsync
```

`FLASK_SECRET_KEY` must be set (or every uWSGI worker/replica signs session
cookies with a different random key and logins start failing at random - the
app logs a warning if you forget it). `uwsgi.ini` runs 4 processes / 2
threads and serves plain HTTP on `0.0.0.0:5000`.

## Environment variables

| Variable               | Required | Default | Purpose |
|-------------------------|----------|---------|---------|
| `FLASK_SECRET_KEY`      | yes (prod) | random per process | Signs the session cookie holding your Clavis/1Password credentials for the browser session. Must be identical across all replicas/workers. |
| `SESSION_COOKIE_SECURE` | no | `false` | Set to `true` once the app is served over HTTPS (e.g. behind the Contour ingress), so the browser only sends the session cookie over an encrypted connection. |

## Deploying to Kubernetes (Contour ingress)

`k8s/full.yaml` is a starting point, not a ready-to-apply manifest - fill in
before applying:

- `image:` in the `Deployment` - your pushed image reference.
- `virtualhost.fqdn` in the `HTTPProxy` and `dnsName`/`targets` in the
  `DNSEndpoint` - your real hostname and external-dns target.
- `issuerRef.name` in the `Certificate` - your cert-manager `ClusterIssuer`.
- `stringData.FLASK_SECRET_KEY` in the `Secret` - a real generated key
  (`openssl rand -hex 32`); do not commit a filled-in copy of this file.

```bash
kubectl apply -f k8s/full.yaml
```

The app sits behind Envoy (Contour), so it trusts one `X-Forwarded-*` hop for
scheme detection (`ProxyFix`) - set `SESSION_COOKIE_SECURE=true` once TLS is
terminated at the ingress, otherwise the session cookie carrying your Clavis/
1Password credentials would only be safe over plain HTTP.

`/healthz` is a dependency-free 200 OK, used as both the readiness and
liveness probe target.
