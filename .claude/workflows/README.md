# Workflows

Claude Code **Workflow-tool scripts** (plain JavaScript, each beginning with `export const meta = {…}`), invoked by name with the Workflow tool. `research-sweep.js` (M2) runs the adversarially verified research sweep for the dossiers (spec §6.4); a `code-review.js` arrives with the first code (Phase 2). Scripts never run spikes on nodes — the main session does (spec §6.4).
