"""Owner Git audit and opt-in local guards; never reset/stash/push/deploy code.

Run independently on each computer. A Windows report cannot verify a Mac tree.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MODULES = {
    'company': ('公司中心', 'supertin0609/Company-', '公司/Company-'),
    'data-center': ('数据中心', 'supertin0609/analysis', '店铺数据分析工具/analysis'),
    'operations': ('店铺运营工作台', 'cccadyforwork-cloud/store-operations-system', '店铺运营工具台/store-operations-system'),
    '1688': ('1688', 'supertin0609/1688', '1688板块/1688'),
    'inventory': ('库存', 'supertin0609/storage', '库存工具/storage'),
    'replenishment': ('补货', 'supertin0609/Daliy-transfer-', '本地库存工具/Daliy-transfer-'),
    'transfer': ('库存调拨', 'supertin0609/storage-transfer', '库存调拨/storage-transfer'),
    'finance': ('财务', 'supertin0609/finance', '财务板块/finance'),
    'tools': ('工具中心', 'supertin0609/company-tool', '公司业务工具/company-tool'),
    'product': ('上传产品', 'cccadyforwork-cloud/shangpin_system', '亚马逊上传产品工具/shangpin_system'),
    'salary': ('薪资', 'supertin0609/salary-pay', '薪资工具/salary-pay'),
    'selection': ('选品', 'supertin0609/Day-Day-Up', '选品工具/Day-Day-Up'),
    'discount': ('折扣', 'supertin0609/Discount-', '折扣促销记录工具/Discount-'),
}


class GuardError(RuntimeError):
    pass


def identity(url):
    if url.startswith('git@github.com:'):
        path = url.split(':', 1)[1]
    else:
        parsed = urlparse(url)
        if parsed.scheme not in ('https', 'ssh') or parsed.hostname != 'github.com':
            raise GuardError('Only the registered GitHub host is accepted')
        if parsed.port or parsed.password or parsed.query or parsed.fragment:
            raise GuardError('Unexpected remote URL options')
        path = parsed.path.lstrip('/')
    if path.endswith('.git'):
        path = path[:-4]
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', path):
        raise GuardError('Unexpected repository identity')
    return path.lower()


def git(repo, *args, optional=False):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
    result = subprocess.run(['git', '-C', str(repo), *args], text=True, encoding='utf-8',
                            errors='replace', capture_output=True, timeout=90, env=env,
                            creationflags=0x08000000 if os.name == 'nt' else 0)
    if result.returncode and not optional:
        # Do not leak credentials from a malformed URL or credential-manager log.
        raise GuardError('Git check failed: ' + args[0] + '; stop without overwriting work')
    return result


def output(repo, *args, optional=False):
    return git(repo, *args, optional=optional).stdout.strip()


def ancestor(repo, previous, candidate):
    return git(repo, 'merge-base', '--is-ancestor', previous, candidate, optional=True).returncode == 0


def verify_remote(repo, module):
    expected = MODULES[module][1].lower()
    for args in (('remote', 'get-url', '--all', 'origin'), ('remote', 'get-url', '--push', '--all', 'origin')):
        urls = output(repo, *args).splitlines()
        if len(urls) != 1 or identity(urls[0]) != expected:
            raise GuardError('Wrong repository or ambiguous fetch/push URL for ' + module)
    root = Path(output(repo, 'rev-parse', '--show-toplevel')).resolve()
    if root != Path(repo).resolve():
        raise GuardError('Project points to a parent or different checkout, not this repository root')


def refresh(repo, module):
    verify_remote(repo, module)
    remote = output(repo, 'ls-remote', 'origin', 'refs/heads/main')
    floor = output(repo, 'config', '--local', '--get', 'company.ownerGuardFloor', optional=True)
    if not remote:
        if floor:
            raise GuardError('Previously verified main was deleted; do not initialize or overwrite it')
        return None
    if len(remote.splitlines()) != 1:
        raise GuardError('Remote main is ambiguous')
    output(repo, 'fetch', '--no-tags', 'origin', '+refs/heads/main:refs/remotes/origin/main')
    latest = output(repo, 'rev-parse', '--verify', 'refs/remotes/origin/main')
    if floor and not ancestor(repo, floor, latest):
        raise GuardError('Remote main was rewound/rewritten or verified history is missing')
    output(repo, 'config', '--local', 'company.ownerGuardFloor', latest)
    return latest


def check_candidate(repo, latest, phase, candidate=None, deployed=None):
    if not latest:
        if phase == 'deploy':
            raise GuardError('Empty main cannot be deployed')
        return
    head = candidate or output(repo, 'rev-parse', '--verify', 'HEAD', optional=True)
    if not head:
        raise GuardError('No local commit; remote main must be integrated first')
    if phase == 'commit':
        parents = [head] + output(repo, 'rev-parse', '-q', '--verify', 'MERGE_HEAD', optional=True).splitlines()
        if output(repo, 'ls-files', '-u') or not any(ancestor(repo, latest, parent) for parent in parents):
            raise GuardError('Include latest main and resolve conflicts before committing')
    elif not ancestor(repo, latest, head):
        raise GuardError('Candidate omits latest main; preserve and integrate both computers changes')
    if phase == 'deploy':
        if output(repo, 'status', '--porcelain'):
            raise GuardError('Uncommitted files are not a verified release')
        if head != latest:
            raise GuardError('Release must equal current remote main, not an older checkout')
        if not deployed or not ancestor(repo, deployed, head):
            raise GuardError('Supply real deployed SHA; candidate must contain deployed history')


def check_push(repo, module, latest, args, text):
    if len(args) != 2 or args[0] != 'origin' or identity(args[1]) != MODULES[module][1].lower():
        raise GuardError('Push must use the registered origin repository')
    for line in text.splitlines():
        local_ref, local_sha, remote_ref, reported_sha = line.split()
        if not remote_ref.startswith('refs/heads/') or set(local_sha) == {'0'}:
            raise GuardError('Deleting branches or pushing tags/arbitrary refs is forbidden')
        check_candidate(repo, latest, 'push', candidate=local_sha)
        current = output(repo, 'ls-remote', 'origin', remote_ref)
        if current:
            remote_sha = current.split()[0]
            output(repo, 'fetch', '--no-tags', 'origin', remote_ref)
            if not ancestor(repo, remote_sha, local_sha):
                raise GuardError('History rewrite/force push or concurrent newer remote commit refused')


def install(repo, module):
    verify_remote(repo, module)
    refresh(repo, module)
    git_dir = Path(output(repo, 'rev-parse', '--absolute-git-dir'))
    folder = git_dir / 'company-owner-guard'
    hooks = folder / 'hooks'
    current = output(repo, 'config', '--local', '--get', 'core.hooksPath', optional=True)
    if current and Path(current).resolve() == hooks.resolve():
        old = output(repo, 'config', '--local', '--get', 'company.ownerGuardOriginalHooks', optional=True)
    else:
        old_path = Path(current) if current else git_dir / 'hooks'
        if not old_path.is_absolute():
            old_path = Path(repo) / old_path
        old = str(old_path.resolve())
    hooks.mkdir(parents=True, exist_ok=True)
    program = folder / 'owner_git_guard.py'
    shutil.copy2(Path(__file__), program)
    output(repo, 'config', '--local', 'company.ownerGuardOriginalHooks', old)
    for hook in ('pre-commit', 'pre-push'):
        command = [sys.executable.replace('\\', '/'), str(program).replace('\\', '/'), 'hook',
                   '--module', module, '--repo', str(Path(repo).resolve()).replace('\\', '/'),
                   '--kind', hook, '--']
        target = hooks / hook
        target.write_text('#!/bin/sh\nexec ' + ' '.join(map(shlex.quote, command)) + ' "$@"\n', encoding='utf-8', newline='\n')
        target.chmod(0o755)
    output(repo, 'config', '--local', 'core.hooksPath', str(hooks).replace('\\', '/'))
    output(repo, 'config', '--local', 'pull.ff', 'only')
    output(repo, 'config', '--local', 'push.default', 'simple')
    return {'module': module, 'hooks': str(hooks), 'original_hooks_preserved': old}


def run_hook(args):
    extra = args.extra[1:] if args.extra[:1] == ['--'] else args.extra
    incoming = sys.stdin.read() if args.kind == 'pre-push' else ''
    latest = refresh(args.repo, args.module)
    if args.kind == 'pre-push':
        check_push(args.repo, args.module, latest, extra, incoming)
    else:
        check_candidate(args.repo, latest, 'commit')
    old = output(args.repo, 'config', '--local', '--get', 'company.ownerGuardOriginalHooks', optional=True)
    previous = Path(old) / args.kind if old else None
    if previous and previous.is_file():
        # Git's POSIX shell executes original shebangs, including on Windows.
        shell = shutil.which('sh')
        if not shell and os.name == 'nt':
            git_executable = shutil.which('git')
            if git_executable:
                git_home = Path(git_executable).parent.parent
                shell = next((str(path) for path in (git_home / 'bin/sh.exe', git_home / 'usr/bin/sh.exe') if path.is_file()), None)
        if not shell:
            raise GuardError('Cannot execute preserved original hook; stop rather than bypass it')
        result = subprocess.run([shell, '-c', 'exec "$@"', 'owner-original-hook', str(previous), *extra],
                                input=incoming, text=True,
                                creationflags=0x08000000 if os.name == 'nt' else 0)
        if result.returncode:
            raise GuardError('Existing project hook rejected operation; it has not been bypassed')


def locate(root, module):
    expected = Path(root) / MODULES[module][2]
    if (expected / '.git').exists():
        return expected
    # Mac folder labels need not be the Windows labels. Look only two levels
    # inside an explicitly supplied project root; never traverse home/volumes.
    candidates = []
    for first in Path(root).iterdir():
        if not first.is_dir() or first.is_symlink() or first.name.startswith('.'):
            continue
        children = [first] + [child for child in first.iterdir() if child.is_dir() and not child.is_symlink() and not child.name.startswith('.')]
        for candidate in children:
            if (candidate / '.git').exists():
                remote = output(candidate, 'remote', 'get-url', 'origin', optional=True)
                try:
                    if identity(remote) == MODULES[module][1].lower():
                        candidates.append(candidate)
                except GuardError:
                    pass
    if len(candidates) != 1:
        raise GuardError('Missing or multiple matching checkouts; use the actual project repository root')
    return candidates[0]


def audit(root, module_ids):
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'platform': sys.platform,
              'executed_on_mac': sys.platform == 'darwin', 'codex_project_associations_verified': False, 'modules': [],
              'miscellaneous': 'No registered Git repository; do not associate another module'}
    for module in module_ids:
        label, expected, relative = MODULES[module]
        repo = Path(root) / relative
        row = {'module': module, 'label': label, 'expected_repository': expected, 'path': str(repo)}
        try:
            repo = locate(root, module)
            row['path'] = str(repo)
            if not (repo / '.git').exists():
                raise GuardError('Repository directory not found; project path must be checked locally')
            latest = refresh(repo, module)
            head = output(repo, 'rev-parse', '--verify', 'HEAD', optional=True) or None
            dirty = output(repo, 'status', '--porcelain').splitlines()
            row.update(remote_main=latest, local_head=head, uncommitted_entries=len(dirty),
                       branch=output(repo, 'branch', '--show-current'),
                       hooks_path=output(repo, 'config', '--local', '--get', 'core.hooksPath', optional=True))
            row['status'] = ('empty-remote' if not latest else 'uncommitted-work' if dirty
                             else 'verified-latest' if head == latest else 'not-current-main')
        except (GuardError, subprocess.TimeoutExpired) as error:
            row.update(status='blocked', error=str(error))
        result['modules'].append(row)
    result['all_repositories_current_and_clean'] = all(row['status'] == 'verified-latest' for row in result['modules'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    audit_parser = sub.add_parser('audit')
    audit_parser.add_argument('--root', required=True)
    audit_parser.add_argument('--module', action='append', choices=MODULES)
    audit_parser.add_argument('--output', type=Path)
    for name in ('install', 'check', 'hook'):
        command = sub.add_parser(name)
        command.add_argument('--module', required=True, choices=MODULES)
        command.add_argument('--repo', required=True, type=Path)
        if name == 'check':
            command.add_argument('--phase', choices=('commit', 'push', 'deploy'), default='commit')
            command.add_argument('--deployed-sha')
        if name == 'hook':
            command.add_argument('--kind', required=True, choices=('pre-commit', 'pre-push'))
            command.add_argument('extra', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == 'audit':
        result = audit(args.root, args.module or list(MODULES))
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(text + '\n', encoding='utf-8')
        print(text)
        return 0 if all(row['status'] == 'verified-latest' for row in result['modules']) else 2
    if args.action == 'install':
        print(json.dumps(install(args.repo, args.module), ensure_ascii=False))
    elif args.action == 'hook':
        run_hook(args)
    else:
        latest = refresh(args.repo, args.module)
        check_candidate(args.repo, latest, args.phase, deployed=args.deployed_sha)
        print('Fresh repository identity/history check passed; this does not replace business release tests')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (GuardError, subprocess.TimeoutExpired) as error:
        print('OWNER-GIT-GUARD: ' + str(error), file=sys.stderr)
        sys.exit(1)
