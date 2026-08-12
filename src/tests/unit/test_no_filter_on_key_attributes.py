"""A DynamoDB FilterExpression may not reference primary key attributes.

Real DynamoDB rejects it outright:

    ValidationException: Filter Expression can only contain non-primary key
    attributes: Primary key attribute: SK

moto does NOT enforce this, so a query filtering on PK/SK/GSI1PK/GSI1SK passes
every moto-backed test and then 502s in production. That is exactly how
GetQuizResults and GetSentences shipped broken - both used
Attr('SK').contains(...) to separate quizzes from sentences, which share a key
range. The correct approach is to filter those in Python after the query.

This is a static check because the behaviour it guards cannot be reproduced with
the test double we use.
"""
import ast
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / 'src'

# Key attributes of the single table and its GSI, per template.yaml.
KEY_ATTRIBUTES = {'PK', 'SK', 'GSI1PK', 'GSI1SK'}


def _source_files():
    return [
        p for p in SRC.rglob('*.py')
        if 'tests' not in p.parts and p.name != '__init__.py'
    ]


def _string_constants(node):
    """Every string literal appearing anywhere under an AST node."""
    return {
        n.value for n in ast.walk(node)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }


def _filter_expression_violations(path):
    """Find FilterExpression=... arguments that mention a key attribute."""
    tree = ast.parse(path.read_text())
    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg != 'FilterExpression':
                continue
            offending = _string_constants(kw.value) & KEY_ATTRIBUTES
            if offending:
                violations.append((getattr(kw.value, 'lineno', node.lineno), sorted(offending)))

    # Also catch the dict form: query['FilterExpression'] = ...
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (isinstance(target, ast.Subscript)
                    and isinstance(target.slice, ast.Constant)
                    and target.slice.value == 'FilterExpression'):
                offending = _string_constants(node.value) & KEY_ATTRIBUTES
                if offending:
                    violations.append((node.lineno, sorted(offending)))

    return violations


SOURCE_FILES = _source_files()


def test_source_files_were_found():
    assert len(SOURCE_FILES) > 20


@pytest.mark.parametrize(
    'path', SOURCE_FILES, ids=[str(p.relative_to(REPO_ROOT)) for p in SOURCE_FILES]
)
def test_no_filter_expression_on_key_attributes(path):
    violations = _filter_expression_violations(path)

    assert not violations, (
        f"{path.relative_to(REPO_ROOT)} builds a FilterExpression referencing key "
        f"attribute(s) {violations}. DynamoDB rejects this with a ValidationException; "
        f"moto does not, so tests would pass and production would 502. "
        f"Filter on a non-key attribute, or filter in Python after the query."
    )
