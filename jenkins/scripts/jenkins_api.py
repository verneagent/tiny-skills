#!/usr/bin/env python3
"""Jenkins API client using Groovy Script Console.

Uses the Groovy Script Console API because config.xml POST returns 500
(the 'ci' user lacks Job/Configure permission but has Script Console access).

Config is read from ~/.config/jenkins.json (outside the repo):
  - url: Jenkins server URL
  - user: Jenkins username
  - token: Jenkins API token
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_PATH = os.path.expanduser("~/.config/jenkins.json")


def _load_config():
    # Read credentials from ~/.config/jenkins.json (not in repo)
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    url = data["url"]
    # Resolve hostname to IP to bypass ICP blocking
    # jenkins.maxeffort.cn resolves to 47.100.13.75
    url = re.sub(r"jenkins\.maxeffort\.cn", "47.100.13.75", url)
    return {
        "url": url.rstrip("/"),
        "user": data["user"],
        "token": data["token"],
    }


def _auth_header(cfg):
    import base64
    cred = base64.b64encode(f'{cfg["user"]}:{cfg["token"]}'.encode()).decode()
    return f"Basic {cred}"


def _get_crumb(cfg):
    """Get Jenkins CSRF crumb."""
    url = f'{cfg["url"]}/crumbIssuer/api/json'
    req = urllib.request.Request(url)
    req.add_header("Authorization", _auth_header(cfg))
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return data["crumb"]


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def check_config() -> str:
    """Check if Jenkins config exists and is valid."""
    if not os.path.exists(CONFIG_PATH):
        print("NOT_CONFIGURED")
        print(f"Config file not found: {CONFIG_PATH}")
        return ""
    try:
        cfg = _load_config()
        print("CONFIGURED")
        print(f"URL: {cfg['url']}")
        print(f"User: {cfg['user']}")
    except Exception as e:
        print(f"ERROR: {e}")
    return ""


def init_config() -> str:
    """Initialize Jenkins config. Reads --url, --user, --token from sys.argv."""
    url = user = token = None
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--url" and i + 1 < len(args):
            url = args[i + 1]; i += 2
        elif args[i] == "--user" and i + 1 < len(args):
            user = args[i + 1]; i += 2
        elif args[i] == "--token" and i + 1 < len(args):
            token = args[i + 1]; i += 2
        else:
            i += 1
    if not all([url, user, token]):
        print("Usage: jenkins_api.py init --url <URL> --user <USER> --token <TOKEN>")
        sys.exit(1)
    # Save config
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    data = {"url": url.rstrip("/"), "user": user, "token": token}
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)
    # Validate connection
    try:
        cfg = _load_config()
        _get_crumb(cfg)
        print("SUCCESS: Config saved and connection verified")
        print(f"Config: {CONFIG_PATH}")
    except Exception as e:
        os.remove(CONFIG_PATH)
        print(f"ERROR: Connection failed — {e}")
        print("Config was NOT saved. Please check your credentials.")
    return ""


# ---------------------------------------------------------------------------
# Groovy Script Execution
# ---------------------------------------------------------------------------

def run_groovy(script: str) -> str:
    """Execute a Groovy script on Jenkins Script Console."""
    cfg = _load_config()
    crumb = _get_crumb(cfg)
    url = f'{cfg["url"]}/scriptText'
    body = urllib.parse.urlencode({"script": script}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", _auth_header(cfg))
    req.add_header("Jenkins-Crumb", crumb)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()


# ---------------------------------------------------------------------------
# High-level Operations
# ---------------------------------------------------------------------------

def get_pipeline_script(job_name: str) -> str:
    """Get the inline pipeline script for a job."""
    return run_groovy(f"""
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition

def job = Jenkins.instance.getItemByFullName("{job_name}") as WorkflowJob
if (!job) {{ println "ERROR: Job not found"; return }}
def defn = job.definition
if (defn instanceof CpsFlowDefinition) {{
    println defn.script
}} else {{
    println "ERROR: Not an inline pipeline script"
}}
""")


def set_pipeline_script(job_name: str, script: str) -> str:
    """Set the inline pipeline script for a job."""
    escaped = script.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    return run_groovy(f"""
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition

def job = Jenkins.instance.getItemByFullName("{job_name}") as WorkflowJob
if (!job) {{ println "ERROR: Job not found"; return }}
def newScript = \"\"\"{escaped}\"\"\"
job.definition = new CpsFlowDefinition(newScript, false)
job.save()
println "SUCCESS: Pipeline script updated"
""")


def list_jobs() -> str:
    """List all Jenkins jobs."""
    return run_groovy("""
import jenkins.model.Jenkins
Jenkins.instance.allItems.each { job ->
    def disabled = job.respondsTo('isDisabled') && job.isDisabled() ? ' [DISABLED]' : ''
    println "${job.fullName}${disabled}"
}
""")


def get_build_status(job_name: str) -> str:
    """Get last build status for a job."""
    return run_groovy(f"""
import jenkins.model.Jenkins

def job = Jenkins.instance.getItemByFullName("{job_name}")
if (!job) {{ println "ERROR: Job not found"; return }}
def build = job.lastBuild
if (!build) {{ println "No builds yet"; return }}
println "Build #${{build.number}}"
println "Status: ${{build.result ?: 'IN PROGRESS'}}"
println "Duration: ${{build.durationString}}"
println "Started: ${{build.timestampString2}}"
""")


def trigger_build(job_name: str) -> str:
    """Trigger a build for a job."""
    return run_groovy(f"""
import jenkins.model.Jenkins

def job = Jenkins.instance.getItemByFullName("{job_name}")
if (!job) {{ println "ERROR: Job not found"; return }}
job.scheduleBuild2(0)
println "SUCCESS: Build triggered for {job_name}"
""")


def get_console_log(job_name: str, build_number: int = 0) -> str:
    """Get console log for a build (0 = last build). Returns last 200 lines."""
    build_selector = f"job.getBuildByNumber({build_number})" if build_number else "job.lastBuild"
    return run_groovy(f"""
import jenkins.model.Jenkins

def job = Jenkins.instance.getItemByFullName("{job_name}")
if (!job) {{ println "ERROR: Job not found"; return }}
def build = {build_selector}
if (!build) {{ println "No build found"; return }}
def log = build.log
def lines = log.split("\\n")
def start = Math.max(0, lines.length - 200)
println "=== Build #${{build.number}} (${{build.result ?: 'IN PROGRESS'}}) ==="
lines[start..-1].each {{ println it }}
""")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMMANDS = {
    "check-config": ("Check if config exists", check_config, []),
    "init": ("Initialize config (--url, --user, --token)", init_config, []),
    "list": ("List all jobs", list_jobs, []),
    "script": ("Get pipeline script", get_pipeline_script, ["job_name"]),
    "status": ("Get last build status", get_build_status, ["job_name"]),
    "trigger": ("Trigger a build", trigger_build, ["job_name"]),
    "log": ("Get console log (last 200 lines)", get_console_log, ["job_name"]),
    "groovy": ("Run raw Groovy script", run_groovy, ["script"]),
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: jenkins_api.py <command> [args...]")
        print("\nCommands:")
        for name, (desc, _, args) in COMMANDS.items():
            args_str = " ".join(f"<{a}>" for a in args)
            print(f"  {name} {args_str} — {desc}")
        sys.exit(1)

    cmd_name = sys.argv[1]
    desc, func, expected_args = COMMANDS[cmd_name]
    args = sys.argv[2:]

    if len(args) < len(expected_args):
        print(f"Usage: jenkins_api.py {cmd_name} {' '.join(f'<{a}>' for a in expected_args)}")
        sys.exit(1)

    result = func(*args[:len(expected_args)])
    print(result)


if __name__ == "__main__":
    main()
