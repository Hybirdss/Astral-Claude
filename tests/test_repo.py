"""Repository hygiene: links, versions, skill frontmatter, manifests, no machine-specific paths."""

import json
import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "artifacts"}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# Built from pieces so this file does not match its own pattern.
PERSONAL_PATH = re.compile(
    "(/" + "home/[A-Za-z0-9_.-]+|/" + "Users/[A-Za-z0-9_.-]+|[A-Za-z]:\\\\Users\\\\)"
)


def tracked_files(*suffixes):
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT).parts
        if any(part in SKIP for part in relative):
            continue
        if path.is_file() and path.suffix in suffixes:
            yield path


def test_markdown_links_resolve():
    broken = []
    for md in tracked_files(".md"):
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if not (md.parent / target.split("#")[0]).resolve().exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    assert not broken, broken


def test_versions_agree_everywhere():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert plugin["version"] == version
    assert f"## [{version}]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    assert re.search(rf'name = "astral-claude"\nversion = "{re.escape(version)}"', lock)


def test_skill_frontmatter_is_valid():
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert len(skills) >= 4
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---\n"), skill
        meta = yaml.safe_load(text.split("---\n", 2)[1])
        assert meta["name"] == skill.parent.name, skill
        description = meta["description"].strip()
        assert description and "\n" not in description, skill
        assert len(description) + len(meta.get("when_to_use", "")) <= 1536, skill


def test_manifests_and_readme_agree():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    servers = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    assert marketplace["plugins"][0]["name"] == plugin["name"]
    assert set(servers) == {"astral-desktop", "blender"}
    assert "${CLAUDE_PLUGIN_ROOT}" in servers["astral-desktop"]["args"]
    assert any(arg.startswith("blender-mcp==") for arg in servers["blender"]["args"])
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for skill in sorted((ROOT / "skills").iterdir()):
        assert f"skills/{skill.name}/SKILL.md" in readme, skill


def test_no_machine_specific_paths_in_tracked_text():
    hits = []
    for path in tracked_files(".md", ".py", ".json", ".toml", ".yml", ".yaml", ".cff", ".txt"):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for number, line in enumerate(lines, 1):
            if PERSONAL_PATH.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:80]}")
    assert not hits, hits
