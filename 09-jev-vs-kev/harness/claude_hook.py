#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook
Invoked by Claude Code CLI before executing Bash commands.
Contract:
- Reads JSON from stdin: {"tool_name": "...", "tool_input": {"command": "..."}}
- If ALLOW: exits with code 0
- If DENY: writes reason to stderr and exits with code 2 (blocking tool execution)
"""
import sys
import json
import os
from pathlib import Path

# Add harness dir to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kev_decision_engine import evaluate_command

LOG_PATH = Path(__file__).parent.parent / "benchmark_data" / "claude_hook_log.jsonl"

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
            
        data = json.loads(raw_input)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")
        
        if tool_name != "Bash" or not command:
            sys.exit(0)
            
        eval_result = evaluate_command(command)
        
        # Log to file
        log_entry = {
            "harness": "Claude Code",
            "tool_name": tool_name,
            "command": command,
            "verdict": eval_result["verdict"],
            "reason": eval_result["reason"],
            "latency_ms": eval_result["latency_ms"],
            "prompt_ms": eval_result["prompt_ms"],
            "gen_ms": eval_result["gen_ms"],
            "hardware": eval_result["hardware"],
            "egress_bytes": 0
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        if eval_result["verdict"] == "DENY":
            sys.stderr.write(f"\n[Kev System 1 Guard]: Execution BLOCKED on RX 7900 XTX.\nCommand: {command}\nReason: {eval_result['reason']}\nLatency: {eval_result['latency_ms']:.1f}ms (Zero Egress)\n")
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        sys.stderr.write(f"[Kev Hook Error]: {e}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
