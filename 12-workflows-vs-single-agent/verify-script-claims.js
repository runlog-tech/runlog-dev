export const meta = {
  name: 'verify-script-claims',
  description: 'Extract the load-bearing factual claims from a video script, verify each against primary sources, then adversarially try to refute the survivors',
  whenToUse: 'Before rendering a RUNLOG video: check every claim like "tool A can, tool B cannot" against official docs or repo receipts',
  phases: [
    { title: 'Extract', detail: 'one agent lists the load-bearing claims' },
    { title: 'Verify', detail: 'one agent per claim checks primary sources' },
    { title: 'Refute', detail: 'one skeptic per surviving claim tries to break it' },
  ],
}

const MAX_CLAIMS = args.maxClaims || 8
const SCRIPT = args.scriptPath

const CLAIMS_SCHEMA = {
  type: 'object',
  required: ['claims'],
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'text', 'line', 'kind', 'thesisWeight'],
        properties: {
          id: { type: 'string' },
          text: { type: 'string', description: 'The claim, quoted or tightly paraphrased from the script' },
          line: { type: 'number', description: 'Line number in the script file' },
          kind: { type: 'string', enum: ['tool-capability', 'own-measurement', 'number', 'other'] },
          thesisWeight: { type: 'number', description: '1-5: how much the video thesis collapses if this claim is false' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'evidence', 'source'],
  properties: {
    verdict: { type: 'string', enum: ['supported', 'contradicted', 'unverifiable'] },
    evidence: { type: 'string', description: 'What the primary source actually says, quoted' },
    source: { type: 'string', description: 'URL or file:line of the primary source' },
  },
}

const REFUTE_SCHEMA = {
  type: 'object',
  required: ['refuted', 'evidence', 'source'],
  properties: {
    refuted: { type: 'boolean' },
    evidence: { type: 'string' },
    source: { type: 'string' },
  },
}

phase('Extract')
const ext = await agent(
  `Read the video script at ${SCRIPT}. List the factual claims that a viewer would take as true about how tools behave or what was measured. Skip transitions, opinions and visual directions.\n` +
  `For each claim give a line number, a kind, and thesisWeight 1-5 (5 = the video's whole argument collapses if this is false). ` +
  `Prioritise claims of the form "tool A can do X / tool B cannot", comparisons, and any number presented as a measured result. ` +
  `Read-only: do not edit any file.`,
  { label: 'extract-claims', phase: 'Extract', schema: CLAIMS_SCHEMA },
)

const all = (ext?.claims || []).sort((a, b) => b.thesisWeight - a.thesisWeight)
const claims = all.slice(0, MAX_CLAIMS)
log(`${all.length} claims extracted; verifying top ${claims.length} by thesisWeight; dropped ${all.length - claims.length}: ${all.slice(MAX_CLAIMS).map(c => c.id).join(', ') || 'none'}`)

const results = await pipeline(
  claims,
  c => agent(
    `You are checking one claim from a video script (${SCRIPT}, line ${c.line}).\n\nCLAIM: ${c.text}\nKIND: ${c.kind}\n\n` +
    `Find the PRIMARY source and decide if the claim is true as stated. Primary sources, in order of preference: the tool's official documentation (use WebFetch/WebSearch; Claude Code docs live under https://code.claude.com/docs/en/), vendored docs or source in this repo, raw receipts (JSON/logs) in this repo for own-measurement claims, read-only local commands such as \`claude --help\`. ` +
    `Do NOT trust the script itself, a harness the script's author wrote, or a third-party video as evidence. Do not run paid model sessions. Read-only: edit nothing.\n` +
    `For "A can, B cannot" claims you must check BOTH sides' primary sources. ` +
    `verdict: supported = a primary source confirms it as stated; contradicted = a primary source shows it false or overstated; unverifiable = no primary source found.`,
    { label: `verify:${c.id}`, phase: 'Verify', schema: VERDICT_SCHEMA },
  ),
  (v, c) => {
    if (!v || v.verdict !== 'supported') return { claim: c, verdict: v, refutation: null }
    return agent(
      `A checker concluded this video-script claim is SUPPORTED:\n\nCLAIM: ${c.text}\nCHECKER EVIDENCE: ${v.evidence}\nCHECKER SOURCE: ${v.source}\n\n` +
      `Your job is to refute it. Assume the checker missed something: a feature on the other side of a comparison, a newer docs page, a setting, an exception, an overstated word like "only" or "never". ` +
      `Search the primary sources (official docs via WebFetch/WebSearch, repo files) for anything that shows the claim is false or overstated. ` +
      `refuted=true only if you find concrete source text that contradicts it; refuted=false if you honestly cannot. Read-only: edit nothing.`,
      { label: `refute:${c.id}`, phase: 'Refute', schema: REFUTE_SCHEMA },
    ).then(r => ({ claim: c, verdict: v, refutation: r }))
  },
)

const rows = results.filter(Boolean)
const flagged = rows.filter(r =>
  !r.verdict || r.verdict.verdict !== 'supported' || (r.refutation && r.refutation.refuted))
return {
  script: SCRIPT,
  extracted: all.length,
  checked: claims.length,
  flagged: flagged.map(r => ({
    id: r.claim.id, line: r.claim.line, text: r.claim.text, weight: r.claim.thesisWeight,
    verdict: r.verdict?.verdict ?? 'agent-failed',
    refuted: r.refutation?.refuted ?? null,
    evidence: r.refutation?.refuted ? r.refutation.evidence : r.verdict?.evidence,
    source: r.refutation?.refuted ? r.refutation.source : r.verdict?.source,
  })),
  passed: rows.filter(r => !flagged.includes(r)).map(r => ({ id: r.claim.id, line: r.claim.line, text: r.claim.text, source: r.verdict.source })),
}