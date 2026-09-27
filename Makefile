# AgentOS Sandbox — Makefile
.DEFAULT_GOAL := help

## Show this help menu of available commands.
help:
	@echo "AgentOS Sandbox — Makefile Commands:"
	@echo ""
	@awk '/^## / { \
		if (helpMessage == "") { \
			helpMessage = substr($$0, 4); \
		} \
	} \
	/^[a-zA-Z\-_0-9]+:/ { \
		if (helpMessage != "") { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			printf "  %-16s %s\n", helpCommand, helpMessage; \
			helpMessage = ""; \
		} \
	}' $(MAKEFILE_LIST)
	@echo ""


# ------------------------------------------------------------------------------
# Documentation & Governance Scaffolding Targets
# ------------------------------------------------------------------------------

## Regenerate docs/status-dashboard.html directly from canonical backlog documents.
dashboard:
	python3 scripts/generate_status_dashboard.py

## Reconcile docs/STATUS.md with the canonical story documents on disk (zero drift).
sync-status:
	python3 scripts/generate_status_dashboard.py --sync

## Scaffold a new Epic directory & plan: make new-epic ID=1 SLUG=user-auth TITLE="User Authentication"
new-epic:
	@test -n "$(ID)" || (echo "Usage: make new-epic ID=<num> SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@test -n "$(SLUG)" || (echo "Usage: make new-epic ID=<num> SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \
	mkdir -p docs/backlog/epic-$(ID)-$(SLUG)/stories; \
	sed -e 's/EPIC-X/EPIC-$(ID)/g' \
	    -e 's/Epic X/Epic $(ID)/g' \
	    -e 's/\[Initiative \/ Capability Title\]/$(TITLE)/g' \
	    docs/templates/EPIC-TEMPLATE.md > docs/backlog/epic-$(ID)-$(SLUG)/EPIC-$(ID)-$$UPPER_SLUG.md; \
	echo "Created docs/backlog/epic-$(ID)-$(SLUG)/EPIC-$(ID)-$$UPPER_SLUG.md and stories/ directory."

## Scaffold a new Story specification: make new-story EPIC_ID=1 STORY_NUM=1 SLUG=jwt-login TITLE="JWT Login"
new-story:
	@test -n "$(EPIC_ID)" || (echo "Usage: make new-story EPIC_ID=<num> STORY_NUM=<subnum> SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@test -n "$(STORY_NUM)" || (echo "Usage: make new-story EPIC_ID=<num> STORY_NUM=<subnum> SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@test -n "$(SLUG)" || (echo "Usage: make new-story EPIC_ID=<num> STORY_NUM=<subnum> SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@TARGET_DIR=$$(find docs/backlog -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); \
	if [ -z "$$TARGET_DIR" ]; then TARGET_DIR=$$(find docs/roadmap -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); fi; \
	if [ -z "$$TARGET_DIR" ]; then echo "Epic directory for Epic $(EPIC_ID) not found in docs/backlog/"; exit 1; fi; \
	EPIC_FOLDER=$$(basename "$$TARGET_DIR"); \
	EPIC_FILE=$$(ls "$$TARGET_DIR" | grep '^EPIC-' | head -n 1); \
	UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \
	sed -e 's/STORY-X\.Y/STORY-$(EPIC_ID).$(STORY_NUM)/g' \
	    -e 's/Story X\.Y/Story $(EPIC_ID).$(STORY_NUM)/g' \
	    -e 's/EPIC-X/EPIC-$(EPIC_ID)/g' \
	    -e 's/Epic X/Epic $(EPIC_ID)/g' \
	    -e 's/\[Story Title\]/$(TITLE)/g' \
	    -e "s|epic-X-NAME/EPIC-X-NAME\.md|$$EPIC_FOLDER/$$EPIC_FILE|g" \
	    -e "s|\.\./EPIC-X-NAME\.md|\.\./$$EPIC_FILE|g" \
	    docs/templates/STORY-TEMPLATE.md > "$$TARGET_DIR/stories/STORY-$(EPIC_ID).$(STORY_NUM)-$$UPPER_SLUG.md"; \
	echo "Created $$TARGET_DIR/stories/STORY-$(EPIC_ID).$(STORY_NUM)-$$UPPER_SLUG.md"

## Scaffold a new Architecture Decision Record: make new-adr ID=1 SLUG=use-postgres TITLE="Use Postgres"
new-adr:
	@test -n "$(ID)" || (echo "Usage: make new-adr ID=<num> SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@test -n "$(SLUG)" || (echo "Usage: make new-adr ID=<num> SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@PADDED_ID=$$(printf "%04d" $(ID)); \
	LOWER_SLUG=$$(echo "$(SLUG)" | tr '[:upper:]' '[:lower:]'); \
	TODAY=$$(date +%Y-%m-%d); \
	sed -e "s/ADR-000X/ADR-$$PADDED_ID/g" \
	    -e "s/ADR 000X/ADR $$PADDED_ID/g" \
	    -e 's/\[Short, Descriptive Title of Decision\]/$(TITLE)/g' \
	    -e "s/YYYY-MM-DD/$$TODAY/g" \
	    docs/templates/ADR-TEMPLATE.md > docs/adr/$$PADDED_ID-$$LOWER_SLUG.md; \
	echo "Created docs/adr/$$PADDED_ID-$$LOWER_SLUG.md"

## Scaffold a new Product Requirements Document: make new-prd SLUG=member-portal TITLE="Member Portal"
new-prd:
	@test -n "$(SLUG)" || (echo "Usage: make new-prd SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \
	TODAY=$$(date +%Y-%m-%d); \
	sed -e "s/PRD-\[NAME\]/PRD-$$UPPER_SLUG/g" \
	    -e 's/\[Product Initiative \/ Feature Requirements\]/$(TITLE)/g' \
	    -e 's/\[Initiative Name\]/$(TITLE)/g' \
	    -e "s/YYYY-MM-DD/$$TODAY/g" \
	    docs/templates/PRD-TEMPLATE.md > docs/product/PRD-$$UPPER_SLUG.md; \
	echo "Created docs/product/PRD-$$UPPER_SLUG.md"

## Scaffold a new Feature Design Spec: make new-design-spec SLUG=checkout-flow TITLE="Checkout Flow"
new-design-spec:
	@test -n "$(SLUG)" || (echo "Usage: make new-design-spec SLUG=<slug> TITLE=\"<Title>\"" && exit 1)
	@UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \
	TODAY=$$(date +%Y-%m-%d); \
	sed -e "s/SPEC-\[NAME\]/SPEC-$$UPPER_SLUG/g" \
	    -e 's/\[Feature \/ Subsystem Design Specification\]/$(TITLE)/g' \
	    -e 's/\[Feature Name\]/$(TITLE)/g' \
	    -e "s/YYYY-MM-DD/$$TODAY/g" \
	    docs/templates/DESIGN-SPEC-TEMPLATE.md > docs/design-specs/$$UPPER_SLUG.md; \
	echo "Created docs/design-specs/$$UPPER_SLUG.md"

## Scaffold a new Epic Handoff document: make new-handoff EPIC_ID=1
new-handoff:
	@test -n "$(EPIC_ID)" || (echo "Usage: make new-handoff EPIC_ID=<num>" && exit 1)
	@TARGET_DIR=$$(find docs/backlog -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); \
	if [ -z "$$TARGET_DIR" ]; then TARGET_DIR=$$(find docs/roadmap -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); fi; \
	if [ -z "$$TARGET_DIR" ]; then echo "Epic directory for Epic $(EPIC_ID) not found in docs/backlog/"; exit 1; fi; \
	EPIC_FOLDER=$$(basename "$$TARGET_DIR"); \
	EPIC_FILE=$$(ls "$$TARGET_DIR" | grep '^EPIC-' | head -n 1); \
	TODAY=$$(date +%Y-%m-%d); \
	sed -e "s/HANDOFF-EPIC-X/HANDOFF-EPIC-$(EPIC_ID)/g" \
	    -e "s/EPIC-X/EPIC-$(EPIC_ID)/g" \
	    -e "s/Epic X/Epic $(EPIC_ID)/g" \
	    -e "s|epic-X-NAME/EPIC-X-NAME\.md|$$EPIC_FOLDER/$$EPIC_FILE|g" \
	    -e "s/YYYY-MM-DD/$$TODAY/g" \
	    docs/templates/HANDOFF-TEMPLATE.md > "docs/history/handoffs/HANDOFF-EPIC-$(EPIC_ID).md"; \
	echo "Created docs/history/handoffs/HANDOFF-EPIC-$(EPIC_ID).md"

## Install GitHub PR template or scaffold PR completion note: make new-pr [OUT=.github/pull_request_template.md]
new-pr:
	@mkdir -p .github
	@if [ -n "$(OUT)" ]; then \
		cp docs/templates/PR-TEMPLATE.md "$(OUT)"; \
		echo "Created $(OUT)"; \
	else \
		cp docs/templates/PR-TEMPLATE.md .github/pull_request_template.md; \
		echo "Installed .github/pull_request_template.md"; \
	fi

## Package the portable governance toolkit into dist/agent-os-governance-kit.zip: make package-kit [DEST=~/Desktop]
package-kit:
	@mkdir -p dist
	@python3 -c "import zipfile; from pathlib import Path; root = Path('$(CURDIR)'); z = zipfile.ZipFile(root / 'dist/agent-os-governance-kit.zip', 'w', zipfile.ZIP_DEFLATED); [z.write(root / f, f) for f in ['scripts/bootstrap_governance.py', 'scripts/generate_status_dashboard.py', 'docs/status-dashboard.template.html', 'docs/templates/PRD-TEMPLATE.md', 'docs/templates/EPIC-TEMPLATE.md', 'docs/templates/STORY-TEMPLATE.md', 'docs/templates/ADR-TEMPLATE.md', 'docs/templates/DESIGN-SPEC-TEMPLATE.md', 'docs/templates/HANDOFF-TEMPLATE.md', 'docs/templates/PR-TEMPLATE.md', 'docs/templates/README.md'] if (root / f).exists()]"
	@if [ -n "$(DEST)" ]; then python3 -c "import shutil, os, sys; dest = os.path.expanduser(sys.argv[1]); shutil.copy2('dist/agent-os-governance-kit.zip', dest); print(f'Copied to {dest}/agent-os-governance-kit.zip' if os.path.isdir(dest) else f'Copied to {dest}')" "$(DEST)"; fi
	@echo "Packaged dist/agent-os-governance-kit.zip ($$(du -h dist/agent-os-governance-kit.zip | cut -f1))"

