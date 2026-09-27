#!/usr/bin/env python3
"""Generate docs/status-dashboard.html directly from canonical repository documentation.

Scans:
1. docs/backlog/ (or docs/roadmap/): Parent EPIC-*.md plans and stories/STORY-*.md specifications
2. docs/product/: Product Requirements Documents (PRD-*.md)
3. docs/design-specs/: Feature and UX Design Specifications (*.md)
4. docs/adr/: Architecture Decision Records (*.md)

Fills __AS_OF_DATE__ and __DATA_JSON__ placeholders in docs/status-dashboard.template.html
to produce docs/status-dashboard.html.

Also detects drift against docs/STATUS.md and supports --sync to reconcile
docs/STATUS.md with the canonical story documents on disk.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKLOG_DIR = REPO_ROOT / "docs" / "backlog"
ROADMAP_DIR = BACKLOG_DIR if BACKLOG_DIR.exists() else (REPO_ROOT / "docs" / "roadmap")
PRODUCT_DIR = REPO_ROOT / "docs" / "product"
DESIGN_SPECS_DIR = REPO_ROOT / "docs" / "design-specs"
ADR_DIR = REPO_ROOT / "docs" / "adr"
STATUS_MD = REPO_ROOT / "docs" / "STATUS.md"
TEMPLATES_DIR = REPO_ROOT / "docs" / "templates"
TEMPLATE_HTML = REPO_ROOT / "docs" / "status-dashboard.template.html"
OUTPUT_HTML = REPO_ROOT / "docs" / "status-dashboard.html"

NOTE_MAX_LEN = 140
SUMMARY_MAX_LEN = 220


def _esc(text: str) -> str:
    """Minimal HTML-escaping for values the template inserts via innerHTML."""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def extract_frontmatter(content: str) -> dict[str, any]:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_text = parts[1]
    data: dict[str, any] = {}
    current_list_key = None
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- ") and current_list_key:
            item = line[2:].strip().strip("\"'")
            if isinstance(data.get(current_list_key), list):
                data[current_list_key].append(item)
            else:
                data[current_list_key] = [item]
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip("\"'")
            if not v:
                current_list_key = k
                data[k] = []
            else:
                current_list_key = None
                data[k] = v
        else:
            current_list_key = None
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


def parse_roadmap_documents(
    design_specs_data: list[dict] | None = None,
    adrs_data: list[dict] | None = None,
) -> list[dict]:
    if not ROADMAP_DIR.exists():
        return []
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

        # Cross-reference associated design specification
        associated_design_spec = None
        ds_val = p_fm.get("design_spec")
        if design_specs_data:
            if ds_val and isinstance(ds_val, str) and ds_val.strip():
                ds_clean = ds_val.strip()
                for ds in design_specs_data:
                    if (
                        ds["path"] == ds_clean
                        or ds["rel_link"] == ds_clean
                        or ds_clean.endswith("/" + Path(ds["path"]).name)
                        or ds_clean == Path(ds["path"]).name
                    ):
                        associated_design_spec = {
                            "id": ds["id"],
                            "title": ds["title"],
                            "status": ds["status"],
                            "rel_link": ds["rel_link"],
                            "path": ds["path"],
                            "content": ds["content"],
                        }
                        break
            if not associated_design_spec:
                # Fallback: match by epic_id declared in design spec frontmatter
                for ds in design_specs_data:
                    ds_epic = str(ds.get("epic_id", "")).strip().upper()
                    if ds_epic in (f"EPIC-{epic_id}", epic_id, f"EPIC {epic_id}"):
                        associated_design_spec = {
                            "id": ds["id"],
                            "title": ds["title"],
                            "status": ds["status"],
                            "rel_link": ds["rel_link"],
                            "path": ds["path"],
                            "content": ds["content"],
                        }
                        break

        # Cross-reference associated ADRs
        associated_adrs = []
        if adrs_data:
            adr_list = p_fm.get("adrs", [])
            if isinstance(adr_list, str):
                adr_list = [adr_list]
            for adr_path in adr_list:
                adr_clean = str(adr_path).strip()
                for adr in adrs_data:
                    if (
                        adr["path"] == adr_clean
                        or adr["rel_link"] == adr_clean
                        or adr_clean.endswith("/" + Path(adr["path"]).name)
                        or adr_clean == Path(adr["path"]).name
                    ):
                        associated_adrs.append(
                            {
                                "id": adr["id"],
                                "number": adr["number"],
                                "title": adr["title"],
                                "status": adr["status"],
                                "rel_link": adr["rel_link"],
                                "path": adr["path"],
                                "content": adr["content"],
                            }
                        )
                        break
            for adr in adrs_data:
                adr_epic = str(adr.get("epic_id", "")).strip().upper()
                if adr_epic in (f"EPIC-{epic_id}", epic_id, f"EPIC {epic_id}"):
                    if not any(a["id"] == adr["id"] for a in associated_adrs):
                        associated_adrs.append(
                            {
                                "id": adr["id"],
                                "number": adr["number"],
                                "title": adr["title"],
                                "status": adr["status"],
                                "rel_link": adr["rel_link"],
                                "path": adr["path"],
                                "content": adr["content"],
                            }
                        )

        plan_rel = plan_file.relative_to(REPO_ROOT / "docs").as_posix()
        plan_p = plan_file.relative_to(REPO_ROOT).as_posix()

        # Back-link parent_epic onto design spec and ADR records
        if associated_design_spec and design_specs_data:
            for ds in design_specs_data:
                if ds["id"] == associated_design_spec["id"]:
                    ds["parent_epic"] = {
                        "id": epic_id,
                        "name": title,
                        "status": calc_status,
                        "plan_rel_link": plan_rel,
                        "plan_path": plan_p,
                        "plan_content": p_content,
                        "adrs": [
                            {
                                "id": a["id"],
                                "number": a["number"],
                                "title": a["title"],
                                "status": a["status"],
                                "rel_link": a["rel_link"],
                                "path": a["path"],
                                "content": a["content"],
                            }
                            for a in associated_adrs
                        ],
                    }
        for a in associated_adrs:
            for adr in adrs_data:
                if adr["id"] == a["id"]:
                    adr["parent_epic"] = {
                        "id": epic_id,
                        "name": title,
                        "status": calc_status,
                        "plan_rel_link": plan_rel,
                        "plan_path": plan_p,
                        "plan_content": p_content,
                        "design_spec": (
                            {
                                "id": associated_design_spec["id"],
                                "title": associated_design_spec["title"],
                                "status": associated_design_spec["status"],
                                "rel_link": associated_design_spec["rel_link"],
                                "path": associated_design_spec["path"],
                                "content": associated_design_spec["content"],
                            }
                            if associated_design_spec
                            else None
                        ),
                    }

        epics_data.append(
            {
                "id": epic_id,
                "name": _esc(title),
                "status": calc_status,
                "note": _esc(note) if note else None,
                "stories": stories_data,
                "plan_rel_link": plan_rel,
                "plan_path": plan_p,
                "plan_content": p_content,
                "design_spec": associated_design_spec,
                "adrs": associated_adrs,
            }
        )

    return epics_data


def parse_product_documents() -> list[dict]:
    if not PRODUCT_DIR.exists():
        return []
    prd_files = sorted(
        [f for f in PRODUCT_DIR.glob("*.md") if f.name != "README.md"],
        key=lambda f: f.name,
    )
    prds: list[dict] = []
    for pf in prd_files:
        content = pf.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)
        title = fm.get("title")
        if not title:
            m = re.search(
                r"^#\s+(?:Product Requirements Document \(PRD\)\s*—\s*|PRD\s*—\s*)?(.*?)$",
                content,
                re.MULTILINE,
            )
            title = m.group(1).strip() if m else pf.stem

        status = fm.get("status", "draft").lower()
        owner = fm.get("owner", "")
        target_epic = fm.get("target_epic", "")

        summary = ""
        m_sec = re.search(
            r"## 1\.\s+(?:Executive Summary\s*(?:&|and)\s*Problem Statement|Executive Summary|Problem Statement)\s*\n+(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL,
        )
        if m_sec:
            paras = [
                p.strip()
                for p in m_sec.group(1).split("\n\n")
                if p.strip() and not p.strip().startswith(">") and not p.strip().startswith("#")
            ]
            if paras:
                summary = re.sub(r"\s+", " ", paras[0])
                summary = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", summary).replace("*", "").replace("`", "")
                if len(summary) > SUMMARY_MAX_LEN:
                    summary = summary[:SUMMARY_MAX_LEN].rstrip() + "…"
        if not summary:
            m_bq = re.search(r"^>\s+(.*?)$", content, re.MULTILINE)
            if m_bq and not m_bq.group(1).strip().startswith("**Status"):
                summary = m_bq.group(1).strip()[:SUMMARY_MAX_LEN]

        prds.append(
            {
                "id": fm.get("id", pf.stem),
                "title": title,
                "status": status,
                "owner": owner,
                "target_epic": target_epic,
                "summary": summary,
                "rel_link": pf.relative_to(REPO_ROOT / "docs").as_posix(),
                "path": pf.relative_to(REPO_ROOT).as_posix(),
                "content": content,
            }
        )
    return prds


def parse_design_specs() -> list[dict]:
    if not DESIGN_SPECS_DIR.exists():
        return []
    spec_files = sorted(
        [f for f in DESIGN_SPECS_DIR.glob("*.md") if f.name != "README.md"],
        key=lambda f: f.name,
    )
    specs: list[dict] = []
    for sf in spec_files:
        content = sf.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)
        title = fm.get("title")
        if not title:
            m = re.search(
                r"^#\s+(?:Feature Design Spec\s*—\s*|Technical Design Document\s*—\s*|Design Specification\s*—\s*)?(.*?)$",
                content,
                re.MULTILINE,
            )
            title = m.group(1).strip() if m else sf.stem.replace("-", " ").title()

        status = fm.get("status", "living").lower()
        category = fm.get("category", "Design Spec")
        surfaces = fm.get("surfaces", "")
        epic_id = fm.get("epic_id", "")

        summary = ""
        m_sec = re.search(
            r"## 1\.\s+(?:Executive Summary\s*(?:&|and)\s*Architecture|Executive Summary|Problem Framing)\s*\n+(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL,
        )
        if m_sec:
            paras = [
                p.strip()
                for p in m_sec.group(1).split("\n\n")
                if p.strip() and not p.strip().startswith(">") and not p.strip().startswith("#") and not p.strip().startswith("```")
            ]
            if paras:
                summary = re.sub(r"\s+", " ", paras[0])
                summary = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", summary).replace("*", "").replace("`", "")
                if len(summary) > SUMMARY_MAX_LEN:
                    summary = summary[:SUMMARY_MAX_LEN].rstrip() + "…"
        if not summary:
            paras = [
                p.strip()
                for p in content.split("\n\n")
                if p.strip() and not p.strip().startswith("#") and not p.strip().startswith(">") and not p.strip().startswith("---")
            ]
            if paras:
                first_clean = re.sub(r"\s+", " ", paras[0])
                first_clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", first_clean).replace("*", "").replace("`", "")
                summary = first_clean[:SUMMARY_MAX_LEN].rstrip() + "…"

        specs.append(
            {
                "id": fm.get("id", sf.stem),
                "title": title,
                "status": status,
                "category": category,
                "surfaces": surfaces,
                "epic_id": epic_id,
                "summary": summary,
                "rel_link": sf.relative_to(REPO_ROOT / "docs").as_posix(),
                "path": sf.relative_to(REPO_ROOT).as_posix(),
                "content": content,
            }
        )
    return specs


def parse_adr_documents() -> list[dict]:
    if not ADR_DIR.exists():
        return []
    adr_files = sorted(
        [f for f in ADR_DIR.glob("*.md") if f.name != "README.md"],
        key=lambda f: f.name,
    )
    adrs: list[dict] = []
    for af in adr_files:
        content = af.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)

        num_m = re.search(r"^(\d+)", af.stem)
        num_str = num_m.group(1) if num_m else "0000"

        title = fm.get("title")
        if not title:
            m = re.search(r"^#\s+(?:ADR\s+\d+:\s*)?(.*?)$", content, re.MULTILINE)
            title = m.group(1).strip() if m else af.stem.replace("-", " ").title()

        raw_status = fm.get("status")
        if not raw_status:
            sm = re.search(r"^>\s+\*\*Status:\*\*\s*(.*?)$", content, re.MULTILINE)
            raw_status = sm.group(1).strip() if sm else "Accepted"

        status_lower = raw_status.lower()
        if "superse" in status_lower:
            status_clean = "Superseded"
        elif "deprecat" in status_lower:
            status_clean = "Deprecated"
        elif "propos" in status_lower:
            status_clean = "Proposed"
        elif "reject" in status_lower:
            status_clean = "Rejected"
        else:
            status_clean = "Accepted"

        date = fm.get("date")
        if not date:
            dm = re.search(r"^>\s+\*\*Date:\*\*\s*(.*?)$", content, re.MULTILINE)
            date = dm.group(1).strip() if dm else ""

        summary = ""
        m_ctx = re.search(r"##\s+Context\s*\n+(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if m_ctx:
            paras = [
                p.strip()
                for p in m_ctx.group(1).split("\n\n")
                if p.strip() and not p.strip().startswith(">") and not p.strip().startswith("#")
            ]
            if paras:
                summary = re.sub(r"\s+", " ", paras[0])
                summary = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", summary).replace("*", "").replace("`", "")
                if len(summary) > SUMMARY_MAX_LEN:
                    summary = summary[:SUMMARY_MAX_LEN].rstrip() + "…"

        adrs.append(
            {
                "id": f"ADR-{num_str}",
                "number": num_str,
                "title": title,
                "status": status_clean,
                "raw_status": raw_status,
                "epic_id": fm.get("epic_id", ""),
                "date": date,
                "summary": summary,
                "rel_link": af.relative_to(REPO_ROOT / "docs").as_posix(),
                "path": af.relative_to(REPO_ROOT).as_posix(),
                "content": content,
            }
        )
    return adrs


def detect_drift(epics_data: list[dict], status_text: str) -> list[str]:
    discrepancies: list[str] = []

    # Map of story ID -> done boolean from status text
    status_stories: dict[str, bool] = {}
    for line in status_text.splitlines():
        line = line.strip()
        m = re.match(
            r"-\s*\[([ xX])\]\s*(?:\[\s*)?\*\*Story\s+([0-9.]+)\*\*", line
        )
        if m:
            is_done = m.group(1).lower() == "x"
            story_id = m.group(2)
            status_stories[story_id] = is_done

    # Compare with disk specifications
    disk_stories: dict[str, bool] = {}
    for ep in epics_data:
        for s in ep.get("stories", []):
            disk_stories[s["id"]] = s["done"]

    for sid, disk_done in disk_stories.items():
        if sid not in status_stories:
            discrepancies.append(
                f"Story {sid} exists on disk but is missing in docs/STATUS.md"
            )
        elif status_stories[sid] != disk_done:
            expected = "completed [x]" if disk_done else "planned [ ]"
            actual = "completed [x]" if status_stories[sid] else "planned [ ]"
            discrepancies.append(
                f"Story {sid} status mismatch: disk has {expected}, docs/STATUS.md has {actual}"
            )

    for sid in status_stories:
        if sid not in disk_stories:
            discrepancies.append(
                f"Story {sid} is listed in docs/STATUS.md but has no file on disk"
            )

    return discrepancies


def sync_status_md(epics_data: list[dict]) -> None:
    if not STATUS_MD.exists():
        return
    content = STATUS_MD.read_text(encoding="utf-8")

    for ep in epics_data:
        epic_num = ep["id"]
        stories = ep.get("stories", [])
        if not stories:
            continue

        pattern = re.compile(
            r"(###\s+Epic\s+"
            + re.escape(epic_num)
            + r"\b[^\n]*\n)(?:(>[^\n]*\n))?((?:-\s*\[[ xX]\].*\n?)*)",
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
    return datetime.date.today().isoformat()


def parse_templates() -> dict[str, str]:
    if not TEMPLATES_DIR.exists():
        return {}
    templates: dict[str, str] = {}
    for tf in TEMPLATES_DIR.glob("*.md"):
        if tf.name != "README.md":
            templates[tf.name] = tf.read_text(encoding="utf-8")
    return templates


def detect_project_name() -> str:
    if STATUS_MD.exists():
        lines = STATUS_MD.read_text(encoding="utf-8").splitlines()
        if lines and lines[0].startswith("#"):
            title_part = lines[0].lstrip("#").strip()
            for sep in ("—", "–", " - ", ":"):
                if sep in title_part:
                    candidate = title_part.split(sep, 1)[0].strip()
                    if candidate:
                        return candidate
            if title_part:
                return title_part

    readme_file = REPO_ROOT / "README.md"
    if readme_file.exists():
        for line in readme_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("# "):
                title_part = line[2:].strip()
                for sep in ("—", "–", " - ", ":"):
                    if sep in title_part:
                        candidate = title_part.split(sep, 1)[0].strip()
                        if candidate:
                            return candidate
                if title_part:
                    return title_part

    return REPO_ROOT.name.replace("-", " ").replace("_", " ").title()


def generate(
    epics_data: list[dict],
    prds_data: list[dict],
    design_specs_data: list[dict],
    adrs_data: list[dict],
    templates_data: dict[str, str] | None = None,
    project_name: str | None = None,
) -> str:
    template = TEMPLATE_HTML.read_text(encoding="utf-8")
    as_of_date = status_md_as_of_date()
    p_name = project_name or detect_project_name()

    clean_epics = []
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
        if ep.get("design_spec"):
            item["design_spec"] = ep["design_spec"]
        if ep.get("adrs"):
            item["adrs"] = ep["adrs"]
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
        clean_epics.append(item)

    payload = {
        "epics": clean_epics,
        "prds": prds_data,
        "design_specs": design_specs_data,
        "adrs": adrs_data,
        "templates": templates_data or {},
    }

    data_json = json.dumps(payload, sort_keys=False, ensure_ascii=False)
    html = (
        template.replace("__AS_OF_DATE__", as_of_date)
        .replace("__PROJECT_NAME__", p_name)
        .replace("__DATA_JSON__", data_json)
    )
    return html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate docs/status-dashboard.html from repository documents and reconcile docs/STATUS.md."
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
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Project name for the dashboard header and title (defaults to title in docs/STATUS.md or repository name).",
    )
    args = parser.parse_args()

    design_specs_data = parse_design_specs()
    adrs_data = parse_adr_documents()
    epics_data = parse_roadmap_documents(design_specs_data, adrs_data)
    prds_data = parse_product_documents()
    templates_data = parse_templates()

    status_text = STATUS_MD.read_text(encoding="utf-8") if STATUS_MD.exists() else ""
    discrepancies = detect_drift(epics_data, status_text) if status_text else []

    if args.check_only:
        if discrepancies:
            print(f"Drift detected ({len(discrepancies)} discrepancies):")
            for d in discrepancies:
                print(f"  - {d}")
            return 1
        print("Zero drift detected: docs/STATUS.md matches disk specifications.")
        return 0

    if args.sync and STATUS_MD.exists():
        sync_status_md(epics_data)
        # re-read after sync
        status_text = STATUS_MD.read_text(encoding="utf-8")
        discrepancies = detect_drift(epics_data, status_text)

    html = generate(
        epics_data,
        prds_data,
        design_specs_data,
        adrs_data,
        templates_data,
        project_name=args.name,
    )
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    total_stories = sum(len(ep["stories"]) for ep in epics_data)
    done_stories = sum(
        sum(1 for s in ep["stories"] if s["done"]) for ep in epics_data
    )
    print(
        f"Wrote {OUTPUT_HTML.relative_to(REPO_ROOT)} from {len(epics_data)} epics ({total_stories} stories), {len(prds_data)} PRDs, {len(design_specs_data)} design specs, and {len(adrs_data)} ADRs."
    )

    if discrepancies and not args.sync:
        print(
            f"Notice: {len(discrepancies)} discrepancies between disk and {STATUS_MD.relative_to(REPO_ROOT)}. Run 'make sync-status' to synchronize."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
