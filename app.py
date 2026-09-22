import os
import sys

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from clavis_functions import buildClavisSecretForOnePass, getAllClavisFolders, getAllClavisSecrets, getClavisFolders
from onepass_functions import createUpdateOPSecret, getOPSecrets, getOPVaults, mapExistingSecrets

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    # Fine for a single-process dev server, but fatal under multiple uwsgi
    # workers or Kubernetes replicas: each would get its own random key and
    # sign session cookies differently, so logins would break depending on
    # which worker/pod handles the next request. In Kubernetes, set the same
    # value on every replica (e.g. from a Secret).
    print('WARNING: FLASK_SECRET_KEY is not set, using a random per-process key.', file=sys.stderr)
    app.secret_key = os.urandom(24)

# Trust exactly one reverse-proxy hop (the ingress) for X-Forwarded-* headers,
# so request.is_secure and the secure-cookie check below see the scheme the
# browser actually used, not the plain HTTP the pod receives from Envoy.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Off by default so plain-HTTP local/dev use keeps working; set to "true"
# behind the Contour ingress, which terminates TLS for browsers.
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'


def strip_scheme(fqdn):
    return fqdn.strip().removeprefix('https://').removeprefix('http://').strip('/')


def build_clavis_tree(folders, secrets):
    nodes = {
        f['id']: {'id': f['id'], 'name': f.get('folderName') or f.get('folderPath') or str(f['id']),
                   'children': [], 'secrets': []}
        for f in folders
    }

    roots = []
    for f in folders:
        node = nodes[f['id']]
        parent_id = f.get('parentFolderId')
        if parent_id in (None, -1) or parent_id not in nodes:
            roots.append(node)
        else:
            nodes[parent_id]['children'].append(node)

    uncategorized = []
    for s in secrets:
        item = {
            'id': s.get('id'),
            'name': s.get('name') or s.get('title') or s.get('secretName') or 'Secret {}'.format(s.get('id')),
        }
        folder_id = s.get('folderId')
        (nodes[folder_id]['secrets'] if folder_id in nodes else uncategorized).append(item)

    for node in nodes.values():
        node['children'].sort(key=lambda n: n['name'].lower())
        node['secrets'].sort(key=lambda n: n['name'].lower())
    roots.sort(key=lambda n: n['name'].lower())

    if uncategorized:
        uncategorized.sort(key=lambda n: n['name'].lower())
        roots.append({'id': None, 'name': 'No folder', 'children': [], 'secrets': uncategorized})

    return roots


def build_op_vaults(vaults):
    return sorted(
        (
            {'id': v.get('id'), 'name': v.get('name') or v.get('id')}
            for v in vaults
        ),
        key=lambda v: v['name'].lower(),
    )


def build_op_items(items):
    return sorted(
        (
            {
                'id': i.get('id'),
                'title': i.get('title') or 'Item {}'.format(i.get('id')),
                'tags': i.get('tags') or [],
            }
            for i in items
        ),
        key=lambda i: i['title'].lower(),
    )


@app.route('/healthz', methods=['GET'])
def healthz():
    # No session/credential checks - Kubernetes liveness/readiness probes
    # need a cheap, always-reachable target, not a check of per-user state.
    return 'ok', 200


@app.route('/', methods=['GET'])
def index():
    return render_template(
        'index.html',
        clavisfqdn=session.get('clavisfqdn', ''),
        onepassfqdn=session.get('onepassfqdn', ''),
    )


@app.route('/connect', methods=['POST'])
def connect():
    clavisfqdn = strip_scheme(request.form.get('clavisfqdn', ''))
    claviskey = request.form.get('claviskey', '').strip()
    onepassfqdn = strip_scheme(request.form.get('onepassfqdn', ''))
    onepasskey = request.form.get('onepasskey', '').strip()

    if not all([clavisfqdn, claviskey, onepassfqdn, onepasskey]):
        flash('Please fill in all fields.', 'error')
        return render_template(
            'index.html',
            clavisfqdn=clavisfqdn,
            onepassfqdn=onepassfqdn,
        )

    if getClavisFolders(clavisfqdn, claviskey, take=1) is None:
        flash('Could not connect to Clavis. Check the address and token.', 'error')
        return render_template(
            'index.html',
            clavisfqdn=clavisfqdn,
            onepassfqdn=onepassfqdn,
        )

    try:
        getOPVaults(onepassfqdn, onepasskey)
    except Exception:
        flash('Could not connect to 1Password Connect. Check the address and token.', 'error')
        return render_template(
            'index.html',
            clavisfqdn=clavisfqdn,
            onepassfqdn=onepassfqdn,
        )

    session['clavisfqdn'] = clavisfqdn
    session['claviskey'] = claviskey
    session['onepassfqdn'] = onepassfqdn
    session['onepasskey'] = onepasskey

    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'clavisfqdn' not in session:
        return redirect(url_for('index'))
    return render_template(
        'dashboard.html',
        clavisfqdn=session['clavisfqdn'],
        onepassfqdn=session['onepassfqdn'],
    )


@app.route('/tree', methods=['GET'])
def tree():
    if 'clavisfqdn' not in session:
        return redirect(url_for('index'))

    clavisfqdn = session['clavisfqdn']
    claviskey = session['claviskey']

    folders = getAllClavisFolders(clavisfqdn, claviskey)
    if folders is None:
        flash('Could not fetch the Clavis folder list.', 'error')
        return redirect(url_for('dashboard'))

    secrets = getAllClavisSecrets(clavisfqdn, claviskey)
    if secrets is None:
        flash('Could not fetch the Clavis item list.', 'error')
        return redirect(url_for('dashboard'))

    roots = build_clavis_tree(folders, secrets)

    opvaults = getOPVaults(session['onepassfqdn'], session['onepasskey'])
    if opvaults is None:
        flash('Could not fetch the 1Password vault list.', 'error')
        opvaults = []
    vaults = build_op_vaults(opvaults)

    return render_template('tree.html', roots=roots, clavisfqdn=clavisfqdn, vaults=vaults)


@app.route('/op/items/<vault_id>', methods=['GET'])
def op_items(vault_id):
    if 'onepassfqdn' not in session:
        return jsonify({'error': 'not connected'}), 401

    items = getOPSecrets(session['onepassfqdn'], vault_id, session['onepasskey'])
    if items is None:
        return jsonify({'error': 'Could not fetch the vault items.'}), 502

    return jsonify(build_op_items(items))


@app.route('/op/match', methods=['POST'])
def op_match():
    if 'onepassfqdn' not in session:
        return jsonify({'error': 'not connected'}), 401

    data = request.get_json(silent=True) or {}
    vault_id = data.get('vault_id')
    clavis_ids = [str(cid) for cid in (data.get('clavis_ids') or [])]
    if not vault_id:
        return jsonify({'error': 'vault_id required'}), 400

    secret_map = mapExistingSecrets(session['onepassfqdn'], vault_id, session['onepasskey'])

    matched = {cid: secret_map[cid] for cid in clavis_ids if cid in secret_map}
    unmatched = [cid for cid in clavis_ids if cid not in secret_map]

    return jsonify({'matched': matched, 'unmatched': unmatched})


@app.route('/sync', methods=['POST'])
def sync():
    if 'clavisfqdn' not in session:
        return jsonify({'error': 'not connected'}), 401

    data = request.get_json(silent=True) or {}
    vault_id = data.get('vault_id')
    clavis_ids = [str(cid) for cid in (data.get('clavis_ids') or [])]
    if not vault_id:
        return jsonify({'error': 'vault_id required'}), 400
    if not clavis_ids:
        return jsonify({'error': 'clavis_ids required'}), 400

    clavisfqdn = session['clavisfqdn']
    claviskey = session['claviskey']
    onepassfqdn = session['onepassfqdn']
    onepasskey = session['onepasskey']

    all_secrets = getAllClavisSecrets(clavisfqdn, claviskey)
    if all_secrets is None:
        return jsonify({'error': 'Could not fetch the Clavis secret list.'}), 502
    folder_id_by_clavis_id = {str(s.get('id')): s.get('folderId') for s in all_secrets}

    opvaults = getOPVaults(onepassfqdn, onepasskey) or []
    vault_name = next((v.get('name') for v in opvaults if str(v.get('id')) == vault_id), '')

    results = []
    for clavis_id in clavis_ids:
        clavis_secret = buildClavisSecretForOnePass(
            clavisfqdn, claviskey, clavis_id, folder_id_by_clavis_id.get(clavis_id), vault_id, vault_name,
        )
        if clavis_secret is None:
            results.append({'id': clavis_id, 'ok': False, 'error': 'Secret not found in Clavis.'})
            continue

        response = createUpdateOPSecret(onepassfqdn, vault_id, onepasskey, clavis_secret)
        ok = response is not None and 200 <= response.status_code < 300
        result = {'id': clavis_id, 'ok': ok, 'title': clavis_secret.title}
        if not ok:
            result['error'] = '1Password error ({}).'.format(response.status_code if response is not None else '?')
        results.append(result)

    return jsonify({'results': results})


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
