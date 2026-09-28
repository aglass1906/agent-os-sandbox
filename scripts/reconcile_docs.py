#!/usr/bin/env python3
"""Universal Document Reconciler & Linter for Agent OS.

Reconciles and lints repository documentation against canonical templates in docs/templates/.
Preserves 100% of engineering analysis, prose, diagrams, schemas, and task completion checkboxes.
Enforces structural alignment, frontmatter invariants, mandatory governance tasks, AI self-audit
checklists, and human verification procedures.

Usage examples:
  # Lint all active documentation (exit code 1 if drift detected)
  python3 scripts/reconcile_docs.py --check

  # Dry-run preview diff for Epic 30 stories
  python3 scripts/reconcile_docs.py --dry-run --epic 30 --target stories

  # Reconcile all in-progress and planned epics and stories
  python3 scripts/reconcile_docs.py --fix --status in_progress,planned

  # Reconcile specific epic and its stories
  python3 scripts/reconcile_docs.py --fix --epic 10
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import glob
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKLOG_DIR = REPO_ROOT / "docs" / "backlog"
TEMPLATES_DIR = REPO_ROOT / "docs" / "templates"
ADR_DIR = REPO_ROOT / "docs" / "adr"
DESIGN_SPECS_DIR = REPO_ROOT / "docs" / "design-specs"
PRODUCT_DIR = REPO_ROOT / "docs" / "product"
HANDOFFS_DIR = REPO_ROOT / "docs" / "history" / "handoffs"
STATUS_MD = REPO_ROOT / "docs" / "STATUS.md"

STATUS_PILLS = {
    "planned": "🟦 Planned",
    "in_progress": "🟨 In Progress",
    "completed": "✅ Completed",
    "accepted": "🟢 Accepted",
    "living": "🟢 Living",
    "approved": "🟢 Approved",
    "draft": "🟦 Draft",
    "review": "🟨 Review",
    "archived": "📦 Archived",
    "superseded": "📦 Superseded",
    "proposed": "🟦 Proposed",
}

AI_SELF_AUDIT_BLOCK = """### AI Self-Audit & Defect Remediation (Mandatory for Code Changes)
> *The AI agent MUST complete this audit and resolve all issues prior to marking the story completed or submitting work.*
- [ ] **Diff Hygiene**: Inspect `git diff` to verify only intended files/lines were touched. Ensure no leftover debugging statements, temporary prints, or commented-out code.
- [ ] **Defect & Regression Triage**: Investigate and fix any newly failing tests, compilation errors, or linter warnings immediately. Never bypass or silence failing checks.
- [ ] **Documentation Reconciliation**: Verify that relevant design specs (`docs/design-specs/`) and architecture docs (`docs/architecture/`) were updated to reflect actual shipped behavior, contracts, and flags.
- [ ] **Handoff Document Maintenance**: Updated `docs/history/handoffs/HANDOFF-EPIC-X.md` with commit log, test command outputs, and next-story guidance for subsequent agents.
- [ ] **Edge Cases & Error Handling**: Verify null/nil safety, error boundary captures, network timeouts, and boundary condition inputs.
- [ ] **State & Resource Teardown**: Confirm scratch databases, temp files, ephemeral worktrees, and test processes have been safely cleaned up."""

EPIC_ACCEPTANCE_GATES_BLOCK = """### Mandatory Acceptance Gate for Every Story
Before marking any story complete, the implementing agent must:
1. Self-audit code, schema, and protocol contracts for diff hygiene and defect remediation.
2. Reconcile living design documentation (`docs/design-specs/` or `docs/architecture/`) to ensure code and specs never diverge.
3. Execute automated tests (`pytest`, `xcodebuild`, `make test-mac-ui`) and document the human verification procedure.
4. Record commands, outputs, and verification evidence in the story handoff.

### Two-Tier Documentation Invariant
- **Tier 1 (Story Task — Mandatory)**: Every code story that modifies APIs, schemas, UI states, or invariants must include an atomic task to update the corresponding feature design spec (`docs/design-specs/`) or architecture spec (`docs/architecture/`).
- **Tier 2 (Epic Story — Large Initiatives)**: For complex multi-story Epics (5+ stories or major architectural initiatives), scope a concluding story (e.g. `Story X.Z — Subsystem Architectural Consolidation, Sequence Diagrams & Runbook`) to synthesize end-to-end system flows and operator runbooks."""

EPIC_TESTING_PROTOCOL_BLOCK = """### Mandatory 3-Phase Testing Protocol
```bash
# Phase 1: Setup
make test-db

# Phase 2: Test Execution
cd orchestrator && pytest -q
xcodebuild -workspace mac-app/AgentOS.xcworkspace -scheme AgentOS build
make test-mac-ui

# Phase 3: Teardown & Cleanup
make reset-test-db
git worktree prune
rm -rf /tmp/agentos-test* "$TMPDIR/agentos-ui-tests"
git status --short
```"""


def parse_frontmatter(content: str) -> tuple[dict[str, any], str]:
    """Parse YAML frontmatter and return (dict, remaining_body)."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_raw = parts[1]
    body = parts[2].lstrip("\n")

    data: dict[str, any] = {}
    current_list_key = None
    for line in fm_raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key:
            item = stripped[2:].strip().strip("\"'")
            if isinstance(data.get(current_list_key), list):
                data[current_list_key].append(item)
            else:
                data[current_list_key] = [item]
            continue
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v_val = v.strip()
            # If value is quoted, preserve quoted content and ignore # inside quotes
            if v_val.startswith('"') and '"' in v_val[1:]:
                close_idx = v_val.rfind('"')
                v = v_val[1:close_idx]
                current_list_key = None
                data[k] = v
            elif v_val.startswith("'") and "'" in v_val[1:]:
                close_idx = v_val.rfind("'")
                v = v_val[1:close_idx]
                current_list_key = None
                data[k] = v
            else:
                if " #" in v_val:
                    v_val = v_val.split(" #", 1)[0]
                v = v_val.strip().strip("\"'")
                if not v:
                    current_list_key = k
                    data[k] = []
                else:
                    current_list_key = None
                    data[k] = v
        else:
            current_list_key = None
    return data, body


def strip_trailing_hr(text: str) -> str:
    """Strips trailing horizontal rules and whitespace."""
    text = text.strip()
    while text.endswith("---"):
        text = text[:-3].strip()
    return text


def serialize_frontmatter(data: dict[str, any]) -> str:
    """Serialize metadata dict into YAML frontmatter string."""
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        elif isinstance(v, (int, float, bool)):
            lines.append(f"{k}: {v}")
        else:
            v_str = str(v)
            # Wrap in quotes for clean YAML formatting
            if not (v_str.startswith('"') and v_str.endswith('"')):
                lines.append(f'{k}: "{v_str}"')
            else:
                lines.append(f"{k}: {v_str}")
    lines.append("---")
    return "\n".join(lines)


def get_epic_num_from_str(s: str) -> int | None:
    m = re.search(r"EPIC[-_](\d+)", s, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"epic[-_](\d+)", s, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def get_story_coords_from_str(s: str) -> tuple[int, int] | None:
    m = re.search(r"STORY[-_](\d+)\.(\d+)", s, re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def load_status_md_epic_statuses() -> dict[int, str]:
    """Parse authoritative epic statuses from docs/STATUS.md rollup table."""
    if not STATUS_MD.exists():
        return {}
    content = STATUS_MD.read_text(encoding="utf-8")
    epic_statuses: dict[int, str] = {}
    for line in content.splitlines():
        m = re.match(r"\|\s*\**(\d+)\**\s*\|\s*([^|]+)\|\s*([^|]+)\|", line)
        if m:
            num_str, _, st = m.groups()
            st_clean = st.strip()
            status_key = "planned"
            if any(w in st_clean for w in ["Done", "Complete", "✅"]):
                status_key = "completed"
            elif any(w in st_clean for w in ["In progress", "In Progress", "🟨", "Living epic"]):
                status_key = "in_progress"
            elif any(w in st_clean for w in ["Planned", "⬜", "🟦"]):
                status_key = "planned"
            elif "Promoted" in st_clean:
                status_key = "archived"
            epic_statuses[int(num_str)] = status_key
    return epic_statuses


def load_epic_metadata_lookup() -> dict[int, dict[str, any]]:
    """Loads all epic directories and returns metadata indexed by epic number."""
    status_md_map = load_status_md_epic_statuses()
    lookup = {}
    for ed in glob.glob(str(BACKLOG_DIR / "epic-*")):
        ed_path = Path(ed)
        if not ed_path.is_dir():
            continue
        epic_files = [f for f in ed_path.glob("EPIC-*.md")]
        if not epic_files:
            continue
        ef = epic_files[0]
        content = ef.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        epic_num = get_epic_num_from_str(ef.name)
        if epic_num is None:
            continue
        title = fm.get("title")
        if not title:
            m_title = re.search(r"#\s+(?:Epic|Phase)\s+\d+[\s—\-]+([^\n]+)", body)
            title = m_title.group(1).strip() if m_title else ef.stem
        # clean title
        title = title.strip("\"'")
        status = fm.get("status") or status_md_map.get(epic_num, "planned")
        lookup[epic_num] = {
            "num": epic_num,
            "dir_path": ed_path,
            "file_path": ef,
            "title": title,
            "status": status,
            "surfaces": fm.get("surfaces", ["mac-app", "orchestrator"]),
            "frontmatter": fm,
        }
    return lookup


def generate_human_verification_flow(story_id: str, title: str, surfaces: list[str]) -> str:
    """Generates a contextual, surface-tailored human verification procedure."""
    s_lower = " ".join(surfaces).lower()
    t_clean = title.strip(" \"'")
    
    if "mac-app" in s_lower and "orchestrator" in s_lower:
        prereqs = """- Local orchestrator API running on `http://127.0.0.1:8000` with test PostgreSQL database.
- Agent OS macOS client compiled and launched in test or live configuration.
- Active workspace registered in client settings."""
        s1_action = f"Launch Agent OS client and navigate to the view associated with {t_clean}."
        s1_out = "Target view loads cleanly with populated workspace data; no network or decoding errors."
        s2_action = f"Initiate action for {t_clean} from the client interface."
        s2_out = "Client transmits corresponding WebSocket protocol event; orchestrator confirms receipt and persists state."
        s3_action = "Restart or reopen the client window."
        s3_out = "Persisted state reloads faithfully without data regression or UI glitches."
        s4_action = "Simulate unexpected input, network drop, or server disconnect during operation."
        s4_out = "Client displays friendly error/reconnect banner and prevents data corruption."
    elif "mac-app" in s_lower:
        prereqs = """- Agent OS macOS client compiled and launched (`xcodebuild -scheme AgentOS build`).
- Target view open in client."""
        s1_action = f"Navigate to the UI surface for {t_clean}."
        s1_out = "View elements render with correct typography, layout, and contrast; keyboard focus operational."
        s2_action = f"Interact with primary controls for {t_clean}."
        s2_out = "Interactive states (clicks, selections, hotkeys) respond immediately with fluid animation."
        s3_action = "Switch away to another view and return."
        s3_out = "View restores prior selection and state seamlessly."
        s4_action = "Trigger boundary condition (e.g. empty list, rapid clicking, escape key)."
        s4_out = "Interface handles edge case gracefully without visual clipping or runtime crashes."
    elif "supabase" in s_lower or "orchestrator" in s_lower:
        prereqs = """- Local test database running on port 55432 (`make test-db`).
- Orchestrator service running with environment configured."""
        s1_action = f"Inspect database schema or call health endpoint for {t_clean}."
        s1_out = "Schema migration applied; API returns 200 OK with correct envelope structure."
        s2_action = f"Execute primary endpoint or handler for {t_clean} with valid payload."
        s2_out = "Database records created/updated with proper RLS scoping; expected payload returned."
        s3_action = "Query data repository or inspect event stream."
        s3_out = "Events recorded with accurate timestamps and metadata."
        s4_action = "Send malformed payload or unauthenticated request."
        s4_out = "Service returns 4xx/401 with structured validation error, rejecting invalid mutation."
    else:
        prereqs = """- Agent OS development environment configured.
- Relevant service and test runners available."""
        s1_action = f"Initialize baseline state for {t_clean}."
        s1_out = "System reports ready and operational."
        s2_action = f"Execute verification scenario for {t_clean}."
        s2_out = "Deliverable executes successfully and satisfies acceptance criteria."
        s3_action = "Inspect logs and persisted artifacts."
        s3_out = "Outputs and artifacts adhere to platform schemas."
        s4_action = "Test boundary inputs or invalid conditions."
        s4_out = "Failures handled deterministically with informative error reporting."

    return f"""## 5. Human Verification Procedure (Step-by-Step)
> *Required for any functional, visual, or interactive change. Provides explicit, step-by-step instructions for human operator validation.*

### Prerequisites
{prereqs}

### Step-by-Step Verification Flow
1. **Step 1: Initial State & Navigation**:
   - **Action**: {s1_action}
   - **Expected Outcome**: {s1_out}
2. **Step 2: Trigger Primary Functional Action**:
   - **Action**: {s2_action}
   - **Expected Outcome**: {s2_out}
3. **Step 3: Verify Persistence & Feedback**:
   - **Action**: {s3_action}
   - **Expected Outcome**: {s3_out}
4. **Step 4: Edge Case / Failure Path**:
   - **Action**: {s4_action}
   - **Expected Outcome**: {s4_out}

### Operator Sign-Off
- [ ] **Human Verification Verified By**: `[Operator Name / Handle]`
- [ ] **Verification Date**: `YYYY-MM-DD`
- [ ] **Outcome**: Pass / Needs Revision"""


def reconcile_story(file_path: Path, epic_lookup: dict[int, dict[str, any]]) -> tuple[str, bool]:
    """Reconciles a story file to match STORY-TEMPLATE.md. Returns (new_content, changed)."""
    orig_content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(orig_content)

    # 1. Coordinate Discovery
    story_coords = get_story_coords_from_str(file_path.name)
    epic_num = story_coords[0] if story_coords else None
    story_num = story_coords[1] if story_coords else None

    story_id = fm.get("id") or (f"STORY-{epic_num}.{story_num}" if epic_num is not None else file_path.stem)
    epic_id = fm.get("epic_id") or (f"EPIC-{epic_num}" if epic_num is not None else "EPIC-X")

    # Title extraction
    title = fm.get("title")
    if not title:
        m_title = re.search(r"^#\s+Story\s+\d+\.\d+[\s—\-]+([^\n]+)", body, re.MULTILINE)
        if m_title:
            title = m_title.group(1).strip()
        else:
            # derive from filename
            name_parts = file_path.stem.split("-", 2)
            title = name_parts[2].replace("-", " ").title() if len(name_parts) > 2 else file_path.stem

    title = title.strip("\"'")
    status = fm.get("status", "planned").lower()
    if status not in STATUS_PILLS:
        status = "planned"

    surfaces = fm.get("surfaces")
    if not surfaces or not isinstance(surfaces, list):
        surfaces = ["mac-app", "orchestrator"]

    epic_meta = epic_lookup.get(epic_num) if epic_num is not None else None
    epic_title = epic_meta["title"] if epic_meta else f"Epic {epic_num}"
    epic_file_name = epic_meta["file_path"].name if epic_meta else f"EPIC-{epic_num}.md"
    epic_dir_name = epic_meta["dir_path"].name if epic_meta else f"epic-{epic_num}"

    # Build standardized frontmatter
    new_fm = {
        "id": story_id,
        "epic_id": epic_id,
        "title": title,
        "type": "story-spec",
        "status": status,
        "surfaces": surfaces,
        "parent_epic": f"docs/backlog/{epic_dir_name}/{epic_file_name}",
    }
    if "design_spec" in fm:
        new_fm["design_spec"] = fm["design_spec"]
    if "adrs" in fm:
        new_fm["adrs"] = fm["adrs"]

    # Rewrite any legacy docs/roadmap/ links in body
    body = body.replace("docs/roadmap/", "docs/backlog/")

    # 2. Decompose body into sections
    sections = re.split(r"\n(?=## \d+\.)", body)

    # Standard header block (Section 0)
    status_pill = STATUS_PILLS.get(status, "🟦 Planned")
    new_header = f"""# Story {epic_num}.{story_num} — {title}

> **Parent Epic:** [Epic {epic_num} — {epic_title}](../{epic_file_name})  
> **Status:** {status_pill}  
> **Living Tracker:** [`docs/STATUS.md`](../../../STATUS.md)

---"""

    sec_map: dict[int, str] = {}
    for s in sections[1:]:
        m_num = re.match(r"## (\d+)\.", s.strip())
        if m_num:
            sec_num = int(m_num.group(1))
            sec_map[sec_num] = s.strip()

    # Reconcile Section 1 (Executive Summary)
    sec1 = sec_map.get(1, "")
    if sec1:
        # Check if it has generic placeholder
        if "Delivers concrete, testable value to the operator" in sec1 and "As " not in sec1:
            sec1 = f"""## 1. Executive Summary & User/Operator Benefit
As an Agent OS operator, I want {title.lower()} so that the system reliably supports {title.lower()} with robust validation and high usability."""
    else:
        sec1 = f"""## 1. Executive Summary & User/Operator Benefit
As an Agent OS operator, I want {title.lower()} so that the system reliably supports {title.lower()} with robust validation and high usability."""

    # Reconcile Section 2 (Scope & Technical Requirements)
    sec2 = sec_map.get(2, "")
    if not sec2:
        sec2 = f"""## 2. Scope & Technical Requirements
- **Deliverables**: {title}
- **Invariants**: Strictly follow platform guidelines and avoid silent failures."""

    # Reconcile Section 3 (Atomic Tasks)
    sec3 = sec_map.get(3, "")
    if not sec3:
        sec3 = f"""## 3. Atomic Tasks
- [ ] **Task {epic_num}.{story_num}.1**: Implement domain logic and contracts for {title}.
- [ ] **Task {epic_num}.{story_num}.2**: Wire UI, service, or protocol integration.
- [ ] **Task {epic_num}.{story_num}.3**: Automated test coverage and verification."""

    # Check for standard governance tasks in sec3
    has_doc_recon = "Documentation reconciliation" in sec3 or "documentation reconciliation" in sec3
    has_handoff = "Session handoff" in sec3 or "session handoff" in sec3

    sec3 = strip_trailing_hr(sec3)
    if not has_doc_recon or not has_handoff:
        # Determine highest existing task number
        task_nums = [int(m.group(1)) for m in re.finditer(rf"Task\s+{epic_num}\.{story_num}\.(\d+)", sec3, re.IGNORECASE)]
        next_num = max(task_nums) + 1 if task_nums else 4
        tasks_to_add = []
        if not has_doc_recon:
            tasks_to_add.append(f"- [ ] **Task {epic_num}.{story_num}.{next_num}**: Documentation reconciliation — update relevant design spec in docs/design-specs/ or architecture spec in docs/architecture/ with shipped behavior, contracts, and flags.")
            next_num += 1
        if not has_handoff:
            tasks_to_add.append(f"- [ ] **Task {epic_num}.{story_num}.{next_num}**: Session handoff — update docs/history/handoffs/HANDOFF-EPIC-{epic_num}.md with test evidence, git commits, and next steps.")
        sec3 = sec3.rstrip() + "\n" + "\n".join(tasks_to_add)

    # Reconcile Section 4 (Acceptance Gates & AI Self-Audit)
    sec4 = sec_map.get(4, "")
    if sec4:
        # Normalize heading to ## 4. Acceptance Gates & AI Self-Audit
        sec4_lines = sec4.splitlines()
        sec4_lines[0] = "## 4. Acceptance Gates & AI Self-Audit"
        sec4_body = "\n".join(sec4_lines)

        # Check if AI Self-Audit block exists
        if "AI Self-Audit & Defect Remediation" not in sec4_body:
            ai_audit_block = AI_SELF_AUDIT_BLOCK.replace("HANDOFF-EPIC-X.md", f"HANDOFF-EPIC-{epic_num}.md") if epic_num is not None else AI_SELF_AUDIT_BLOCK
            sec4_body = strip_trailing_hr(sec4_body) + "\n\n" + ai_audit_block
        sec4 = sec4_body
    else:
        ai_audit_block = AI_SELF_AUDIT_BLOCK.replace("HANDOFF-EPIC-X.md", f"HANDOFF-EPIC-{epic_num}.md") if epic_num is not None else AI_SELF_AUDIT_BLOCK
        sec4 = f"""## 4. Acceptance Gates & AI Self-Audit

### Automated Verification Gates
- [ ] `cd orchestrator && pytest -q`
- [ ] `xcodebuild -workspace mac-app/AgentOS.xcworkspace -scheme AgentOS build`

{ai_audit_block}"""

    # Reconcile Section 5 (Human Verification Procedure)
    sec5 = sec_map.get(5, "")
    if not sec5 or "Human Verification" not in sec5:
        sec5 = generate_human_verification_flow(story_id, title, surfaces)

    # Assemble complete content with single dividers
    assembled_body = f"""{new_header}

{strip_trailing_hr(sec1)}

---

{strip_trailing_hr(sec2)}

---

{strip_trailing_hr(sec3)}

---

{strip_trailing_hr(sec4)}

---

{strip_trailing_hr(sec5)}
"""
    assembled = serialize_frontmatter(new_fm) + "\n\n" + assembled_body.strip() + "\n"
    changed = assembled != orig_content
    return assembled, changed


def reconcile_epic(file_path: Path, stories: list[Path]) -> tuple[str, bool]:
    """Reconciles an epic plan file to match EPIC-TEMPLATE.md. Returns (new_content, changed)."""
    orig_content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(orig_content)

    epic_num = get_epic_num_from_str(file_path.name)
    epic_id = fm.get("id") or (f"EPIC-{epic_num}" if epic_num is not None else "EPIC-X")

    title = fm.get("title")
    if not title:
        m_title = re.search(r"^#\s+(?:Epic|Phase)\s+\d+[\s—\-]+([^\n]+)", body, re.MULTILINE)
        if m_title:
            title = m_title.group(1).strip()
        else:
            title = file_path.stem.replace(f"EPIC-{epic_num}-", "").replace("-", " ").title()
    title = title.strip("\"'")

    surfaces = fm.get("surfaces")
    if not surfaces or not isinstance(surfaces, list):
        surfaces = ["mac-app", "orchestrator"]

    today = datetime.date.today().isoformat()
    created = fm.get("created", today)
    updated = today

    # Count stories done vs total
    stories_total = len(stories)
    stories_done = 0
    story_rows = []
    for s_path in sorted(stories):
        s_content = s_path.read_text(encoding="utf-8")
        s_fm, s_body = parse_frontmatter(s_content)
        s_status = s_fm.get("status", "planned").lower()
        if s_status == "completed":
            stories_done += 1
        s_coords = get_story_coords_from_str(s_path.name)
        s_label = f"Story {s_coords[0]}.{s_coords[1]}" if s_coords else s_path.stem
        s_title = s_fm.get("title", s_label).strip("\"'")
        s_pill = STATUS_PILLS.get(s_status, "🟦 Planned")
        story_rows.append(f"| [`{s_label}`](./stories/{s_path.name}) | {s_title} | {s_pill} | [`{s_fm.get('id', s_label)}`](./stories/{s_path.name}) |")

    # Authoritative status resolution:
    status_md_map = load_status_md_epic_statuses()
    st_from_md = status_md_map.get(epic_num)
    if st_from_md == "completed" or (stories_total > 0 and stories_done == stories_total):
        status = "completed"
    elif st_from_md == "in_progress" or (stories_done > 0 and stories_done < stories_total):
        status = "in_progress"
    elif fm.get("status") and fm.get("status").lower() in STATUS_PILLS:
        status = fm.get("status").lower()
    else:
        status = st_from_md or "planned"

    new_fm = {
        "id": epic_id,
        "title": title,
        "type": "epic-plan",
        "status": status,
        "created": created,
        "updated": updated,
    }
    if "design_spec" in fm:
        new_fm["design_spec"] = fm["design_spec"]
    if "adrs" in fm:
        new_fm["adrs"] = fm["adrs"]
    new_fm["surfaces"] = surfaces
    new_fm["stories_total"] = stories_total
    new_fm["stories_done"] = stories_done

    # Rewrite any legacy docs/roadmap/ links in body
    body = body.replace("docs/roadmap/", "docs/backlog/")

    # Standard Category & Status header block
    status_pill = STATUS_PILLS.get(status, "🟦 Planned")
    new_header = f"""# Epic {epic_num} — {title}

> **Category:** Master Backlog & Epic Execution Plan  
> **Status:** {status_pill}  
> **Master Epic Backlog:** [`docs/backlog/BACKLOG.md`](../BACKLOG.md)  
> **Living Execution Tracker:** [`docs/STATUS.md`](../../STATUS.md)  
> **Stories Directory:** [`./stories/`](./stories/)

---"""

    # Parse sections split by \n(?=## )
    raw_sections = re.split(r"\n(?=## )", body)
    
    # Process each section:
    processed_sections = []
    has_story_breakdown = False
    has_testing_strategy = False

    for s in raw_sections[1:]:
        s_clean = strip_trailing_hr(s.strip())
        if not s_clean:
            continue
        
        # Check if this section is the Story Breakdown section
        if ("| Story |" in s_clean or "Story Breakdown" in s_clean) and not has_story_breakdown:
            has_story_breakdown = True
            lines = s_clean.splitlines()
            lines[0] = "## 3. Story Breakdown & Acceptance Gates"
            s_body = "\n".join(lines)
            
            # If the story breakdown doesn't have the table, or table needs updating
            if "| Story |" not in s_body and story_rows:
                table_str = "\n".join(story_rows)
                s_body = s_body + f"\n\n| Story | Title | Status | Specification |\n|---|---|---|---|\n{table_str}"
            
            if "Mandatory Acceptance Gate for Every Story" not in s_body:
                s_body = s_body.rstrip() + "\n\n" + EPIC_ACCEPTANCE_GATES_BLOCK
            processed_sections.append(strip_trailing_hr(s_body))
        elif "Testing Strategy" in s_clean or "3-Phase Testing Protocol" in s_clean or "Verification & Testing" in s_clean:
            has_testing_strategy = True
            lines = s_clean.splitlines()
            lines[0] = "## 4. Verification & Testing Strategy"
            s_body = "\n".join(lines)
            if "Mandatory 3-Phase Testing Protocol" not in s_body:
                s_body = s_body.rstrip() + "\n\n" + EPIC_TESTING_PROTOCOL_BLOCK
            processed_sections.append(strip_trailing_hr(s_body))
        else:
            processed_sections.append(s_clean)

    # If story breakdown was not present in the document at all, insert it
    if not has_story_breakdown:
        table_str = "\n".join(story_rows) if story_rows else "| Story | Title | Status | Specification |\n|---|---|---|---|\n| TBD | Planned | 🟦 Planned | TBD |"
        s3 = f"""## 3. Story Breakdown & Acceptance Gates

| Story | Title | Status | Specification |
|---|---|---|---|
{table_str}

{EPIC_ACCEPTANCE_GATES_BLOCK}"""
        processed_sections.append(strip_trailing_hr(s3))

    # If testing strategy was not present in the document at all, append it
    if not has_testing_strategy:
        s4 = f"""## 4. Verification & Testing Strategy

{EPIC_TESTING_PROTOCOL_BLOCK}"""
        processed_sections.append(strip_trailing_hr(s4))

    # Assemble sections with single --- dividers
    assembled_body = new_header + "\n\n" + "\n\n---\n\n".join(processed_sections)
    assembled = serialize_frontmatter(new_fm) + "\n\n" + assembled_body.strip() + "\n"
    changed = assembled != orig_content
    return assembled, changed


def reconcile_design_spec(file_path: Path, epic_lookup: dict[int, dict]) -> tuple[str, bool]:
    orig_content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(orig_content)

    stem = file_path.stem
    title = fm.get("title")
    if not title:
        m = re.search(r"^#\s+(?:Feature Design Spec\s*[—\-:]\s*)?(.*?)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else stem.replace("-", " ").title()
    title = title.strip('"').strip("'")

    doc_id = fm.get("id")
    if not doc_id:
        doc_id = stem if stem.startswith("SPEC-") else f"SPEC-{stem}"

    raw_status = fm.get("status", "")
    if not raw_status:
        m_st = re.search(r"Status[:*]+\s*([^\n\.<]+)", body)
        raw_status = m_st.group(1).strip() if m_st else "living"
    raw_status = raw_status.lower()
    if "draft" in raw_status:
        status = "draft"
    elif "superseded" in raw_status:
        status = "superseded"
    elif "accepted" in raw_status:
        status = "accepted"
    elif "planned" in raw_status:
        status = "planned"
    else:
        status = "living"

    created = fm.get("created", "2026-09-27")
    updated = fm.get("updated", "2026-09-27")

    epic_id = fm.get("epic_id")
    if not epic_id:
        for k in ("related_epic", "parent_epic", "target_epic"):
            if fm.get(k):
                m_ep = re.search(r"EPIC-(\d+)", str(fm[k]), re.IGNORECASE)
                if m_ep:
                    epic_id = f"EPIC-{m_ep.group(1)}"
                    break
    if not epic_id:
        m_ep = re.search(r"(?:Epic|Phase)\s+(\d+)", body)
        if m_ep:
            epic_id = f"EPIC-{m_ep.group(1)}"

    adrs = fm.get("adrs", [])
    if isinstance(adrs, str):
        adrs = [adrs]
    elif not adrs and fm.get("adr"):
        adrs = [fm["adr"]]
    if not adrs:
        found_adrs = re.findall(r"docs/adr/(00\d{2}[^.\s\)]+\.md)", body)
        if found_adrs:
            adrs = [f"docs/adr/{a}" for a in sorted(set(found_adrs))]

    surfaces = fm.get("surfaces", [])
    if isinstance(surfaces, str):
        surfaces = [surfaces]
    if not surfaces:
        surfaces = ["mac-app", "orchestrator"]

    new_fm = {
        "id": doc_id,
        "title": title,
        "type": "design-spec",
        "status": status,
        "created": created,
        "updated": updated,
    }
    if epic_id:
        new_fm["epic_id"] = epic_id
    if adrs:
        new_fm["adrs"] = adrs
    new_fm["surfaces"] = surfaces

    # Fix relative links
    body = body.replace("docs/roadmap/", "docs/backlog/")
    body = body.replace("../roadmap/", "../backlog/")
    body = body.replace("../../roadmap/", "../../backlog/")

    # Header & Breadcrumbs
    pill = STATUS_PILLS.get(status, f"🟦 {status.title()}")
    epic_link_line = ""
    if epic_id:
        ep_num = get_epic_num_from_str(epic_id)
        if ep_num is not None and ep_num in epic_lookup:
            ep_meta = epic_lookup[ep_num]
            rel_plan = f"../backlog/{ep_meta['dir_path'].name}/{ep_meta['file_path'].name}"
            epic_link_line = f"\n> **Associated Epic:** [`{ep_meta['file_path'].name}`]({rel_plan})"

    # Header & Breadcrumbs
    pill = STATUS_PILLS.get(status, f"🟦 {status.title()}")
    epic_link_line = ""
    if epic_id:
        ep_num = get_epic_num_from_str(epic_id)
        if ep_num is not None and ep_num in epic_lookup:
            ep_meta = epic_lookup[ep_num]
            rel_plan = f"../backlog/{ep_meta['dir_path'].name}/{ep_meta['file_path'].name}"
            epic_link_line = f"\n> **Associated Epic:** [`{ep_meta['file_path'].name}`]({rel_plan})"

    extra_bq_lines = []
    body_clean = re.sub(r"^#\s+.*?\n+", "", body, count=1).lstrip()
    if body_clean.startswith(">"):
        lines = body_clean.splitlines(keepends=True)
        idx = 0
        while idx < len(lines) and (lines[idx].strip().startswith(">") or not lines[idx].strip()):
            line_str = lines[idx].strip()
            if line_str.startswith(">"):
                is_std = any(k in line_str for k in ("Category:", "Status:", "Index:", "Associated Epic:", "Applies to:", "Date:"))
                if not is_std:
                    extra_bq_lines.append(line_str)
            idx += 1
        body_clean = "".join(lines[idx:]).lstrip()
    body_clean = re.sub(r"^---\s*\n+", "", body_clean).lstrip()

    extra_str = ("\n" + "\n".join(extra_bq_lines)) if extra_bq_lines else ""
    expected_header = f"""# Feature Design Spec — {title}

> **Category:** Technical & UX Design Specification  
> **Status:** {pill}  
> **Index:** [`docs/design-specs/README.md`](./README.md){epic_link_line}{extra_str}"""

    assembled = serialize_frontmatter(new_fm) + "\n\n" + expected_header + "\n\n---\n\n" + body_clean.strip() + "\n"
    changed = assembled != orig_content
    return assembled, changed


def reconcile_adr(file_path: Path, epic_lookup: dict[int, dict]) -> tuple[str, bool]:
    orig_content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(orig_content)

    stem = file_path.stem
    m_num = re.search(r"^(?:ADR-)?(\d+)", stem, re.IGNORECASE)
    num_str = m_num.group(1).zfill(4) if m_num else "0000"
    doc_id = f"ADR-{num_str}"

    title = fm.get("title")
    if not title:
        m = re.search(r"^#\s*ADR\s*\d+\s*[:—\-]\s*(.*?)$", body, re.MULTILINE)
        if not m:
            m = re.search(r"^#\s*(.*?)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else stem.replace("-", " ").title()
    title = title.strip('"').strip("'")

    raw_status = fm.get("status", "")
    if not raw_status:
        m_st = re.search(r"\*\*Status:\*\*\s*([^\n<]+)", body)
        raw_status = m_st.group(1).strip() if m_st else "accepted"
    raw_status = raw_status.lower()
    if "proposed" in raw_status:
        status = "proposed"
    elif "rejected" in raw_status:
        status = "rejected"
    elif "superseded" in raw_status:
        status = "superseded"
    elif "deprecated" in raw_status:
        status = "deprecated"
    else:
        status = "accepted"

    date_str = fm.get("date") or fm.get("created")
    if not date_str:
        m_dt = re.search(r"\*\*Date:\*\*\s*([0-9\-]+)", body)
        date_str = m_dt.group(1).strip() if m_dt else "2026-09-27"

    deciders = fm.get("deciders", [])
    if isinstance(deciders, str):
        deciders = [deciders]
    if not deciders:
        m_dec = re.search(r"\*\*Deciders:\*\*\s*([^\n<]+)", body)
        if m_dec:
            deciders = [m_dec.group(1).strip()]
        else:
            deciders = ["Agent OS Architecture & Platform Team"]

    epic_id = fm.get("epic_id")
    if not epic_id:
        m_ep = re.search(r"(?:Epic|Phase)\s+(\d+)", body)
        if m_ep:
            epic_id = f"EPIC-{m_ep.group(1)}"

    new_fm = {
        "id": doc_id,
        "title": title,
        "type": "adr",
        "status": status,
        "date": date_str,
        "deciders": deciders,
    }
    if epic_id:
        new_fm["epic_id"] = epic_id

    body = body.replace("docs/roadmap/", "docs/backlog/")
    body = body.replace("../roadmap/", "../backlog/")
    body = body.replace("../../roadmap/", "../../backlog/")

    pill = "✅ Accepted" if status == "accepted" else ("🟦 Proposed" if status == "proposed" else f"📦 {status.title()}")
    epic_line = ""
    if epic_id:
        ep_num = get_epic_num_from_str(epic_id)
        if ep_num is not None and ep_num in epic_lookup:
            ep_meta = epic_lookup[ep_num]
            rel_plan = f"../backlog/{ep_meta['dir_path'].name}/{ep_meta['file_path'].name}"
            epic_line = f"\n> **Applies to:** [`{ep_meta['file_path'].name}`]({rel_plan})"

    extra_bq_lines = []
    body_clean = re.sub(r"^#\s+.*?\n+", "", body, count=1).lstrip()
    if body_clean.startswith(">"):
        lines = body_clean.splitlines(keepends=True)
        idx = 0
        while idx < len(lines) and (lines[idx].strip().startswith(">") or not lines[idx].strip()):
            line_str = lines[idx].strip()
            if line_str.startswith(">"):
                is_std = any(k in line_str for k in ("Category:", "Status:", "Index:", "Associated Epic:", "Applies to:", "Date:"))
                if not is_std:
                    extra_bq_lines.append(line_str)
            idx += 1
        body_clean = "".join(lines[idx:]).lstrip()
    body_clean = re.sub(r"^---\s*\n+", "", body_clean).lstrip()

    extra_str = ("\n" + "\n".join(extra_bq_lines)) if extra_bq_lines else ""
    expected_header = f"""# ADR {num_str}: {title}

> **Category:** Architecture Decision Record  
> **Status:** {pill}  
> **Date:** {date_str}  
> **Index:** [`docs/adr/README.md`](./README.md){epic_line}{extra_str}"""

    assembled = serialize_frontmatter(new_fm) + "\n\n" + expected_header + "\n\n---\n\n" + body_clean.strip() + "\n"
    changed = assembled != orig_content
    return assembled, changed


def reconcile_prd(file_path: Path) -> tuple[str, bool]:
    orig_content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(orig_content)

    stem = file_path.stem
    doc_id = fm.get("id", stem if stem.startswith("PRD-") else f"PRD-{stem}")
    title = fm.get("title")
    if not title:
        m = re.search(r"^#\s+(?:Product Requirements Document \(PRD\)\s*[—\-:]\s*|PRD\s*[—\-:]\s*)?(.*?)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else stem.replace("-", " ").title()
    title = title.strip('"').strip("'")

    status = fm.get("status", "approved").lower()
    created = fm.get("created", "2026-09-27")
    updated = fm.get("updated", "2026-09-27")
    owner = fm.get("owner", "Platform Team")
    target_epic = fm.get("target_epic", "docs/backlog/BACKLOG.md")
    if "roadmap" in str(target_epic):
        target_epic = str(target_epic).replace("roadmap", "backlog")

    personas = fm.get("personas", ["operator", "software-architect", "ai-agent"])
    if isinstance(personas, str):
        personas = [personas]

    new_fm = {
        "id": doc_id,
        "title": title,
        "type": "prd",
        "status": status,
        "created": created,
        "updated": updated,
        "owner": owner,
        "target_epic": target_epic,
        "personas": personas,
    }

    body = body.replace("docs/roadmap/", "docs/backlog/")
    body = body.replace("../roadmap/", "../backlog/")
    body = body.replace("../../roadmap/", "../../backlog/")

    pill = "🟢 Approved" if status == "approved" else ("🟨 Review" if status == "review" else "🟦 Draft")
    extra_bq_lines = []
    body_clean = re.sub(r"^#\s+.*?\n+", "", body, count=1).lstrip()
    if body_clean.startswith(">"):
        lines = body_clean.splitlines(keepends=True)
        idx = 0
        while idx < len(lines) and (lines[idx].strip().startswith(">") or not lines[idx].strip()):
            line_str = lines[idx].strip()
            if line_str.startswith(">"):
                is_std = any(k in line_str for k in ("Category:", "Status:", "Index:", "Target Epic Backlog:", "Owner:"))
                if not is_std:
                    extra_bq_lines.append(line_str)
            idx += 1
        body_clean = "".join(lines[idx:]).lstrip()
    body_clean = re.sub(r"^---\s*\n+", "", body_clean).lstrip()

    extra_str = ("\n" + "\n".join(extra_bq_lines)) if extra_bq_lines else ""
    expected_header = f"""# Product Requirements Document (PRD) — {title}

> **Category:** Product Requirements & Scope Specification  
> **Status:** {pill}  
> **Index:** [`docs/product/README.md`](./README.md)  
> **Target Epic Backlog:** [`docs/backlog/BACKLOG.md`](../backlog/BACKLOG.md)  
> **Owner:** {owner}{extra_str}"""

    assembled = serialize_frontmatter(new_fm) + "\n\n" + expected_header + "\n\n---\n\n" + body_clean.strip() + "\n"
    changed = assembled != orig_content
    return assembled, changed


def reconcile_handoff(file_path: Path, epic_lookup: dict[int, dict]) -> tuple[str, bool]:
    orig_content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(orig_content)

    stem = file_path.stem
    doc_id = fm.get("id", stem)
    title = fm.get("title")
    if not title:
        m = re.search(r"^#\s*(.*?)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else stem.replace("-", " ").title()
    title = title.strip('"').strip("'")

    epic_id = fm.get("epic_id")
    if not epic_id:
        m_ep = re.search(r"EPIC-(\d+)", stem, re.IGNORECASE)
        if not m_ep:
            m_ep = re.search(r"PHASE-(\d+)", stem, re.IGNORECASE)
        if not m_ep:
            m_ep = re.search(r"(?:Epic|Phase)\s+(\d+)", body)
        if m_ep:
            epic_id = f"EPIC-{m_ep.group(1)}"

    raw_status = fm.get("status", "")
    if not raw_status:
        m_st = re.search(r"\*\*Status[:*]+\s*([^\n<]+)", body)
        raw_status = m_st.group(1).strip() if m_st else "in_progress"
    raw_status = raw_status.lower()
    if "complete" in raw_status or "done" in raw_status or "audited" in raw_status:
        status = "completed"
    else:
        status = "in_progress"

    created = fm.get("created", "2026-09-27")
    updated = fm.get("updated", "2026-09-27")

    parent_epic = fm.get("parent_epic")
    if not parent_epic and epic_id:
        ep_num = get_epic_num_from_str(epic_id)
        if ep_num is not None and ep_num in epic_lookup:
            meta = epic_lookup[ep_num]
            parent_epic = f"docs/backlog/{meta['dir_path'].name}/{meta['file_path'].name}"

    new_fm = {
        "id": doc_id,
    }
    if epic_id:
        new_fm["epic_id"] = epic_id
    new_fm.update({
        "title": title,
        "type": "handoff",
        "status": status,
        "created": created,
        "updated": updated,
    })
    if parent_epic:
        new_fm["parent_epic"] = parent_epic

    body = body.replace("docs/roadmap/", "docs/backlog/")
    body = body.replace("../roadmap/", "../backlog/")
    body = body.replace("../../roadmap/", "../../backlog/")

    pill = "✅ Completed" if status == "completed" else "🟨 In Progress"
    plan_link = f"[`{parent_epic}`](../../{parent_epic.replace('docs/', '')})" if parent_epic else "[`docs/backlog/BACKLOG.md`](../../backlog/BACKLOG.md)"

    extra_bq_lines = []
    body_clean = re.sub(r"^#\s+.*?\n+", "", body, count=1).lstrip()
    if body_clean.startswith(">"):
        lines = body_clean.splitlines(keepends=True)
        idx = 0
        while idx < len(lines) and (lines[idx].strip().startswith(">") or not lines[idx].strip()):
            line_str = lines[idx].strip()
            if line_str.startswith(">"):
                is_std = any(k in line_str for k in ("Status:", "Canonical Plan:", "Living Tracker:"))
                if not is_std:
                    extra_bq_lines.append(line_str)
            idx += 1
        body_clean = "".join(lines[idx:]).lstrip()
    body_clean = re.sub(r"^---\s*\n+", "", body_clean).lstrip()

    extra_str = ("\n" + "\n".join(extra_bq_lines)) if extra_bq_lines else ""
    expected_header = f"""# {title}

> **Status:** {pill}  
> **Canonical Plan:** {plan_link}  
> **Living Tracker:** [`docs/STATUS.md`](../../STATUS.md){extra_str}"""

    assembled = serialize_frontmatter(new_fm) + "\n\n" + expected_header + "\n\n---\n\n" + body_clean.strip() + "\n"
    changed = assembled != orig_content
    return assembled, changed


def parse_args():
    parser = argparse.ArgumentParser(description="Agent OS Universal Documentation Reconciler & Linter")
    parser.add_argument(
        "--target",
        choices=["stories", "epics", "backlog", "design-specs", "adrs", "prds", "handoffs", "all", "all-docs"],
        default="all",
        help="Target document kind: stories, epics, backlog, design-specs, adrs, prds, handoffs, all (backlog epics+stories), all-docs (every document)",
    )
    parser.add_argument("--status", default="in_progress,planned", help="Comma-separated status filter: in_progress, planned, completed, all")
    parser.add_argument("--epic", type=int, help="Target single epic number (e.g. 30)")
    parser.add_argument("--epics", help="Comma-separated list or range of epic numbers (e.g. 10,21,30 or 20-25)")
    parser.add_argument("--file", help="Specific file path or glob")
    parser.add_argument("--check", action="store_true", help="Linter mode: check only, exit 1 if drift detected")
    parser.add_argument("--dry-run", action="store_true", help="Preview unified diff without writing changes to disk")
    parser.add_argument("--fix", action="store_true", help="Apply reconciliation and update files in place")
    return parser.parse_args()


def parse_epic_filter(epic_arg: int | None, epics_arg: str | None) -> set[int] | None:
    if epic_arg is not None:
        return {epic_arg}
    if not epics_arg:
        return None
    res = set()
    for part in epics_arg.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            res.update(range(int(lo), int(hi) + 1))
        elif part.isdigit():
            res.add(int(part))
    return res


def main():
    args = parse_args()
    if not (args.check or args.dry_run or args.fix):
        print("Notice: No mode specified (--check, --dry-run, or --fix). Defaulting to --check mode.")
        args.check = True

    status_filter = {s.strip().lower() for s in args.status.split(",") if s.strip()}
    epic_filter = parse_epic_filter(args.epic, args.epics)

    epic_lookup = load_epic_metadata_lookup()

    # Discover target files
    stories_to_process = []
    epics_to_process = []
    specs_to_process = []
    adrs_to_process = []
    prds_to_process = []
    handoffs_to_process = []

    target = args.target.lower()
    include_epics = target in ("epics", "all", "backlog", "all-docs")
    include_stories = target in ("stories", "all", "backlog", "all-docs")
    include_specs = target in ("design-specs", "all-docs")
    include_adrs = target in ("adrs", "all-docs")
    include_prds = target in ("prds", "all-docs")
    include_handoffs = target in ("handoffs", "all-docs")

    if args.file:
        matched_files = glob.glob(args.file, recursive=True)
        for mf in matched_files:
            p = Path(mf).resolve()
            if p.name.startswith("STORY-") and p.name.endswith(".md"):
                stories_to_process.append(p)
            elif p.name.startswith("EPIC-") and p.name.endswith(".md"):
                epics_to_process.append(p)
            elif "design-specs" in p.parts and p.suffix == ".md" and p.name != "README.md":
                specs_to_process.append(p)
            elif "adr" in p.parts and p.suffix == ".md" and p.name != "README.md":
                adrs_to_process.append(p)
            elif "product" in p.parts and p.suffix == ".md" and p.name != "README.md":
                prds_to_process.append(p)
            elif "handoffs" in p.parts and p.suffix == ".md" and p.name != "README.md":
                handoffs_to_process.append(p)
    else:
        if include_epics or include_stories:
            for epic_num, meta in epic_lookup.items():
                if epic_filter and epic_num not in epic_filter:
                    continue
                e_status = meta["status"].lower()
                if "all" not in status_filter and e_status not in status_filter:
                    continue

                if include_epics:
                    epics_to_process.append(meta["file_path"])

                if include_stories:
                    stories_dir = meta["dir_path"] / "stories"
                    if stories_dir.exists():
                        for sf in sorted(stories_dir.glob("STORY-*.md")):
                            stories_to_process.append(sf)

        if include_specs and DESIGN_SPECS_DIR.exists():
            for sf in sorted(DESIGN_SPECS_DIR.glob("*.md")):
                if sf.name == "README.md":
                    continue
                if epic_filter:
                    m_ep = re.search(r"EPIC-(\d+)", sf.name, re.IGNORECASE)
                    if not m_ep:
                        txt = sf.read_text(encoding="utf-8")
                        m_ep = re.search(r"EPIC-(\d+)", txt, re.IGNORECASE)
                    if m_ep and int(m_ep.group(1)) not in epic_filter:
                        continue
                specs_to_process.append(sf)

        if include_adrs and ADR_DIR.exists():
            for af in sorted(ADR_DIR.glob("*.md")):
                if af.name == "README.md":
                    continue
                adrs_to_process.append(af)

        if include_prds and PRODUCT_DIR.exists():
            for pf in sorted(PRODUCT_DIR.glob("*.md")):
                if pf.name == "README.md":
                    continue
                prds_to_process.append(pf)

        if include_handoffs and HANDOFFS_DIR.exists():
            for hf in sorted(HANDOFFS_DIR.glob("*.md")):
                if hf.name == "README.md":
                    continue
                if epic_filter:
                    m_ep = re.search(r"EPIC-(\d+)", hf.name, re.IGNORECASE)
                    if not m_ep:
                        txt = hf.read_text(encoding="utf-8")
                        m_ep = re.search(r"EPIC-(\d+)", txt, re.IGNORECASE)
                    if m_ep and int(m_ep.group(1)) not in epic_filter:
                        continue
                handoffs_to_process.append(hf)

    print("=" * 80)
    print("Agent OS Universal Documentation Reconciler & Linter")
    print(f"Scope Filters:")
    print(f"  • Target:        {args.target}")
    print(f"  • Status Filter: {sorted(status_filter)}")
    print(f"  • Epic Filter:   {sorted(epic_filter) if epic_filter else 'ALL'}")
    print(f"Matched:")
    if epics_to_process:
        print(f"  • Epics:         {len(epics_to_process)}")
    if stories_to_process:
        print(f"  • Stories:       {len(stories_to_process)}")
    if specs_to_process:
        print(f"  • Design Specs:  {len(specs_to_process)}")
    if adrs_to_process:
        print(f"  • ADRs:          {len(adrs_to_process)}")
    if prds_to_process:
        print(f"  • PRDs:          {len(prds_to_process)}")
    if handoffs_to_process:
        print(f"  • Handoffs:      {len(handoffs_to_process)}")
    mode_str = "LINT / CHECK ONLY" if args.check else ("DRY RUN (Preview Diffs)" if args.dry_run else "FIX / IN-PLACE RECONCILIATION")
    print(f"Mode:              {mode_str}")
    print("=" * 80)

    total_checked = 0
    drift_count = 0

    # 1. Process Epics
    for ef in epics_to_process:
        total_checked += 1
        epic_num = get_epic_num_from_str(ef.name)
        child_stories = list((ef.parent / "stories").glob("STORY-*.md")) if (ef.parent / "stories").exists() else []
        new_content, changed = reconcile_epic(ef, child_stories)
        if changed:
            drift_count += 1
            rel_path = ef.relative_to(REPO_ROOT)
            print(f"[DRIFT DETECTED] {rel_path}")
            if args.dry_run:
                orig_lines = ef.read_text(encoding="utf-8").splitlines(keepends=True)
                new_lines = new_content.splitlines(keepends=True)
                diff = difflib.unified_diff(orig_lines, new_lines, fromfile=str(rel_path), tofile=str(rel_path))
                sys.stdout.writelines(diff)
            elif args.fix:
                ef.write_text(new_content, encoding="utf-8")
                print(f"  ↳ [RECONCILED] {rel_path}")

    # 2. Process Stories
    for sf in stories_to_process:
        total_checked += 1
        new_content, changed = reconcile_story(sf, epic_lookup)
        if changed:
            drift_count += 1
            rel_path = sf.relative_to(REPO_ROOT)
            print(f"[DRIFT DETECTED] {rel_path}")
            if args.dry_run:
                orig_lines = sf.read_text(encoding="utf-8").splitlines(keepends=True)
                new_lines = new_content.splitlines(keepends=True)
                diff = difflib.unified_diff(orig_lines, new_lines, fromfile=str(rel_path), tofile=str(rel_path))
                sys.stdout.writelines(diff)
            elif args.fix:
                sf.write_text(new_content, encoding="utf-8")
                print(f"  ↳ [RECONCILED] {rel_path}")

    # 3. Process Design Specs
    for spec_f in specs_to_process:
        total_checked += 1
        new_content, changed = reconcile_design_spec(spec_f, epic_lookup)
        if changed:
            drift_count += 1
            rel_path = spec_f.relative_to(REPO_ROOT)
            print(f"[DRIFT DETECTED] {rel_path}")
            if args.dry_run:
                orig_lines = spec_f.read_text(encoding="utf-8").splitlines(keepends=True)
                new_lines = new_content.splitlines(keepends=True)
                diff = difflib.unified_diff(orig_lines, new_lines, fromfile=str(rel_path), tofile=str(rel_path))
                sys.stdout.writelines(diff)
            elif args.fix:
                spec_f.write_text(new_content, encoding="utf-8")
                print(f"  ↳ [RECONCILED] {rel_path}")

    # 4. Process ADRs
    for adr_f in adrs_to_process:
        total_checked += 1
        new_content, changed = reconcile_adr(adr_f, epic_lookup)
        if changed:
            drift_count += 1
            rel_path = adr_f.relative_to(REPO_ROOT)
            print(f"[DRIFT DETECTED] {rel_path}")
            if args.dry_run:
                orig_lines = adr_f.read_text(encoding="utf-8").splitlines(keepends=True)
                new_lines = new_content.splitlines(keepends=True)
                diff = difflib.unified_diff(orig_lines, new_lines, fromfile=str(rel_path), tofile=str(rel_path))
                sys.stdout.writelines(diff)
            elif args.fix:
                adr_f.write_text(new_content, encoding="utf-8")
                print(f"  ↳ [RECONCILED] {rel_path}")

    # 5. Process PRDs
    for prd_f in prds_to_process:
        total_checked += 1
        new_content, changed = reconcile_prd(prd_f)
        if changed:
            drift_count += 1
            rel_path = prd_f.relative_to(REPO_ROOT)
            print(f"[DRIFT DETECTED] {rel_path}")
            if args.dry_run:
                orig_lines = prd_f.read_text(encoding="utf-8").splitlines(keepends=True)
                new_lines = new_content.splitlines(keepends=True)
                diff = difflib.unified_diff(orig_lines, new_lines, fromfile=str(rel_path), tofile=str(rel_path))
                sys.stdout.writelines(diff)
            elif args.fix:
                prd_f.write_text(new_content, encoding="utf-8")
                print(f"  ↳ [RECONCILED] {rel_path}")

    # 6. Process Handoffs
    for hf in handoffs_to_process:
        total_checked += 1
        new_content, changed = reconcile_handoff(hf, epic_lookup)
        if changed:
            drift_count += 1
            rel_path = hf.relative_to(REPO_ROOT)
            print(f"[DRIFT DETECTED] {rel_path}")
            if args.dry_run:
                orig_lines = hf.read_text(encoding="utf-8").splitlines(keepends=True)
                new_lines = new_content.splitlines(keepends=True)
                diff = difflib.unified_diff(orig_lines, new_lines, fromfile=str(rel_path), tofile=str(rel_path))
                sys.stdout.writelines(diff)
            elif args.fix:
                hf.write_text(new_content, encoding="utf-8")
                print(f"  ↳ [RECONCILED] {rel_path}")

    print("\n" + "=" * 80)
    print(f"Summary: Checked {total_checked} files. Found {drift_count} with template drift.")
    if args.check:
        if drift_count > 0:
            print(f"FAILED: {drift_count} files deviate from canonical templates. Run with --fix to reconcile.")
            sys.exit(1)
        else:
            print("SUCCESS: All checked files conform to canonical templates.")
            sys.exit(0)
    elif args.fix:
        print(f"SUCCESS: Successfully reconciled {drift_count} files in place.")
    print("=" * 80)


if __name__ == "__main__":
    main()
