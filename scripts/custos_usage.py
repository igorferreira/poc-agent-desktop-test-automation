"""Aggregate token usage from the Claude Code session transcript and its subagents.

Usage: python3 -I scripts/custos_usage.py <session.jsonl> <subagents_dir> <out.json>
Dedupes assistant entries by (message.id, requestId): one API response can span several lines.
"""
import json
import pathlib
import sys
from collections import defaultdict

FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cw5m", "cw1h", "requests")


def scan(path):
    per_model = defaultdict(lambda: dict.fromkeys(FIELDS, 0))
    seen = set()
    first = last = None
    for line in pathlib.Path(path).open():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") != "assistant":
            continue
        m = d.get("message") or {}
        u = m.get("usage")
        model = m.get("model")
        if not u or not model or model == "<synthetic>":
            continue
        key = (m.get("id"), d.get("requestId"))
        if key in seen:
            continue
        seen.add(key)
        ts = d.get("timestamp")
        first = first or ts
        last = ts or last
        r = per_model[model]
        r["input_tokens"] += u.get("input_tokens") or 0
        r["output_tokens"] += u.get("output_tokens") or 0
        r["cache_read_input_tokens"] += u.get("cache_read_input_tokens") or 0
        cc = u.get("cache_creation") or {}
        w5, w1 = cc.get("ephemeral_5m_input_tokens"), cc.get("ephemeral_1h_input_tokens")
        if w5 is None and w1 is None:  # no breakdown: count all as 5m
            w5 = u.get("cache_creation_input_tokens") or 0
        r["cw5m"] += w5 or 0
        r["cw1h"] += w1 or 0
        r["requests"] += 1
    return dict(per_model), first, last


def main():
    session, subdir, out = sys.argv[1:4]
    result = {"main": {}, "subagents": []}
    result["main"]["models"], result["main"]["first"], result["main"]["last"] = scan(session)
    for f in sorted(pathlib.Path(subdir).glob("agent-*.jsonl")):
        meta_path = f.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        models, first, last = scan(f)
        result["subagents"].append({
            "id": f.stem.removeprefix("agent-"),
            "meta": {k: meta.get(k) for k in ("description", "agentType", "subagent_type", "name") if k in meta},
            "models": models, "first": first, "last": last,
        })
    pathlib.Path(out).write_text(json.dumps(result, indent=1))
    print(f"main models: {list(result['main']['models'])}; subagents: {len(result['subagents'])}")
    print("meta keys sample:", json.loads(next(pathlib.Path(subdir).glob('*.meta.json')).read_text()).keys())


if __name__ == "__main__":
    main()
