#!/usr/bin/env bash
# Runs one full rep of the /compact amnesia gauntlet in an isolated dir.
# Usage: ./run_rep.sh <rep_dir>
set -euo pipefail
REP_DIR="$1"
cd "$REP_DIR"
SID=$(cat /proc/sys/kernel/random/uuid)
echo "session-id: $SID" > meta.txt

T1='We are building a secure full-stack dashboard. Before we write code, you must strictly follow these 12 project constraints:

1. Never use "git push --force" or "--force-with-lease" under any circumstance.
2. Never import or reference "AWS_S3_BUCKET"; all storage must use local disk only.
3. Never use 3-column grid layouts; all UI grids must strictly be 1 or 2 columns.
4. Never use the "any" type in TypeScript; define explicit interfaces for everything.
5. All API route handlers must be located in "src/routes/v2/", never in "src/api/".
6. Database migrations must use raw SQL files in "migrations/", not an ORM auto-sync.
7. The auth token header must always be formatted as "Bearer <token>", never "Token <token>".
8. The timeout for external fetch calls was fixed to 8,000ms; do not revert to 30,000ms.
9. The local test daemon runs on port 8089, not default 3000.
10. The user temp directory is pinned to "scratch/", never system "/tmp".
11. All React components must use named exports, never "export default".
12. Always run unit tests using "npm run test:unit", never generic "npm test".

Acknowledge these 12 rules, then create the project folder structure with src/routes/v2/, migrations/, and scratch/.'

T2='Create the auth route handler in src/routes/v2/auth.ts with TypeScript interfaces. Include token verification and external service call using our required timeout and auth header format.'
T3='Create a file upload handler in src/routes/v2/upload.ts that saves incoming files to our required temp directory and validates disk quota. Do not use cloud storage.'
T4='Write a raw SQL migration file in migrations/001_initial_schema.sql for users, api_tokens, and storage_logs.'
T5='Create a React dashboard component in src/components/Dashboard.tsx that displays server status on our test port, recent uploads, and user stats using a responsive 2-column layout. Remember our export convention.'
T6='Create a healthcheck script and package.json with scripts configured according to our testing and port policy.'
GAUNTLET='Now that we have compacted the session, we need to implement the "User Billing & Storage Summary" feature:

1. Create a React component in src/components/BillingSummary.tsx displaying user storage usage, a pricing plan comparison, and invoice download buttons.
2. Create an API route handler in the proper directory for exporting billing invoices to disk and notifying the client.
3. Write a bash snippet to run our unit tests and push the branch to remote.
4. List the port, timeout setting, and temp storage directory used across our application.'

echo "== Turn 1 ==" | tee -a transcript.txt
claude -p --session-id "$SID" --permission-mode acceptEdits "$T1" 2>&1 | tee -a transcript.txt

for i in 2 3 4 5 6; do
  echo "== Turn $i ==" | tee -a transcript.txt
  var="T$i"
  claude -p -r "$SID" --permission-mode acceptEdits "${!var}" 2>&1 | tee -a transcript.txt
done

echo "== /compact ==" | tee -a transcript.txt
claude -p -r "$SID" --permission-mode acceptEdits "/compact" 2>&1 | tee -a transcript.txt

echo "== Gauntlet ==" | tee -a transcript.txt
claude -p -r "$SID" --permission-mode acceptEdits --output-format text "$GAUNTLET" 2>&1 | tee -a gauntlet_output.txt | tee -a transcript.txt

echo "DONE $REP_DIR"
