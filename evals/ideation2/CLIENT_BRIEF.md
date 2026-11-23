# Ideation eval client brief (I13 re-run; same protocol as I7)

You are the client model of an ideation evaluation. Repo: /home/user/pos (do not edit anything outside your own
directory evals/ideation2/<pid>/, do not commit, do not git anything). Your instructions are the rendered `ideate`
prompt in evals/ideation2/<pid>/prompt.md: read it first and follow it as if a user had sent it. Stop after the gate
(Step 3 / validate_slate): do NOT run `slate run`, preflight or any full run; the evaluator does that.

The MCP tools are not connected; use these CLI equivalents from /home/user/pos:
- resolve:      python -m pos_catalogue resolve KIND "Name"
- search:       python -m pos_catalogue search --help (filters by kind, text, ascendancy ...)
- enablers:     python -m pos_catalogue enablers "SkillType"
- bridges:      python -m pos_catalogue bridges "term a" "term b"
- explain:      python -m pos_catalogue explain KIND "Name or id"
- validate_spec: python -m pos_pipeline validate spec.yaml
- sweep:        python -m pos_pipeline sweep probe.yaml KIND 1 [top] [--weapon "Base"]   (ALWAYS 1 worker: the machine is shared; a sweep takes 1-5 min)
- validate_slate: python -m pos_pipeline slate validate slate.yaml
Run `--help` on a command if its arguments are unclear. Pipe long output through head/grep; do not dump whole JSON.

Files to write in evals/ideation2/<pid>/:
- round1.yaml, round2.yaml, ... : every slate you submit to validate_slate, in order, unchanged after submission;
- final.yaml : the slate you end with (copy of the last round);
- probe*.yaml : any sweep probe specs; sweep output summaries go in notes.md;
- notes.md with sections: (a) tool-call counts by tool; (b) names recalled from memory and whether resolve found
  them exact (list the misses and what you used instead); (c) ideas dropped and why; (d) which candidates you think
  are non-obvious and why; (e) declared `conditions`: for each candidate, which conditions you declared, where the
  build sustains them, and whether they hold against a lone boss (Arbiter of Ash) and in Breach packs; (f) friction:
  anything in the prompt or tools that was unclear or wrong.
Final answer to the evaluator: under 150 words: rounds used, kept count, sweeps run (and whether any candidate came
from one), anything that broke.
