"""Verify declared source files and optionally read current server hashes. Never deploy."""
import argparse
import ast
import hashlib
import json
import pathlib
import shlex
import subprocess

def verify(root):
    manifest = json.loads((root / 'server-source/source-manifest.json').read_text(encoding='utf-8'))
    errors = []
    for entry in manifest['files']:
        relative = pathlib.PurePosixPath(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe repository path')
        file = root / 'server-source' / relative
        if file.is_symlink() or not file.is_file():
            errors.append(str(relative) + ': missing/linked source')
            continue
        data = file.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['repository_sha256']:
            errors.append(str(relative) + ': source changed; update reviewed candidate hash, preserve server baseline hash')
        if file.suffix == '.py':
            ast.parse(data.decode('utf-8'), filename=str(file))
    if errors:
        raise RuntimeError('\n'.join(errors))
    return manifest

def check_server(manifest, host, key):
    paths = [entry['server_path'] for entry in manifest['files']]
    for path in paths:
        relative = pathlib.PurePosixPath(path)
        if not path.startswith('/opt/company-tools/') or '..' in relative.parts or not relative.is_absolute():
            raise ValueError('Unsafe server path')
    argv = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15']
    if key:
        argv.extend(['-i',key])
    argv.extend([host, 'sha256sum -- ' + ' '.join(shlex.quote(p) for p in paths)])
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=True)
    hashes = {}
    for line in result.stdout.splitlines():
        digest, path = line.split(maxsplit=1)
        hashes[path.lstrip('*')] = digest
    changed = [entry['path'] for entry in manifest['files'] if hashes.get(entry['server_path']) != entry['server_sha256']]
    if changed:
        raise RuntimeError('Online code changed after baseline; preserve it and integrate forward: ' + ', '.join(changed))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', default=str(pathlib.Path(__file__).resolve().parents[1]))
    parser.add_argument('--server', help='Optional existing trusted SSH destination; read-only comparison')
    parser.add_argument('--key', help='Local private-key path only; never distribute private keys')
    args = parser.parse_args()
    manifest = verify(pathlib.Path(args.repo).resolve())
    if args.server:
        check_server(manifest, args.server, args.key)
    print(json.dumps({'module':manifest['module'], 'files':len(manifest['files']), 'repository_hashes':'pass', 'server_baseline':'pass' if args.server else 'not-checked', 'deploy_performed':False}))

if __name__ == '__main__':
    main()
