from app.library_registry.frontmatter import parse_frontmatter


def test_parse_frontmatter_extracts_yaml_block() -> None:
    content = "---\nname: deploy\ndescription: Deploy the app\n---\nBody text.\n"

    result = parse_frontmatter(content)

    assert result == {"name": "deploy", "description": "Deploy the app"}


def test_parse_frontmatter_returns_empty_dict_when_no_frontmatter() -> None:
    result = parse_frontmatter("Just a plain markdown file.\n")

    assert result == {}


def test_parse_frontmatter_returns_empty_dict_when_yaml_is_not_a_mapping() -> None:
    content = "---\n- a\n- b\n---\nBody.\n"

    result = parse_frontmatter(content)

    assert result == {}


def test_parse_frontmatter_handles_list_field() -> None:
    content = "---\nname: foo\ntags: [a, b, c]\n---\n"

    result = parse_frontmatter(content)

    assert result["tags"] == ["a", "b", "c"]
