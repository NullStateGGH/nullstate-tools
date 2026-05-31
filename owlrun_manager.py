import os, json, requests, subprocess, time

OWLRUN_DIR = os.path.expanduser("~/.owlrun")
OWLRUN_CONF = os.path.join(OWLRUN_DIR, "owlrun.conf")
DASHBOARD_URL = "http://localhost:19131"


def get_status():
    try:
        r = requests.get(f"{DASHBOARD_URL}/api/node", timeout=5)
        return r.json() if r.status_code == 200 else r.text[:500]
    except:
        return None


def get_earnings():
    try:
        r = requests.get(f"{DASHBOARD_URL}/api/earnings", timeout=5)
        return r.json() if r.status_code == 200 else {"raw": r.text[:500]}
    except:
        return {"error": "dashboard not reachable"}


def set_lightning_address(address, method="api"):
    if method == "api":
        try:
            r = requests.post(
                f"{DASHBOARD_URL}/api/settings",
                json={"lightning_address": address},
                timeout=5
            )
            return f"API: HTTP {r.status_code}"
        except Exception as e:
            return f"API error: {e}"
    elif method == "config":
        if os.path.exists(OWLRUN_CONF):
            with open(OWLRUN_CONF) as f:
                config = f.read()
            if "lightning_address" in config:
                config = config.replace(
                    f'lightning_address = "{get_current_address()}"' 
                    if get_current_address() else "lightning_address =",
                    f'lightning_address = "{address}"'
                )
            else:
                config += f'\nlightning_address = "{address}"\n'
            with open(OWLRUN_CONF, "w") as f:
                f.write(config)
            restart_owlrun()
            return f"Config updated, owlrun restarted"
    return "Unknown method"


def get_current_address():
    try:
        status = get_status()
        if status and isinstance(status, dict):
            return status.get("lightning_address", "")
    except:
        pass
    return ""


def restart_owlrun():
    subprocess.run("pkill owlrun 2>/dev/null; sleep 1", shell=True)
    subprocess.run(
        "nohup owlrun > /tmp/owlrun.log 2>&1 &",
        shell=True, executable="/bin/bash"
    )
    return "Owlrun restarted"


def check_jobs():
    try:
        r = requests.get(f"{DASHBOARD_URL}/api/jobs", timeout=5)
        jobs = r.json() if r.status_code == 200 else []
        return jobs[:10]
    except:
        return []


def monitor(interval=60):
    print("[owlrun_manager] Starting monitor...")
    while True:
        status = get_status()
        earnings = get_earnings()
        jobs = check_jobs()
        print(f"Status: {json.dumps(status, indent=2)[:200] if status else 'offline'}")
        print(f"Earnings: {json.dumps(earnings, indent=2)[:200] if earnings else 'none'}")
        print(f"Active jobs: {len(jobs)}")
        print(f"--- {time.strftime('%H:%M:%S')} ---")
        time.sleep(interval)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            s = get_status()
            print(json.dumps(s, indent=2) if s else "offline")
        elif cmd == "earnings":
            e = get_earnings()
            print(json.dumps(e, indent=2) if e else "no data")
        elif cmd == "set-ln":
            addr = sys.argv[2] if len(sys.argv) > 2 else input("Lightning address: ")
            print(set_lightning_address(addr))
        elif cmd == "restart":
            print(restart_owlrun())
        elif cmd == "monitor":
            monitor()
        elif cmd == "jobs":
            jobs = check_jobs()
            print(json.dumps(jobs, indent=2))
        else:
            print("Commands: status, earnings, set-ln <addr>, restart, monitor, jobs")
    else:
        s = get_status()
        e = get_earnings()
        print("=== Owlrun Status ===")
        print(json.dumps(s, indent=2)[:300] if s else "OFFLINE")
        print("\n=== Earnings ===")
        print(json.dumps(e, indent=2)[:300] if e else "No data")
