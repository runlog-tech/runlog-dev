#!/usr/bin/env python3
"""
Antigravity PreToolUse Hook
Invoked by Antigravity engine before executing tool calls.
Contract:
- Reads protojson from stdin: {"toolCall": {"name": "run_command", "args": {"CommandLine": "..."}}, ...}
- If ALLOW: outputs {"decision": "allow"}
- If REWRITE/SANITIZE: outputs {"decision": "allow", "overwrite": {"CommandLine": "..."}} (In-memory argument rewrite)
- If DENY: outputs {"decision": "deny", "reason": "..."}
"""
import sys
import json
import os
from pathlib import Path

# Add harness dir to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kev_decision_engine import evaluate_command

LOG_PATH = Path(__file__).parent.parent / "benchmark_data" / "antigravity_hook_log.jsonl"

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return
            
        data = json.loads(raw_input)
        tool_call = data.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        command = args.get("CommandLine", "")
        
        # Only inspect run_command
        if tool_name != "run_command" or not command:
            print(json.dumps({"decision": "allow"}))
            return
            
        eval_result = evaluate_command(command)
        
        # Log to benchmark receipts
        log_entry = {
            "harness": "Antigravity",
            "tool_name": tool_name,
            "command": command,
            "verdict": eval_result["verdict"],
            "reason": eval_result["reason"],
            "overwrite_command": eval_result["overwrite_command"],
            "latency_ms": eval_result["latency_ms"],
            "prompt_ms": eval_result["prompt_ms"],
            "gen_ms": eval_result["gen_ms"],
            "hardware": eval_result["hardware"],
            "egress_bytes": 0
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        if eval_result["verdict"] == "DENY":
            # Antigravity Superpower: In-memory argument rewrite without LLM apology loop
            response = {
                "decision": "allow",
                "reason": f"Kev System 1: In-memory rewrite applied ({eval_result['reason']})",
                "overwrite": {
                    "CommandLine": eval_result["overwrite_command"]
                }
            }
        else:
            response = {
                "decision": "allow"
            }
            
        print(json.dumps(response))
        
    except Exception as e:
        # Fallback allow to avoid breaking session if hook crashes
        print(json.dumps({"decision": "allow", "reason": f"Hook exception fallback: {e}"}))

if __name__ == "__main__":
    main()
