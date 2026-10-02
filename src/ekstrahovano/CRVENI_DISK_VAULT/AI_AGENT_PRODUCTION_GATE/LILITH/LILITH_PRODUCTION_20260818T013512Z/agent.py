#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.parse
import urllib.request

AGENT="LILITH"
AGENT_ID="LILITH_MAC_AI_AGENT_888"
ROLE="SIGNAL_RESEARCH"

MODEL="llama3.1:latest"
ENDPOINT="http://127.0.0.1:11434"
API_URL="http://127.0.0.1:11434/api/generate"

REQUIRED_TOKEN="APPROVE_LILITH_LOCAL_DRY_RUN"
OUTPUT_STATUS="LOCAL_DRY_RUN_ONLY"

ALLOWED_CATEGORIES={
    "important",
    "normal",
    "noise",
    "review_required",
}

def fail(message, code=2):
    result={
        "agent":AGENT,
        "agent_id":AGENT_ID,
        "role":ROLE,
        "model":MODEL,
        "status":"FAIL_CLOSED",
        "error":message,
    }
    sys.stdout.write(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    raise SystemExit(code)

def validate_endpoint():
    parsed=urllib.parse.urlparse(ENDPOINT)

    if parsed.scheme != "http":
        fail("FAIL_CLOSED_EXTERNAL_NETWORK_DENIED")

    if parsed.hostname not in {
        "127.0.0.1",
        "localhost",
    }:
        fail("FAIL_CLOSED_EXTERNAL_NETWORK_DENIED")

    if parsed.port != 11434:
        fail("FAIL_CLOSED_EXTERNAL_NETWORK_DENIED")

def read_input():
    raw=sys.stdin.read()

    if not raw:
        fail("INPUT_REQUIRED")

    try:
        payload=json.loads(raw)
    except Exception:
        fail("INPUT_INVALID_JSON")

    if not isinstance(payload,dict):
        fail("INPUT_OBJECT_REQUIRED")

    if set(payload.keys()) != {"content"}:
        fail("INPUT_BOUNDARY_VIOLATION")

    content=payload.get("content")

    if not isinstance(content,str):
        fail("CONTENT_STRING_REQUIRED")

    if len(content) < 1:
        fail("CONTENT_EMPTY")

    if len(content) > 50000:
        fail("CONTENT_TOO_LARGE")

    return content

def build_prompt(content):
    return (
        "PROTOCOL=888\n"
        "ROLE=SIGNAL_RESEARCH\n"
        "You are LILITH operating only on explicitly approved local text.\n"
        "Extract useful signals ONLY from the supplied text.\n"
        "Do not use external facts or outside context.\n"
        "Do not perform or recommend external actions.\n"
        "Do not sign, send, publish, delete, move, rename, overwrite, "
        "promote, activate, or execute anything.\n"
        "Return STRICT JSON only with this exact shape:\n"
        '{"signals":[{"label":"...",'
        '"category":"important|normal|noise|review_required",'
        '"evidence":"...",'
        '"confidence":0.0}]}\n'
        "Confidence must be between 0 and 1.\n"
        "Evidence must be grounded in the supplied input.\n"
        "Maximum 50 signals.\n\n"
        "APPROVED_LOCAL_INPUT_BEGIN\n"
        + content +
        "\nAPPROVED_LOCAL_INPUT_END"
    )

def call_local_model(prompt):
    validate_endpoint()

    body=json.dumps(
        {
            "model":MODEL,
            "prompt":prompt,
            "stream":False,
            "format":"json",
        }
    ).encode("utf-8")

    req=urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type":"application/json"
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=120
        ) as response:
            raw=response.read().decode("utf-8")
    except Exception as exc:
        fail(
            "LOCAL_MODEL_REQUEST_FAILED:"
            + type(exc).__name__
        )

    try:
        outer=json.loads(raw)
    except Exception:
        fail("LOCAL_MODEL_RESPONSE_INVALID_JSON")

    model_text=outer.get("response")

    if not isinstance(model_text,str):
        fail("LOCAL_MODEL_RESPONSE_MISSING")

    try:
        inner=json.loads(model_text)
    except Exception:
        fail("SIGNAL_OUTPUT_INVALID_JSON")

    return inner

def validate_signals(result):
    if not isinstance(result,dict):
        fail("SIGNAL_OUTPUT_OBJECT_REQUIRED")

    if set(result.keys()) != {"signals"}:
        fail("SIGNAL_OUTPUT_BOUNDARY_VIOLATION")

    signals=result.get("signals")

    if not isinstance(signals,list):
        fail("SIGNALS_ARRAY_REQUIRED")

    if len(signals) > 50:
        fail("SIGNAL_COUNT_LIMIT_EXCEEDED")

    clean=[]

    for item in signals:
        if not isinstance(item,dict):
            fail("SIGNAL_ITEM_OBJECT_REQUIRED")

        if set(item.keys()) != {
            "label",
            "category",
            "evidence",
            "confidence",
        }:
            fail("SIGNAL_ITEM_BOUNDARY_VIOLATION")

        label=item.get("label")
        category=item.get("category")
        evidence=item.get("evidence")
        confidence=item.get("confidence")

        if (
            not isinstance(label,str)
            or not label.strip()
            or len(label) > 200
        ):
            fail("SIGNAL_LABEL_INVALID")

        if category not in ALLOWED_CATEGORIES:
            fail("SIGNAL_CATEGORY_INVALID")

        if (
            not isinstance(evidence,str)
            or not evidence.strip()
            or len(evidence) > 1000
        ):
            fail("SIGNAL_EVIDENCE_INVALID")

        if (
            isinstance(confidence,bool)
            or not isinstance(confidence,(int,float))
            or confidence < 0
            or confidence > 1
        ):
            fail("SIGNAL_CONFIDENCE_INVALID")

        clean.append(
            {
                "label":label.strip(),
                "category":category,
                "evidence":evidence.strip(),
                "confidence":float(confidence),
            }
        )

    return clean

def main():
    parser=argparse.ArgumentParser()

    parser.add_argument(
        "--human-gate-token",
        required=True,
    )

    args=parser.parse_args()

    if args.human_gate_token != REQUIRED_TOKEN:
        fail("HUMAN_GATE_TOKEN_REQUIRED")

    content=read_input()
    prompt=build_prompt(content)
    model_result=call_local_model(prompt)
    signals=validate_signals(model_result)

    result={
        "agent":AGENT,
        "agent_id":AGENT_ID,
        "role":ROLE,
        "model":MODEL,
        "status":OUTPUT_STATUS,
        "signals":signals,
    }

    sys.stdout.write(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

if __name__ == "__main__":
    main()
