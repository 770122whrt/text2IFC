"""Frozen synthetic submission-envelope family; no model or formal IFC results.

The native instruction asks for one JSON declaration in the final response,
not JSON-only text. The supported prose envelope is a single top-level JSON
fence at the end; quoted, illustrative and ambiguous envelopes fail closed.
"""
import json

import pytest

from scripts.ifc_repair.repair_comparison.isolated_dsh import submitted_path


DECLARATION = '{"submitted_ifc":"output/repaired.ifc"}'
FENCE = '```json\n' + DECLARATION + '\n```'


@pytest.mark.parametrize(('response', 'expected'), [
    pytest.param(DECLARATION, 'output/repaired.ifc', id='legacy-plain-json'),
    pytest.param(FENCE, 'output/repaired.ifc', id='legacy-whole-fence'),
    pytest.param('  \n' + DECLARATION + '\n ', 'output/repaired.ifc', id='legacy-outer-whitespace'),
    pytest.param('Repair complete.\n\n' + FENCE, 'output/repaired.ifc', id='explanation-final-fence'),
    pytest.param('已完成。\n\n- 已保存输出。\n- 已重新打开 IFC。\n\n' + FENCE,
                 'output/repaired.ifc', id='chinese-explanation-final-fence'),
    pytest.param('## Result\nThe file `output/repaired.ifc` is ready.\n\n' + FENCE,
                 'output/repaired.ifc', id='markdown-prose-with-inline-filename'),
    pytest.param(('Completed.\n\n' + FENCE).replace('\n', '\r\n'),
                 'output/repaired.ifc', id='crlf-envelope'),
    pytest.param('Complete.\n\n```json\n{\n "submitted_ifc": "output/修复 门.IFC"\n}\n```\n',
                 'output/修复 门.IFC', id='sibling-multiline-unicode-spaces'),
    pytest.param('{"submitted_ifc":"model.ifc"}', 'model.ifc', id='root-relative-file'),
])
def test_one_explicit_submission_is_received(response, expected):
    assert submitted_path(response) == expected


def rejected(response):
    """Both no declaration and an explicit contract error prevent publication."""
    try:
        value = submitted_path(response)
    except ValueError:
        return
    assert value is None


@pytest.mark.parametrize('response', [
    pytest.param('', id='empty'),
    pytest.param('I wrote output/repaired.ifc.', id='filename-is-not-declaration'),
    pytest.param('The final IFC is in the output directory.', id='no-directory-discovery'),
    pytest.param(FENCE + '\n\n' + FENCE, id='two-identical-fenced-declarations'),
    pytest.param(FENCE + '\n\n' + FENCE.replace('repaired', 'other'), id='two-distinct-fenced-declarations'),
    pytest.param(DECLARATION + '\n' + FENCE, id='plain-then-fenced-declaration'),
    pytest.param(FENCE + '\n' + DECLARATION, id='fenced-then-plain-declaration'),
    pytest.param(DECLARATION + '\n' + DECLARATION, id='two-plain-declarations'),
    pytest.param('{"submitted_ifc":"one.ifc","submitted_ifc":"two.ifc"}', id='duplicate-key-distinct'),
    pytest.param('{"submitted_ifc":"one.ifc","submitted_ifc":"one.ifc"}', id='duplicate-key-identical'),
    pytest.param('{"submitted_ifc":"one.ifc","submitted_\\u0069fc":"two.ifc"}', id='escaped-duplicate-key'),
    pytest.param('Complete.\n```json\n{"submitted_ifc":"one.ifc","submitted_ifc":"two.ifc"}\n```',
                 id='enveloped-duplicate-key'),
    pytest.param('Earlier: {"submitted_\\u0069fc":"one.ifc"}\n' + FENCE, id='escaped-earlier-declaration'),
    pytest.param('Earlier `submitted_ifc` was one.ifc.\n' + FENCE, id='earlier-declaration-marker'),
    pytest.param('```python\nprint("done")\n```\n' + FENCE, id='another-code-fence'),
    pytest.param('~~~~\n' + FENCE + '\n~~~~', id='nested-markdown-fence'),
    pytest.param('> ' + FENCE.replace('\n', '\n> '), id='quoted-fence'),
    pytest.param('> A quoted response:\n\n' + FENCE, id='blockquote-introduces-fence'),
    pytest.param('"' + FENCE + '"', id='quoted-whole-envelope'),
    pytest.param(json.dumps({'message': DECLARATION}), id='json-string-nested-declaration'),
    pytest.param(json.dumps({'result': {'submitted_ifc': 'one.ifc'}}), id='nested-object-not-declaration'),
    pytest.param(json.dumps([{'submitted_ifc': 'one.ifc'}]), id='array-not-declaration'),
    pytest.param(json.dumps(DECLARATION), id='encoded-json-string'),
    pytest.param('Complete.\n' + FENCE + '\nThis is the file.', id='trailing-prose-not-final-block'),
    pytest.param('Complete. ' + FENCE, id='inline-not-top-level-fence'),
    pytest.param('Complete.\n  ' + FENCE.replace('\n', '\n  '), id='indented-code-example'),
    pytest.param('Complete.\n```json\n' + DECLARATION, id='truncated-fence'),
    pytest.param('Complete.\n```json\n{"submitted_ifc":"one.ifc"\n```', id='truncated-object'),
    pytest.param('Complete.\n```json\n' + DECLARATION + ',\n```', id='malformed-json'),
    pytest.param('Complete.\n```python\n' + DECLARATION + '\n```', id='wrong-fence-language'),
    pytest.param('Complete.\n```\n' + DECLARATION + '\n```', id='missing-json-fence-label'),
    pytest.param('Complete.\n```json\n' + DECLARATION + '\n' + DECLARATION + '\n```', id='two-json-in-one-fence'),
    pytest.param('Complete.\n```json\n{"submitted_ifc":"one.ifc","note":"ready"}\n```', id='extra-envelope-key'),
    pytest.param('{"submitted_ifc":"one.ifc","other":"two.ifc"}', id='legacy-extra-key'),
    pytest.param('{"submitted_ifc":{"path":"one.ifc"}}', id='nested-path-object'),
    pytest.param('{"submitted_ifc":["one.ifc"]}', id='path-array'),
    pytest.param('{"submitted_ifc":null}', id='null-path'),
    pytest.param('{"submitted_ifc":17}', id='numeric-path'),
])
def test_ambiguous_malformed_or_nested_envelopes_are_rejected(response):
    rejected(response)


@pytest.mark.parametrize('response', [
    pytest.param(FENCE + '\n\n' + FENCE, id='same-path-twice'),
    pytest.param(FENCE + '\n\n' + FENCE.replace('repaired', 'other'), id='different-paths'),
    pytest.param('First result:\n' + FENCE + '\n\nSecond result:\n' + FENCE,
                 id='prose-between-declarations'),
    pytest.param(FENCE + '\n\n' + FENCE + '\n\n' + FENCE, id='three-declarations'),
])
def test_multiple_explicit_fenced_declarations_are_contract_errors(response):
    with pytest.raises(ValueError, match='^ONE_EXPLICIT_IFC_REQUIRED$'):
        submitted_path(response)


def test_unrelated_code_fence_is_no_declaration_not_contract_error():
    assert submitted_path('```python\nprint("done")\n```\n' + FENCE) is None


@pytest.mark.parametrize('prefix', [
    'Example:', 'For example, return:', 'Sample output:', 'Illustration:',
    'Quoted response:', 'This is a quotation:', 'Template:',
    'Do not submit this:', 'This is not a submission:',
    '示例：', '例如：', '样例输出：', '引用回复：', '仅供参考：',
    '提交格式模板：', '不要提交以下内容：', '尚未提交：',
    '<blockquote>', '<!-- quoted material -->',
])
def test_marked_examples_and_quotes_are_not_submissions(prefix):
    rejected(prefix + '\n\n' + FENCE)


@pytest.mark.parametrize('path', [
    '../outside.ifc', 'output/../../outside.ifc', '/state/model.ifc',
    '//host/share/model.ifc', 'C:/model.ifc', 'C:model.ifc',
    'output\\model.ifc', 'https://example.invalid/model.ifc',
    'output/./model.ifc', './model.ifc', '', 'output/model.txt',
    'output/nu\x00l.ifc', 'output/new\nline.ifc', 'output/tab\tname.ifc',
    'output/delete\x7f.ifc', 'output//model.ifc',
    ' output/model.ifc', 'output/model.ifc ',
])
@pytest.mark.parametrize('enveloped', [False, True], ids=['plain', 'prose-fence'])
def test_invalid_or_out_of_workspace_paths_are_never_received(path, enveloped):
    body = json.dumps({'submitted_ifc': path})
    response = 'Complete.\n```json\n' + body + '\n```' if enveloped else body
    rejected(response)
