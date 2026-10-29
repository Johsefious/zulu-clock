"""page_js.pick finds a function or const whatever its indent, so the page script can be re-indented without every
archive test breaking."""
import page_js

SAMPLE = {
    0: "function a() {\n  if (x) {\n    y();\n  }\n}\nfunction b() {}\n",
    2: "  function a() {\n    if (x) {\n      y();\n    }\n  }\n  function b() {}\n",
    4: "    async function a(p) {\n      if (x) {\n        y();\n      }\n    }\n    const k = 1;\n",
    '\t': "\tfunction a() {\n\t\tif (x) {\n\t\t\ty();\n\t\t}\n\t}\n\tfunction b() {}\n",
}


def test_pick_ends_a_function_at_its_own_closing_brace_at_any_indent(monkeypatch):
    for indent, js in SAMPLE.items():
        monkeypatch.setattr(page_js, 'source', lambda js=js: js)
        got = page_js.pick('a')
        assert got.count('{') == got.count('}') and 'y();' in got, repr(indent)
        assert 'function b' not in got and 'const k' not in got, repr(indent)


def test_pick_finds_a_const_at_any_indent(monkeypatch):
    monkeypatch.setattr(page_js, 'source', lambda: SAMPLE[4])
    assert page_js.pick('k') == '    const k = 1;\n'


def test_pick_leaves_out_an_optional_name_the_page_does_not_have(monkeypatch):
    monkeypatch.setattr(page_js, 'source', lambda: SAMPLE[0])
    assert page_js.pick('nope?') == ''
