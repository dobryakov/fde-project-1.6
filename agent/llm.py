"""One place for every model call the agent makes. Swap providers here.

Providers (set LLM_PROVIDER):
  claude_cli  default. Runs the local `claude -p` CLI, so it uses your Claude Code login and
              needs no API key. Model from LLM_MODEL (default: haiku). CLAUDE_BIN overrides the
              command (default: claude). LLM_CLEAN_CONFIG=<empty dir> keeps your own CLAUDE.md out.
  anthropic   Anthropic API. Needs ANTHROPIC_API_KEY and `pip install anthropic`.
  openai      OpenAI API. Needs OPENAI_API_KEY and `pip install openai`.
  mock        No model. Returns "" so the agent falls back to its templates. Fast, free, for tests.

Every call is logged to <run_dir>/llm_calls.jsonl (the dashboard reads it for cost).
LLM_MAX_CALLS caps calls per run (default 80). Past the cap, complete() returns "".
"""
import json
import os
import subprocess
import time

PROVIDER = os.environ.get("LLM_PROVIDER", "claude_cli")
MODEL = os.environ.get("LLM_MODEL", "")
MAX_CALLS = int(os.environ.get("LLM_MAX_CALLS", "80"))
_state = {"calls": 0, "log": None}


def set_log(run_dir):
    _state["log"] = os.path.join(run_dir, "llm_calls.jsonl")


def _log(rec):
    if _state["log"]:
        with open(_state["log"], "a") as f:
            f.write(json.dumps(rec) + "\n")


def complete(prompt, system="", max_tokens=600, tag=""):
    if PROVIDER == "mock" or _state["calls"] >= MAX_CALLS:
        return ""
    _state["calls"] += 1
    t0 = time.time()
    text, err = "", None
    try:
        if PROVIDER == "claude_cli":
            cmd = [os.environ.get("CLAUDE_BIN", "claude"), "-p", "--model", MODEL or "haiku", "--tools", "", "--no-session-persistence",
                   "--output-format", "text"]
            if system:
                cmd += ["--system-prompt", system]
            env = dict(os.environ)
            if os.environ.get("LLM_CLEAN_CONFIG"):  # optional: an empty config dir keeps your own CLAUDE.md out of agent calls
                env["CLAUDE_CONFIG_DIR"] = os.environ["LLM_CLEAN_CONFIG"]
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=180, env=env)
            text = r.stdout.strip()
            if r.returncode != 0:  # e.g. not logged in or out of credit: never send the error text to a creator
                err = (r.stderr.strip() or text)[:300]
                text = ""
        elif PROVIDER == "anthropic":
            import anthropic
            msg = anthropic.Anthropic().messages.create(model=MODEL or "claude-haiku-4-5", max_tokens=max_tokens,
                                                        system=system, messages=[{"role": "user", "content": prompt}])
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        elif PROVIDER == "openai":
            from openai import OpenAI
            r = OpenAI().chat.completions.create(model=MODEL or "gpt-4o-mini", max_tokens=max_tokens,
                                                 messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}])
            text = (r.choices[0].message.content or "").strip()
        else:
            err = f"unknown provider {PROVIDER}"
    except Exception as e:  # a failed call must never crash the run
        err = str(e)[:300]
    _log({"tag": tag, "provider": PROVIDER, "model": MODEL, "secs": round(time.time() - t0, 2),
          "prompt_chars": len(prompt) + len(system), "out_chars": len(text), "error": err})
    return text


def calls_made():
    return _state["calls"]
