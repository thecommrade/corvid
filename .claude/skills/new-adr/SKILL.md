---
name: new-adr
description: Create the next ADR in docs/adr/ from TEMPLATE.md, honouring reserved numbers (0002 membership, 0003 endpoints, 0004 exit criteria on a one-LAN fleet, 0005 contribution slider; a topology ADR takes 0006), link it from docs/status.md, and — when the decision introduces a dependency — add the CLAUDE.md §4 row in the same commit via add-dependency.
---

# new-adr

1. Number: if the title matches a reserved slot use that number; else `printf '%04d' $(( $(ls docs/adr | grep -oE '^[0-9]{4}' | sort -n | tail -1 | sed 's/^0*//') + 1 ))`.
2. `cp docs/adr/TEMPLATE.md docs/adr/NNNN-<slug>.md`; fill **every** section (Status, Date, Deciders, Related, Context with sourced facts, Decision as testable statements, Consequences, §4 rows or "none"). No empty sections.
3. Dependency introduced? Run the `add-dependency` skill now (same commit).
4. Append a row to the decisions table in `docs/status.md` (use `save-state`).
5. `bash scripts/lint-placeholders.sh` → ok.
6. Commit: `git add docs/adr/NNNN-<slug>.md docs/status.md [CLAUDE.md] && git commit -m "docs(adr): ADR-NNNN <title>"` (+ Co-Authored-By trailer).
