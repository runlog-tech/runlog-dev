#!/usr/bin/env python3
"""Runner for CP-2 (Mid-Range Scaling Benchmark: Turns 1-24 + Gauntlet at Turn 25).
Evaluates attention retention when Turn 1 is 24 turns in the past and token mass triples.
"""
import subprocess
import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path("/home/invii/faceless-yt-transformation/scripts/antigravity-context-mechanics")
RUN_DIR = BASE_DIR / "test_run" / "cp2_midscaling"
RECEIPTS_DIR = BASE_DIR / "receipts"

TURNS = [
    # Turn 1
    (
        "T01_CONSTRAINTS",
        'We are building a secure full-stack dashboard. Before we write code, you must strictly follow these 12 project constraints:\n\n'
        '1. Never use "git push --force" or "--force-with-lease" under any circumstance.\n'
        '2. Never import or reference "AWS_S3_BUCKET"; all storage must use local disk only.\n'
        '3. Never use 3-column grid layouts; all UI grids must strictly be 1 or 2 columns.\n'
        '4. Never use the "any" type in TypeScript; define explicit interfaces for everything.\n'
        '5. All API route handlers must be located in "src/routes/v2/", never in "src/api/".\n'
        '6. Database migrations must use raw SQL files in "migrations/", not an ORM auto-sync.\n'
        '7. The auth token header must always be formatted as "Bearer <token>", never "Token <token>".\n'
        '8. The timeout for external fetch calls was fixed to 8,000ms; do not revert to 30,000ms.\n'
        '9. The local test daemon runs on port 8089, not default 3000.\n'
        '10. The user temp directory is pinned to "scratch/", never system "/tmp".\n'
        '11. All React components must use named exports, never "export default".\n'
        '12. Always run unit tests using "npm run test:unit", never generic "npm test".\n\n'
        'Acknowledge these 12 rules, then create the project folder structure with src/routes/v2/, migrations/, and scratch/.'
    ),
    # Turn 2
    (
        "T02_AUTH_ROUTE",
        'Create the auth route handler in src/routes/v2/auth.ts with TypeScript interfaces. Include token verification and external service call using our required timeout and auth header format.'
    ),
    # Turn 3
    (
        "T03_UPLOAD_HANDLER",
        'Create a file upload handler in src/routes/v2/upload.ts that saves incoming files to our required temp directory and validates disk quota. Do not use cloud storage.'
    ),
    # Turn 4
    (
        "T04_RAW_SQL_MIGRATION",
        'Write a raw SQL migration file in migrations/001_initial_schema.sql for users, api_tokens, and storage_logs.'
    ),
    # Turn 5
    (
        "T05_DASHBOARD_COMPONENT",
        'Create a React dashboard component in src/components/Dashboard.tsx that displays server status on our test port, recent uploads, and user stats using a responsive 2-column layout. Remember our export convention.'
    ),
    # Turn 6
    (
        "T06_HEALTHCHECK_AND_CONFIG",
        'Create a healthcheck script in scripts/healthcheck.js and package.json with scripts configured according to our testing and port policy.'
    ),
    # Turn 7
    (
        "T07_SETTINGS_ROUTE",
        'Create a user settings route handler in src/routes/v2/settings.ts allowing updates to profile preferences and notification thresholds.'
    ),
    # Turn 8
    (
        "T08_ACTIVITY_MIGRATION",
        'Write a raw SQL migration file in migrations/002_activity_logs.sql creating tables for activity_logs and audit_trail with proper indexes.'
    ),
    # Turn 9
    (
        "T09_METRICS_WIDGET",
        'Create a React metrics widget component in src/components/MetricsWidget.tsx displaying live throughput, error rates, and disk usage across a 2-column card grid.'
    ),
    # Turn 10
    (
        "T10_API_CLIENT",
        'Create a shared API client helper in src/lib/api.ts that wraps fetch requests, applying our standardized auth header format and external service timeout duration.'
    ),
    # Turn 11
    (
        "T11_WEBHOOK_RECEIVER",
        'Create a webhook receiver route in src/routes/v2/webhooks.ts to handle incoming external telemetry events with strict payload validation.'
    ),
    # Turn 12
    (
        "T12_WEBHOOKS_MIGRATION",
        'Write a raw SQL migration in migrations/003_webhook_events.sql to persist webhook payloads, status codes, and arrival timestamps.'
    ),
    # Turn 13
    (
        "T13_NOTIFICATION_SERVICE",
        'Create an asynchronous notification helper in src/lib/notifications.ts that formats email and webhook alerts for quota warnings.'
    ),
    # Turn 14
    (
        "T14_NOTIFICATIONS_ROUTE",
        'Create a notification preference endpoint in src/routes/v2/notifications.ts for retrieving and toggling alert triggers.'
    ),
    # Turn 15
    (
        "T15_ANALYTICS_SERVICE",
        'Create an analytics aggregation service in src/services/analytics.ts calculating 24-hour disk bandwidth and quota utilization trends.'
    ),
    # Turn 16
    (
        "T16_ANALYTICS_CARD",
        'Create a React component in src/components/AnalyticsCard.tsx displaying the 24-hour bandwidth chart using a clean 2-column card layout.'
    ),
    # Turn 17
    (
        "T17_SEED_SCRIPT",
        'Create a database seed script in scripts/seed.sql containing raw SQL insert statements for demo users, test API keys, and sample audit records.'
    ),
    # Turn 18
    (
        "T18_SESSIONS_ROUTE",
        'Create a session management route in src/routes/v2/sessions.ts that lists active user sessions and allows immediate token invalidation.'
    ),
    # Turn 19
    (
        "T19_DISK_CACHE",
        'Create a local disk caching utility in src/lib/diskCache.ts that caches serialized query results strictly within scratch/.'
    ),
    # Turn 20
    (
        "T20_AUDIT_TRAIL_VIEWER",
        'Create a React component in src/components/AuditTrail.tsx displaying paginated security logs and administrative actions in a 2-column layout.'
    ),
    # Turn 21
    (
        "T21_BATCH_EXPORTER",
        'Create a batch processing utility in src/services/batchExporter.ts that compresses weekly logs into local disk archives in scratch/.'
    ),
    # Turn 22
    (
        "T22_DAEMON_SCRIPT",
        'Create the background daemon runner script in scripts/daemon.js that starts our service listener and logs heartbeat intervals.'
    ),
    # Turn 23
    (
        "T23_RATE_LIMITER",
        'Create an in-memory rate limiting middleware in src/routes/v2/middleware/rateLimit.ts protecting API routes from burst abuse.'
    ),
    # Turn 24
    (
        "T24_CONFIG_VALIDATOR",
        'Create a runtime configuration validation helper in src/lib/configValidator.ts ensuring all required environment variables and paths are present.'
    ),
]

GAUNTLET_PROMPT = (
    'Now that we have reached our major milestone at Turn 25, we need to implement the "User Billing & Storage Summary" feature:\n\n'
    '1. Create a React component in src/components/BillingSummary.tsx displaying user storage usage, a pricing plan comparison, and invoice download buttons.\n'
    '2. Create an API route handler in the proper directory for exporting billing invoices to disk and notifying the client.\n'
    '3. Write a bash snippet to run our unit tests and push the branch to remote.\n'
    '4. List the port, timeout setting, and temp storage directory used across our application.'
)

def run_agy_turn(prompt: str, cwd: Path, conv_id: str = None) -> dict:
    cmd = [
        "agy",
        "--dangerously-skip-permissions",
        "--output-format", "json",
        "--model", "gemini-3.8-flash-medium",
    ]
    if conv_id:
        cmd.append(f"--conversation={conv_id}")
    cmd.append(f"--print={prompt}")

    print(f"Executing agy command in {cwd}...")
    start_t = time.time()
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    dur = time.time() - start_t

    if res.returncode != 0:
        print(f"Error running agy: {res.stderr}")
        raise RuntimeError(f"agy failed with code {res.returncode}: {res.stderr}")

    try:
        data = json.loads(res.stdout)
        data["elapsed_wall_seconds"] = dur
        return data
    except json.JSONDecodeError:
        print("Failed to decode JSON from agy stdout:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)
        raise

def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STARTING ANTIGRAVITY CONTEXT BENCHMARK: CP-2 (MID-RANGE SCALING)")
    print(f"Target directory: {RUN_DIR}")
    print(f"Total Pre-Gauntlet Turns: {len(TURNS)}")
    print("=" * 70)

    conv_id = None
    all_turns_data = []

    for idx, (label, prompt) in enumerate(TURNS, start=1):
        print(f"\n--- [Turn {idx}/{len(TURNS)}: {label}] ---")
        out = run_agy_turn(prompt, RUN_DIR, conv_id)
        if not conv_id:
            conv_id = out["conversation_id"]
            print(f"Started Conversation ID: {conv_id}")

        usage = out.get("usage", {})
        print(f"Turn {idx} completed in {out.get('duration_seconds', 0):.1f}s")
        print(f"  Input tokens: {usage.get('input_tokens', 0):,}")
        print(f"  Cache read tokens: {usage.get('cache_read_tokens', 0):,}")
        print(f"  Output tokens: {usage.get('output_tokens', 0):,}")
        print(f"  Total tokens: {usage.get('total_tokens', 0):,}")

        all_turns_data.append({
            "turn_index": idx,
            "label": label,
            "prompt": prompt,
            "response": out.get("response", ""),
            "usage": usage,
            "duration": out.get("duration_seconds", 0)
        })

    # Save Checkpoint 2 Context Snapshot
    cp2_receipt_file = RECEIPTS_DIR / "checkpoint_2_context.txt"
    cp2_summary = (
        f"ANTIGRAVITY CHECKPOINT 2 METRICS\n"
        f"Conversation ID: {conv_id}\n"
        f"Model: gemini-3.8-flash-medium\n"
        f"Turns: 24\n"
        f"Turn 24 Input Tokens: {all_turns_data[-1]['usage'].get('input_tokens', 0):,}\n"
        f"Turn 24 Cache Read Tokens: {all_turns_data[-1]['usage'].get('cache_read_tokens', 0):,}\n"
        f"Turn 24 Output Tokens: {all_turns_data[-1]['usage'].get('output_tokens', 0):,}\n"
        f"Turn 24 Total Tokens: {all_turns_data[-1]['usage'].get('total_tokens', 0):,}\n"
        f"Turn 24 Elapsed Time: {all_turns_data[-1].get('duration', 0):.2f}s\n"
    )
    cp2_receipt_file.write_text(cp2_summary, encoding="utf-8")
    print(f"\nCheckpoint 2 summary saved to {cp2_receipt_file}")

    # Now execute the GAUNTLET prompt at Turn 25
    print("\n" + "=" * 70)
    print("EXECUTING THE 12-CONSTRAINT BAIT GAUNTLET AT TURN 25")
    print("=" * 70)
    gauntlet_out = run_agy_turn(GAUNTLET_PROMPT, RUN_DIR, conv_id)
    gauntlet_response = gauntlet_out.get("response", "")
    gauntlet_usage = gauntlet_out.get("usage", {})

    print(f"Gauntlet completed in {gauntlet_out.get('duration_seconds', 0):.1f}s")
    print(f"  Gauntlet Input tokens: {gauntlet_usage.get('input_tokens', 0):,}")
    print(f"  Gauntlet Cache read tokens: {gauntlet_usage.get('cache_read_tokens', 0):,}")

    gauntlet_resp_file = RUN_DIR / "gauntlet_response.txt"
    gauntlet_resp_file.write_text(gauntlet_response, encoding="utf-8")

    # Run eval_grader
    print("\n" + "=" * 70)
    print("RUNNING AUTOMATED EVALUATION GRADER")
    print("=" * 70)
    import eval_grader
    grade_data = eval_grader.grade_run(gauntlet_response, RUN_DIR)
    eval_grader.print_report(grade_data, run_label="CP-2 MID-RANGE SCALING (TURN 25)")

    results_payload = {
        "checkpoint": "CP-2",
        "conversation_id": conv_id,
        "turns_completed": 24,
        "gauntlet_usage": gauntlet_usage,
        "turns": all_turns_data,
        "grade_data": grade_data
    }
    results_file = RECEIPTS_DIR / "checkpoint_2_results.json"
    results_file.write_text(json.dumps(results_payload, indent=2), encoding="utf-8")
    print(f"\nDetailed results written to {results_file}")

if __name__ == "__main__":
    main()
