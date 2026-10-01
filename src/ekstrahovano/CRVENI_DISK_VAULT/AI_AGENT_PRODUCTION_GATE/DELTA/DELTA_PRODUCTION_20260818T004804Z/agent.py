#!/usr/bin/env python3
"""
DELTA — FREYA Protocol 888
STAGING ONLY. No production authority.
Local Ollama loopback inference only.
"""

import argparse
import json
import urllib.request
import urllib.parse

AGENT_ID = "DELTA_MAC_AI_AGENT_888"
AGENT_NAME = "DELTA"
ROLE = "ANALYST_VALIDATOR"
MODEL = "llama3.1:latest"
OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/generate"

SYSTEM_PROMPT = """
You are DELTA, a local analysis and validation component.
Analyze only the supplied local test content.
Do not claim authority to sign, send, approve, publish, delete,
move, rename, overwrite, or promote anything.
Return concise validation findings for Human Gate review.
""".strip()

def validate_endpoint(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http":
        raise RuntimeError("FAIL_CLOSED_NON_HTTP_LOOPBACK_ENDPOINT")
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("FAIL_CLOSED_EXTERNAL_NETWORK_DENIED")
    if parsed.port != 11434:
        raise RuntimeError("FAIL_CLOSED_UNAPPROVED_PORT")

def local_inference(content: str, goal: str) -> str:
    validate_endpoint(OLLAMA_ENDPOINT)

    prompt = (
        SYSTEM_PROMPT
        + "\n\nVALIDATION_GOAL:\n"
        + goal
        + "\n\nCONTENT:\n"
        + content
    )

    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_ENDPOINT,
        data=payload,
        headers={"Content-Type":"application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        data=json.loads(response.read().decode("utf-8"))

    return str(data.get("response","")).strip()

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to explicit local test JSON")
    parser.add_argument(
        "--human-gate-token",
        choices=["APPROVE_LOCAL_DRY_RUN"]
    )
    args=parser.parse_args()

    if not args.input:
        print("STATUS=STAGING_NOT_EXECUTED")
        print("HUMAN_GATE_REQUIRED=YES")
        return 0

    if args.human_gate_token != "APPROVE_LOCAL_DRY_RUN":
        raise SystemExit("HOLD=HUMAN_GATE_TOKEN_REQUIRED")

    with open(args.input,"r",encoding="utf-8") as f:
        obj=json.load(f)

    content=obj.get("content")
    goal=obj.get("validation_goal","Validate the supplied content.")

    if not isinstance(content,str) or not content.strip():
        raise SystemExit("HOLD=INVALID_INPUT_CONTENT")

    result=local_inference(content,goal)

    output={
        "agent":AGENT_NAME,
        "role":ROLE,
        "model":MODEL,
        "status":"LOCAL_DRY_RUN_ONLY",
        "analysis":result
    }

    print(json.dumps(output,indent=2,ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
