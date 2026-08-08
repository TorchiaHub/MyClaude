import re

import yaml

FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


def parse_frontmatter(content: str) -> dict:
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}
    data = yaml.safe_load(match.group(1))
    return data if isinstance(data, dict) else {}
