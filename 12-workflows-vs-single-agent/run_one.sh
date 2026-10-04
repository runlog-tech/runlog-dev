#!/usr/bin/env bash
# usage: run_one.sh <single|workflow> <script-slug> <rep>
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=/home/invii/faceless-yt-transformation
arm=$1; slug=$2; rep=$3
out="$HERE/runs/${slug}-${arm}-r${rep}"; mkdir -p "$out"
script="$REPO/scripts/$slug/script.md"
ALLOW="Read,Grep,Glob,WebFetch,WebSearch,Bash(claude --help:*),Bash(claude --version),Bash(ls:*),Bash(cat:*),Bash(grep:*),Bash(find:*),Bash(head:*),Bash(wc:*)"
DENY="Edit,Write,NotebookEdit"
if [ "$arm" = workflow ]; then
  mkdir -p "$REPO/.scratch" && cp "$HERE/verify-script-claims.js" "$REPO/.scratch/verify-script-claims.js"  # Workflow tool only accepts scriptPath inside the cwd
  prompt=$(sed -e "s#{WF}#$REPO/.scratch/verify-script-claims.js#" -e "s#{SCRIPT}#$script#" "$HERE/prompts/workflow.txt")
  allow="$ALLOW,Workflow"; deny="$DENY"
else
  prompt=$(sed -e "s#{SCRIPT}#$script#" "$HERE/prompts/single.txt")
  allow="$ALLOW"; deny="$DENY,Workflow"
fi
cd "$REPO" || exit 1
claude -p "/usage" </dev/null > "$out/usage-before.txt" 2>&1
date -Iseconds > "$out/started.txt"
timeout 1800 claude -p "$prompt" --allowedTools "$allow" --disallowedTools "$deny" --output-format json </dev/null > "$out/result.json" 2> "$out/stderr.txt"
echo $? > "$out/exit-code.txt"
date -Iseconds > "$out/ended.txt"
sleep 5
claude -p "/usage" </dev/null > "$out/usage-after.txt" 2>&1
sed -n 3,4p "$out/usage-before.txt" | sed 's/^/before: /'
sed -n 3,4p "$out/usage-after.txt" | sed 's/^/after:  /'
