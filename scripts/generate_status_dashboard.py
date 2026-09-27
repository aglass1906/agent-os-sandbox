#!/usr/bin/env python3
"""Generate docs/status-dashboard.html directly from canonical roadmap documents.

Scans docs/roadmap/epic-*/ to parse parent EPIC-*.md plans and stories/STORY-*.md
specifications as the primary source of truth. Fills the __AS_OF_DATE__ and
__DATA_JSON__ placeholders in docs/status-dashboard.template.html to produce
docs/status-dashboard.html.

Also detects drift against docs/STATUS.md and supports --sync to reconcile
docs/STATUS.md with the canonical story documents on disk.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKLOG_DIR = REPO_ROOT / "docs" / "backlog"
ROADMAP_DIR = BACKLOG_DIR if BACKLOG_DIR.exists() else (REPO_ROOT / "docs" / "roadmap")
STATUS_MD = REPO_ROOT / "docs" / "STATUS.md"
TEMPLATE_HTML = REPO_ROOT / "docs" / "status-dashboard.template.html"
OUTPUT_HTML = REPO_ROOT / "docs" / "status-dashboard.html"

NOTE_MAX_LEN = 140


def _esc(text: str) -> str:
    """Minimal HTML-escaping for values the template inserts via innerHTML."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def extract_frontmatter(content: str) -> dict[str, str]:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_text = parts[1]
    data: dict[str, str] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip("\"'")
    return data


def parse_epic_summary(content: str) -> str:
    m_sec1 = re.search(
        r"## 1\.\s+(?:Executive Summary\s*(?:&|and)\s*Goal|Goal|Executive Summary)\s*\n+(.*?)(?=\n##|\Z)",
        content,
        re.DOTALL,
    )
    if m_sec1:
        sec1_text = m_sec1.group(1).strip()
        paras = [
            p.strip()
            for p in sec1_text.split("\n\n")
            if p.strip() and not p.strip().startswith(">")
        ]
        if paras:
            first_p = re.sub(r"\s+", " ", paras[0])
            first_p = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", first_p)
            first_p = first_p.replace("*", "").replace("`", "")
            if len(first_p) > NOTE_MAX_LEN:
                return first_p[:NOTE_MAX_LEN].rstrip() + "…"
            return first_p
    m_bq = re.search(r"^>\s+(.*?)$", content, re.MULTILINE)
    if m_bq:
        bq = m_bq.group(1).strip()
        if not bq.startswith("**Status") and not bq.startswith("Status:"):
            if len(bq) > NOTE_MAX_LEN:
                return bq[:NOTE_MAX_LEN].rstrip() + "…"
            return bq
    return ""


def parse_roadmap_documents() -> list[dict]:
    epic_dirs = sorted(
        [d for d in ROADMAP_DIR.iterdir() if d.is_dir() and d.name.startswith("epic-")],
        key=lambda d: int(re.search(r"epic-(\d+)", d.name).group(1)),
    )

    epics_data: list[dict] = []
    for ed in epic_dirs:
        m = re.search(r"epic-(\d+)", ed.name)
        if not m:
            continue
        epic_id = m.group(1)
        plan_files = list(ed.glob("EPIC-*.md"))
        if not plan_files:
            continue
        plan_file = plan_files[0]
        p_content = plan_file.read_text(encoding="utf-8")
        p_fm = extract_frontmatter(p_content)

        title = p_fm.get("title")
        if not title:
            tm = re.search(r"^#\s+Epic\s+\d+\s+—\s+(.*?)$", p_content, re.MULTILINE)
            title = (
                tm.group(1).strip()
                if tm
                else ed.name.replace("epic-" + epic_id + "-", "")
                .replace("-", " ")
                .title()
            )

        note = parse_epic_summary(p_content)

        stories_dir = ed / "stories"
        story_files = []
        if stories_dir.exists():
            story_files = sorted(
                list(stories_dir.glob("STORY-*.md")),
                key=lambda f: [
                    int(x)
                    for x in re.search(r"STORY-(\d+)\.(\d+)", f.name).groups()
                ]
                if re.search(r"STORY-(\d+)\.(\d+)", f.name)
                else [999, 999],
            )

        stories_data: list[dict] = []
        for sf in story_files:
            s_content = sf.read_text(encoding="utf-8")
            s_fm = extract_frontmatter(s_content)
            s_title = s_fm.get("title")
            if not s_title:
                stm = re.search(
                    r"^#\s+Story\s+[0-9.]+\s+—\s+(.*?)$", s_content, re.MULTILINE
                )
                s_title = stm.group(1).strip() if stm else sf.stem

            s_status = s_fm.get("status", "planned").lower()
            done = s_status == "completed"

            s_id_m = re.search(r"STORY-([0-9.]+)", sf.name)
            s_id = s_id_m.group(1) if s_id_m else ""

            rel_link = sf.relative_to(REPO_ROOT / "docs").as_posix()
            story_html = f'<code>Story {s_id}</code> <a href="{rel_link}" target="_blank" style="color:inherit;text-decoration:none;">{_esc(s_title)}</a>'
            stories_data.append(
                {
                    "id": s_id,
                    "title": s_title,
                    "status": s_status,
                    "done": done,
                    "t": story_html,
                    "rel_link": rel_link,
                    "file_path": sf,
                    "path": sf.relative_to(REPO_ROOT).as_posix(),
                    "content": s_content,
                }
            )

        p_status = p_fm.get("status", "").lower()
        if p_status == "completed":
            calc_status = "done"
        elif p_status == "in_progress":
            calc_status = "progress"
        elif p_status == "planned":
            calc_status = "planned"
        else:
            if not stories_data:
                calc_status = "planned"
            elif all(s["done"] for s in stories_data):
                calc_status = "done"
            elif any(s["done"] for s in stories_data):
                calc_status = "progress"
            else:
                calc_status = "planned"

        epics_data.append(
            {
                "id": epic_id,
                "name": _esc(title),
                "status": calc_status,
                "note": _esc(note) if note else None,
                "stories": stories_data,
                "plan_file": plan_file,
                "plan_rel_link": plan_file.relative_to(REPO_ROOT / "docs").as_posix(),
                "plan_path": plan_file.relative_to(REPO_ROOT).as_posix(),
                "plan_content": p_content,
            }
        )

    return epics_data


def detect_drift(epics_data: list[dict], status_text: str) -> list[str]:
    discrepancies: list[str] = []

    # Map stories in STATUS.md
    status_stories: dict[str, dict] = {}
    for m in re.finditer(
        r"-\s\[([ xX])\]\s+\[?\*\*Story\s+([0-9]+(?:\.[0-9]+)?)\*\*\]?(?:\((.*?)\))?:\s*(.*)",
        status_text,
    ):
        done = m.group(1).lower() == "x"
        story_id = m.group(2)
        link = m.group(3) or ""
        title = m.group(4).strip()
        status_stories[story_id] = {"done": done, "link": link, "title": title}

    disk_stories: dict[str, dict] = {}
    for ep in epics_data:
        for s in ep["stories"]:
            disk_stories[s["id"]] = s

    for s_id, s in disk_stories.items():
        if s_id not in status_stories:
            discrepancies.append(
                f"Story {s_id} ({s['title']}) exists on disk but is missing in docs/STATUS.md"
            )
        else:
            st = status_stories[s_id]
            if s["done"] != st["done"]:
                state_disk = "completed" if s["done"] else "planned/in_progress"
                state_doc = "checked [x]" if st["done"] else "unchecked [ ]"
                discrepancies.append(
                    f"Story {s_id} completion mismatch: disk is {state_disk}, STATUS.md has {state_doc}"
                )

    return discrepancies


def sync_status_md(epics_data: list[dict]) -> None:
    content = STATUS_MD.read_text(encoding="utf-8")

    for ep in epics_data:
        epic_id = ep["id"]
        stories = ep["stories"]
        if not stories:
            continue

        # Look for the section header ## Epic <id> —
        pattern = re.compile(
            rf"(##\s+Epic\s+{re.escape(epic_id)}\s+—\s+[^\n]+\n+)(?:(>[^\n]+\n+)?)(?:(?:\s*-\s*\[[ xX]\].*?\n+)*)",
            re.MULTILINE,
        )
        match = pattern.search(content)
        if not match:
            continue

        header_part = match.group(1)
        note_part = match.group(2) or ""

        # Build clean checklist from disk stories
        new_checklist_lines = []
        for s in stories:
            box = "[x]" if s["done"] else "[ ]"
            rel_link = f"./{s['rel_link']}"
            new_checklist_lines.append(
                f"- {box} [**Story {s['id']}**]({rel_link}): {s['title']}"
            )
        new_checklist = "\n".join(new_checklist_lines) + "\n\n"

        replacement = f"{header_part}{note_part}{new_checklist}"
        content = content[: match.start()] + replacement + content[match.end() :]

    STATUS_MD.write_text(content, encoding="utf-8")
    print(f"Synchronized {STATUS_MD.relative_to(REPO_ROOT)} with disk specifications.")


def status_md_as_of_date() -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short", "--", str(ROADMAP_DIR)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        date = result.stdout.strip()
        if date:
            return date
    except Exception:
        pass
    import datetime
    return datetime.date.today().isoformat()



def generate(epics_data: list[dict]) -> str:
    template = TEMPLATE_HTML.read_text(encoding="utf-8")
    as_of_date = status_md_as_of_date()

    clean_data = []
    for ep in epics_data:
        item: dict = {
            "id": ep["id"],
            "name": ep["name"],
            "status": ep["status"],
            "plan_rel_link": ep["plan_rel_link"],
            "plan_path": ep["plan_path"],
            "plan_content": ep["plan_content"],
        }
        if ep.get("note"):
            item["note"] = ep["note"]
        if ep.get("stories"):
            item["stories"] = [
                {
                    "id": s["id"],
                    "title": s["title"],
                    "status": s["status"],
                    "done": s["done"],
                    "t": s["t"],
                    "rel_link": s["rel_link"],
                    "path": s["path"],
                    "content": s["content"],
                }
                for s in ep["stories"]
            ]
        clean_data.append(item)

    data_json = json.dumps(clean_data, sort_keys=False, ensure_ascii=False)
    html = template.replace("__AS_OF_DATE__", as_of_date).replace(
        "__DATA_JSON__", data_json
    )
    return html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate docs/status-dashboard.html from roadmap documents and reconcile docs/STATUS.md."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Reconcile docs/STATUS.md with the canonical story documents on disk.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for drift between disk and docs/STATUS.md, returning non-zero if drift exists.",
    )
    args = parser.parse_args()

    epics_data = parse_roadmap_documents()
    status_text = STATUS_MD.read_text(encoding="utf-8")
    discrepancies = detect_drift(epics_data, status_text)

    if args.check_only:
        if discrepancies:
            print(f"Drift detected ({len(discrepancies)} discrepancies):")
            for d in discrepancies:
                print(f"  - {d}")
            return 1
        print("Zero drift detected: docs/STATUS.md matches disk specifications.")
        return 0

    if args.sync:
        sync_status_md(epics_data)
        # re-read after sync
        status_text = STATUS_MD.read_text(encoding="utf-8")
        discrepancies = detect_drift(epics_data, status_text)

    html = generate(epics_data)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    total_stories = sum(len(ep["stories"]) for ep in epics_data)
    done_stories = sum(
        sum(1 for s in ep["stories"] if s["done"]) for ep in epics_data
    )
    print(
        f"Wrote {OUTPUT_HTML.relative_to(REPO_ROOT)} from {len(epics_data)} epics and {total_stories} stories ({done_stories} completed)."
    )

    if discrepancies and not args.sync:
        print(
            f"Notice: {len(discrepancies)} discrepancies between disk and {STATUS_MD.relative_to(REPO_ROOT)}. Run 'make sync-status' to synchronize."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
