"""Every environment variable the code *requires* must be declared in template.yaml.

This guards a class of bug unit tests structurally cannot catch: conftest.py sets
env vars for the whole test process, so a handler reading os.environ['X'] passes
its tests whether or not template.yaml actually provisions X for that function.
The failure only appears at runtime, in AWS, as a KeyError.

That is exactly how VerifyAuthChallengeResponse shipped broken: it gained a
jwt.decode() call reading OTP_SECRET_KEY, but its template resource had no
Environment block at all, so every sign-in failed with
'VerifyAuthChallengeResponse failed with error OTP_SECRET_KEY'.

Only bracket access (os.environ['X']) is treated as required - os.environ.get('X')
has a fallback and cannot raise.
"""
import os
import re
import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TEMPLATE = REPO_ROOT / 'template.yaml'
LAYER_DIR = REPO_ROOT / 'src' / 'layer' / 'python'

# Provided by the Lambda runtime itself, never declared in a template.
# https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
RUNTIME_PROVIDED = {
    'AWS_REGION', 'AWS_DEFAULT_REGION', 'AWS_LAMBDA_FUNCTION_NAME',
    'AWS_LAMBDA_FUNCTION_VERSION', 'AWS_LAMBDA_FUNCTION_MEMORY_SIZE',
    'AWS_LAMBDA_LOG_GROUP_NAME', 'AWS_LAMBDA_LOG_STREAM_NAME',
    'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN',
    'LAMBDA_TASK_ROOT', 'LAMBDA_RUNTIME_DIR', 'TZ', '_HANDLER',
}

# os.environ['NAME'] / os.environ["NAME"] — bracket access only.
REQUIRED_ENV_RE = re.compile(r"""os\.environ\[\s*['"]([A-Z0-9_]+)['"]\s*\]""")
IMPORT_RE = re.compile(r'^\s*import\s+([a-z_][a-z0-9_]*)', re.MULTILINE)


class _CfnLoader(yaml.SafeLoader):
    """SafeLoader that tolerates CloudFormation intrinsic tags (!Ref, !Sub, ...)."""


_CfnLoader.add_multi_constructor('!', lambda loader, suffix, node: None)


def _layer_modules():
    return {p.stem: p for p in LAYER_DIR.glob('*.py') if p.stem != '__init__'}


def _required_env_in_file(path):
    return set(REQUIRED_ENV_RE.findall(path.read_text()))


def _required_env_for_source_dir(code_uri):
    """Env vars required by a function's own source plus the layer modules it imports.

    Layer imports are resolved transitively - user_service imports review_word_service,
    and both read TABLE_NAME.
    """
    src_dir = REPO_ROOT / code_uri
    layer = _layer_modules()

    required = set()
    seen_modules = set()
    pending = []

    for py in src_dir.rglob('*.py'):
        required |= _required_env_in_file(py)
        pending += [m for m in IMPORT_RE.findall(py.read_text()) if m in layer]

    while pending:
        module = pending.pop()
        if module in seen_modules:
            continue
        seen_modules.add(module)
        text = layer[module].read_text()
        required |= set(REQUIRED_ENV_RE.findall(text))
        pending += [m for m in IMPORT_RE.findall(text) if m in layer]

    return required - RUNTIME_PROVIDED


def _serverless_functions():
    template = yaml.load(TEMPLATE.read_text(), Loader=_CfnLoader)
    functions = []
    for name, resource in template['Resources'].items():
        if resource.get('Type') not in ('AWS::Serverless::Function', "'AWS::Serverless::Function'"):
            continue
        props = resource.get('Properties', {})
        code_uri = props.get('CodeUri')
        if not code_uri:
            continue
        declared = set((props.get('Environment') or {}).get('Variables', {}) or {})
        functions.append((name, code_uri, declared))
    return functions


FUNCTIONS = _serverless_functions()


def test_template_defines_serverless_functions():
    # Guard against the parsing above silently finding nothing.
    assert len(FUNCTIONS) >= 20


@pytest.mark.parametrize('name,code_uri,declared', FUNCTIONS, ids=[f[0] for f in FUNCTIONS])
def test_required_env_vars_are_declared(name, code_uri, declared):
    required = _required_env_for_source_dir(code_uri)
    missing = required - declared

    assert not missing, (
        f"{name} ({code_uri}) reads os.environ{sorted(missing)} but template.yaml "
        f"declares {sorted(declared) or 'no Environment.Variables'}. "
        f"This raises KeyError at runtime in AWS."
    )
