"""One reviewed scanner-authority transition; ordinary PRs remain frozen."""
import hashlib, json, os, subprocess

REPOSITORY = 'appolon1908/Codestra-TTS-Piper'
BASE = 'ee17de4a4615c7010aa3fc7c124e02bcccf597c8'
EXPECTED = {'.github/scripts/validate_source_scope.py': 'ffd79df3c33065a333f49dfbf88f513340e2c35bf3e3f062017d7bb4070484ee', '.github/source-scope.json': '0d1776bd1148640ddfaf9f81d438eca1515981b09fe71b0fe552d84a1bc6de1a', 'governance/interim-release-policy.json': '6fd3f1be5a580142d06fb7071fa65041041a3c6bd7ee787089ac890cef8cc379', '.github/scripts/test_source_scope.py': '19219d4715baaa55150ffa279bef50c1d16895aa7e5103f7d7853cebc9ae3f7f', '.github/scripts/test_secret_scanner.sh': '4d783f4f8ea40ec7acdbb94c4732f0ec2f9b320cea1e6a408a6702f08ee2d016'}
OLD_CONTEXT = 'frozen-vendor-documentation-source'
NEW_CONTEXT = 'frozen-vendor-documentation-source-v2'
EXTERNAL_REVIEW_FILES = {'.github/workflows/source-scope.yml', '.github/scripts/validate_scanner_upgrade.py'}

def trusted_manifest(base, repository):
    if base != BASE or repository != REPOSITORY:
        raise ValueError('Unregistered scanner authority transition')
    changes = subprocess.check_output(['git', 'diff', '--raw', '--no-abbrev', '--no-renames', base, 'HEAD']).decode().splitlines()
    changed = set()
    for entry in changes:
        metadata, path = entry.split('\t', 1)
        old_mode, new_mode, old_blob, new_blob, status = metadata[1:].split()
        if path not in set(EXPECTED) | EXTERNAL_REVIEW_FILES or new_mode != '100644' or status not in ('A', 'M'):
            raise ValueError('Unreviewed source, authority, mode or path change: ' + path)
        changed.add(path)
        if path in EXPECTED:
            content = subprocess.check_output(['git', 'show', 'HEAD:' + path])
            if hashlib.sha256(content).hexdigest() != EXPECTED[path]:
                raise ValueError('Reviewed scanner delta changed: ' + path)
    if changed != set(EXPECTED) | EXTERNAL_REVIEW_FILES:
        raise ValueError('Scanner upgrade delta incomplete')
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal']).strip():
        raise ValueError('Dirty or untracked scanner upgrade source')
    manifest = json.loads(subprocess.check_output(['git', 'show', base + ':.github/source-scope.json']))
    policy = manifest['structured_files']['governance/interim-release-policy.json']
    found = 0
    for check in policy['required_checks']:
        if check['context'] == OLD_CONTEXT:
            check['context'] = NEW_CONTEXT
            found += 1
    if found != 1:
        raise ValueError('Unexpected prior scope policy')
    return manifest

if __name__ == '__main__':
    trusted_manifest(os.environ['BASE_SHA'], os.environ['GITHUB_REPOSITORY'])
    print('Exact reviewed scanner-only authority transition PASS; product source unchanged')
