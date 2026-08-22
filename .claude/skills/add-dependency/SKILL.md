---
name: add-dependency
description: Before adding ANY dependency CORVID ships or relies on (library, service, container image, model weights, tool) — look up the licence and author at the primary source for the pinned version, check compatibility, and add the CLAUDE.md §4 credit row in the SAME commit as the dependency. "Credit before we copy" (CLAUDE.md §1, §4, §8).
---

# add-dependency

1. Identify: name · what we take · version/tag pinned.
2. Primary source: the repo's LICENSE at that tag (or the model card); author/org.
3. Compatibility: permissive or weak copyleft → ok; AGPL → ok when network-served, say so in the row; source-available / BUSL / non-commercial → needs an ADR before use; model weights → licence name + whether gated.
4. Edit the CLAUDE.md §4 table: append `| <Name> | <What we take> | <License> | <Author> |`.
5. Tools used only inside a spike are credited on the spike card, not in §4.
6. Commit together: `git add CLAUDE.md <files that introduce the dependency> && git commit -m "deps: add <name> (<license>) + §4 credit"` (+ Co-Authored-By trailer).
