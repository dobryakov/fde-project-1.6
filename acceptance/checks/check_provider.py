"""Model provider constraints: default claude_cli, haiku/sonnet, no new providers or
committed keys wired as default. Covers AC-3."""
import re

from _util import ROOT, agent_sources, bad, ok, read


def run(root=ROOT):
    res = []
    llm = read("agent", "llm.py")
    if not llm:
        res.append(bad("AC-3", "agent/llm.py missing"))
        return res

    probs = []
    m = re.search(r'PROVIDER\s*=\s*os\.environ\.get\(\s*["\']LLM_PROVIDER["\']\s*,\s*["\']([a-z_]+)["\']', llm)
    if not m:
        probs.append("could not find PROVIDER default")
    elif m.group(1) != "claude_cli":
        probs.append(f"default provider is '{m.group(1)}', expected claude_cli")

    # Default model must resolve to haiku or sonnet (empty default is fine: llm.py maps "" -> haiku)
    low = llm.lower()
    if "haiku" not in low and "sonnet" not in low:
        probs.append("no haiku/sonnet model reference in llm.py")

    # No brand-new provider branch beyond the shipped set, and no hard-wired key as default.
    allowed = {"claude_cli", "anthropic", "openai", "mock"}
    found = set(re.findall(r'PROVIDER\s*==\s*["\']([a-z_]+)["\']', llm))
    extra = found - allowed
    if extra:
        probs.append(f"unexpected provider branch(es): {sorted(extra)}")

    # Scan whole agent for a hard-coded API key literal used as default.
    for fp in agent_sources():
        with open(fp, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        if re.search(r'sk-ant-[A-Za-z0-9]', txt) or re.search(r'sk-[A-Za-z0-9]{20}', txt):
            probs.append(f"hard-coded API key literal in {fp}")

    if probs:
        res.append(bad("AC-3", "; ".join(probs)))
    else:
        res.append(ok("AC-3", "default provider claude_cli, haiku/sonnet, no new providers or hard-coded keys"))
    return res
