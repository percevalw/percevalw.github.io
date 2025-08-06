"""
To update the publications list, edit the references.bib file and run
`python scripts/generate_publications.py` at the root of the website
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import mkdocs.config
import mkdocs.structure.files
import mkdocs.structure.pages

log = logging.getLogger("generate_publications")


def _build_publications(bib_path: Path) -> str:
    """
    Parse bib_path and return the content of the markdown file with the list of publications
    """
    if not bib_path.is_file():
        log.warning("BibTeX file %s not found: skipping page generation", bib_path)
        return ""

    entries: list[dict] = []
    entry: dict | None = None
    raw_lines: list[str] = []

    with bib_path.open() as f:
        for line in f:
            if line.startswith("@"):
                entry_type, rest = line[1:].split("{", 1)
                key = rest.rstrip(",\n").strip()
                entry = {
                    "type": entry_type.strip(),
                    "key": key,
                    "fields": {},
                    "raw": "",
                }
                raw_lines = [line]
            elif entry is not None:
                raw_lines.append(line)
                if line.strip() == "}":
                    entry["raw"] = "".join(raw_lines).strip()
                    entries.append(entry)
                    entry = None
                else:
                    if "=" in line:
                        name, value = line.split("=", 1)
                        name = name.strip()
                        value = value.strip().strip(",").strip('{}"')
                        entry["fields"][name.lower()] = value

    lines = ["# Publications", ""]

    MONTH_NAMES = {
        "jan": "January",
        "feb": "February",
        "mar": "March",
        "apr": "April",
        "may": "May",
        "jun": "June",
        "jul": "July",
        "aug": "August",
        "sep": "September",
        "oct": "October",
        "nov": "November",
        "dec": "December",
    }

    def process_value(value: str) -> str:
        # replace brackets for accents
        value = value.replace("{\\'e}", "é")
        value = value.replace("{\\`a}", "à")
        value = value.replace('{\\"u}', "ü")
        value = value.replace("{\\'E}", "É")
        value = value.replace("{\\^o}", "ô")
        # remove LaTeX commands
        value = value.replace("{", "").replace("}", "")
        value = re.sub(r"\\[a-zA-Z]+", "", value)
        value = re.sub("\n\n+", "<br>", value)
        value = re.sub("\n", " ", value)
        return value

    new_entries = []
    for e in entries:
        f = e["fields"]
        f = {
            k.lower(): process_value(v) for k, v in f.items()
        }  # normalize keys to lowercase
        year = f.get("year", "")

        month_key = f.get("month", "").lower()[:3]
        month_key = (
            str(list(MONTH_NAMES.keys()).index(month_key) + 1).zfill(2)
            if month_key in MONTH_NAMES
            else ""
        )
        day = f.get("day", "")
        if month_key in MONTH_NAMES:
            month_name = MONTH_NAMES[month_key]
            date = f"{month_name} {day + ', ' if day else ''}{year}"
        else:
            date = year
        f["date"] = date
        f["_date"] = f"{year}-{month_key or '01'}-{day or '01'}"  # YYYY-MM-DD format
        new_entries.append(f)

    entries = new_entries

    first = True
    last_year = None
    for f in sorted(entries, key=lambda x: x.get("_date", ""), reverse=True):
        year = f.get("year", "")
        if not first:
            lines.append("---")
            # lines.append(f"{f['_date']}    ")
            lines.append("")
        if year != last_year:
            lines.append(f"## {year}")

        title = f.get("title", "").strip()
        authors = f.get("author", "")
        kind = f.get("type", "Article").lower()
        if kind == "theses" or kind == "thesis" or kind == "phdthesis":
            kind = "Thesis"
        else:
            kind = "Article"
        authors = ", ".join(
            [
                a.split(",")[1].strip() + " " + a.split(",")[0].strip()
                if "," in a
                else a.strip()
                for a in authors.split(" and ")
            ]
        )  # split by "and" and strip each author
        authors = authors.replace("Wajsburt", "Wajsbürt")
        authors = authors.replace("Perceval Wajsbürt", "<u>Perceval Wajsbürt</u>")
        date = f.get("date", "")

        url = f.get("url", "")
        if not url and "doi" in f:
            # If DOI is present, use it to construct the URL
            doi = f["doi"].strip()
            url = f"https://doi.org/{doi}" if doi else url
        arxiv_url = None
        if f.get("archiveprefix", "").lower() == "arxiv":
            arxiv_url = "https://arxiv.com/abs/" + f.get("eprint", "").strip()

        code_link = f.get("code")
        abstract = f.get("abstract", "")
        venue = f.get("journal") or f.get("booktitle", "")
        pub_type = e["type"].capitalize()

        lines.append(authors + "   ")

        lines.append(f"**{title}**" + "   ")

        # if abstract:
        #     lines.append(
        #         "<details style='margin: 0'><summary>Abstract</summary>"
        #         + html.escape(abstract)
        #         + "</details>"
        #     )

        # if venue:
        #     lines.append(f"*{venue}*" + "   ")

        link_parts: list[str] = []
        if url:
            link_parts.append(f'[{kind}]({url}){{ .button-link .blue-button }}')
        if arxiv_url:
            link_parts.append(f'[ArXiv]({arxiv_url}){{ .button-link .blue-button }}')
        if code_link:
            link_parts.append(f'[Code]({code_link}){{ .button-link .green-button }}')
        if link_parts:
            lines.append(" · ".join(link_parts))

        lines.append("")
        first = False
        last_year = year

    markdown = "\n".join(lines)
    log.info("📝  Built virtual publications page (%s entries)", len(entries))

    return markdown


if __name__ == "__main__":
    from pathlib import Path

    docs_dir = Path("docs")
    bib_path = docs_dir / "references.bib"
    content = _build_publications(bib_path)
    with open(docs_dir / "publications.md", "w") as f:
        f.write(content)
