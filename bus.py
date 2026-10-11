#!/usr/bin/env python3
"""local-model-cli-bus — a minimal launch-bus spec + reference adapters.

Lets coding agents start and switch local inference engines through ONE
command interface, instead of memorizing each engine's private flags.
Ships an adapter contract and two reference stubs (echo, openai-compat).
Binds to no vendor's private API: engines are described by a registry file.
Pure standard library. No network. No secrets. Data currency: 2026-10-11.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

AS_OF = "2026-10-11"

DEFAULT_REGISTRY = {
    "version": "0.1",
    "engines": {
        "stub-echo": {
            "adapter": "echo",
            "description": "dry-run stub used by self tests; prints the plan",
        },
        "stub-local-openai": {
            "adapter": "openai-compat",
            "command": ["local-engine", "serve"],
            "base_url": "http://127.0.0.1:11434/v1",
            "description": "any OpenAI-compatible local server (generic flags only)",
        },
    },
}


class InputError(ValueError):
    """Invalid user input or registry; CLI maps this to exit code 2."""


# --------------------------- adapter contract -------------------------------
# Every adapter implements exactly two methods (this is the bus spec, v0.1):
#   build_launch_command(spec, model, opts) -> list[str]   # argv to execute
#   healthcheck_fields(spec) -> list[str]                  # fields to probe
# `spec` is the engine's registry entry; `opts` is user-supplied kwargs.
# ----------------------------------------------------------------------------

ADAPTERS = {}


def register(name):
    def deco(cls):
        ADAPTERS[name] = cls()
        return cls
    return deco


class Adapter:
    name = "base"

    def build_launch_command(self, spec, model, opts):
        raise NotImplementedError

    def healthcheck_fields(self, spec):
        return ["pid", "ready"]


@register("echo")
class EchoAdapter(Adapter):
    """Test/dry-run stub: emits a plan instead of touching any process."""

    name = "echo"

    def build_launch_command(self, spec, model, opts):
        return ["echo", "bus:engine=%s model=%s opts=%s"
                % (spec.get("name", "?"), model, json.dumps(opts, sort_keys=True))]

    def healthcheck_fields(self, spec):
        return ["argv_preview"]


@register("openai-compat")
class OpenAICompatAdapter(Adapter):
    """Generic adapter for any OpenAI-compatible local HTTP server.

    Uses only generic flags (--model, --base-url); never a vendor's
    private API surface. Engines map their own specifics in the registry.
    """

    name = "openai-compat"

    def build_launch_command(self, spec, model, opts):
        command = spec.get("command")
        if not command or not isinstance(command, list):
            raise InputError("engine spec missing 'command' list (adapter=openai-compat)")
        argv = [str(c) for c in command]
        argv += ["--model", model]
        base = spec.get("base_url")
        if base:
            argv += ["--base-url", str(base)]
        if opts.get("context"):
            argv += ["--context", str(opts["context"])]
        return argv

    def healthcheck_fields(self, spec):
        return ["pid", "http_ready", "model_loaded"]


def load_registry(path):
    if path is None:
        return json.loads(json.dumps(DEFAULT_REGISTRY))
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise InputError("registry file is not valid JSON: %s" % exc)
    except OSError as exc:
        raise InputError("cannot read registry file: %s" % exc)
    if not isinstance(data, dict) or not isinstance(data.get("engines"), dict):
        raise InputError("registry must be a JSON object with an 'engines' object")
    return data


def launch_plan(registry, engine, model, opts):
    engines = registry["engines"]
    if engine not in engines:
        raise InputError("unknown engine: %r (available: %s)"
                         % (engine, ", ".join(sorted(engines)) or "none"))
    spec = dict(engines[engine])
    spec["name"] = engine
    adapter_name = spec.get("adapter")
    adapter = ADAPTERS.get(adapter_name)
    if adapter is None:
        raise InputError("engine %r references unknown adapter %r (installed: %s)"
                         % (engine, adapter_name, ", ".join(sorted(ADAPTERS))))
    if not model:
        raise InputError("--model is required for launch")
    argv = adapter.build_launch_command(spec, model, opts)
    return {
        "as_of": AS_OF,
        "engine": engine,
        "adapter": adapter.name,
        "model": model,
        "argv": argv,
        "healthcheck_fields": adapter.healthcheck_fields(spec),
        "bus_spec_version": registry.get("version", "unknown"),
    }


def cmd_engines(ns):
    registry = load_registry(ns.registry)
    for name in sorted(registry["engines"]):
        spec = registry["engines"][name]
        print("%-22s adapter=%-14s %s" % (name, spec.get("adapter", "?"),
                                          spec.get("description", "")))
    return 0


def cmd_launch(ns):
    registry = load_registry(ns.registry)
    opts = {}
    if ns.context:
        opts["context"] = ns.context
    plan = launch_plan(registry, ns.engine, ns.model, opts)
    if ns.json:
        print(json.dumps(plan, indent=2))
    else:
        print("launch plan (bus spec %s, as of %s)" % (plan["bus_spec_version"], AS_OF))
        print("  engine : %s" % plan["engine"])
        print("  adapter: %s" % plan["adapter"])
        print("  model  : %s" % plan["model"])
        print("  argv   : %s" % " ".join(plan["argv"]))
        print("  health : %s" % ", ".join(plan["healthcheck_fields"]))
    if ns.exec:
        try:
            proc = subprocess.run(plan["argv"])
        except FileNotFoundError:
            print("error: executable not found: %s" % plan["argv"][0], file=sys.stderr)
            return 3
        except OSError as exc:
            print("error: launch failed: %s" % exc, file=sys.stderr)
            return 3
        return proc.returncode
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="bus", description=__doc__)
    p.add_argument("--registry", default=None,
                   help="engine registry JSON (defaults to built-in stub registry)")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("engines", help="list engines in the registry")
    e.set_defaults(func=cmd_engines)

    l = sub.add_parser("launch", help="build (and optionally run) a launch plan")
    l.add_argument("engine")
    l.add_argument("--model", required=True)
    l.add_argument("--context", type=int, default=None)
    l.add_argument("--json", action="store_true")
    l.add_argument("--exec", action="store_true",
                   help="execute the plan (default: dry-run, print only)")
    l.set_defaults(func=cmd_launch)
    return p


def main(argv=None):
    ns = build_parser().parse_args(argv)
    try:
        return ns.func(ns)
    except InputError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
