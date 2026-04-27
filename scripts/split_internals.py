from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple


class Section(NamedTuple):
    number: str
    title: str
    slug: str
    lines: list[str]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def parse_sections(lines: list[str]) -> tuple[str, list[Section]]:
    title = ""
    sections: list[Section] = []
    current: Section | None = None

    section_re = re.compile(r"^##\s+(\d+)\.\s+(.*)$")

    for line in lines:
        if not title and line.startswith("# "):
            title = line.strip()
            continue

        match = section_re.match(line)
        if match:
            if current is not None:
                sections.append(current)

            number, heading = match.groups()
            slug = f"{int(number):02d}-{slugify(heading)}"
            current = Section(number=number, title=heading, slug=slug, lines=[line])
            continue

        if current is not None:
            current.lines.append(line)

    if current is not None:
        sections.append(current)

    if not title:
        raise ValueError("Could not find document title")

    return title, sections


def write_docs(source: Path, target_dir: Path) -> None:
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    title, sections = parse_sections(lines)

    target_dir.mkdir(parents=True, exist_ok=True)

    index_lines = [title, "", "---", "", "## Table of Contents", ""]
    for section in sections:
        link = f"{section.slug}.md"
        index_lines.append(f"{section.number}. [{section.title}]({link})")
    index_lines.append("")

    index_text = "\n".join(index_lines).rstrip() + "\n"
    (target_dir / "index.md").write_text(index_text, encoding="utf-8")

    for section in sections:
        path = target_dir / f"{section.slug}.md"
        path.write_text("\n".join(section.lines).rstrip() + "\n", encoding="utf-8")

    print(f"Wrote {len(sections)} section files to {target_dir}")
    print(f"Wrote table of contents to {target_dir / 'index.md'}")


def main() -> None:
    source = Path("demo_projects/multiplayerv2/INTERNALS.md")
    output = Path("docs/multiplayerv2_internals")
    write_docs(source, output)


if __name__ == "__main__":
    main()
