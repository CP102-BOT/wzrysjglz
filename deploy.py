import paramiko, time, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore

HOST = os.environ.get("VPS_HOST")
PORT = int(os.environ.get("VPS_PORT", "22"))
USER = os.environ.get("VPS_USER", "root")
PASS = os.environ.get("VPS_PASS")
REPO = "https://github.com/CP102-BOT/wzrysjglz.git"
APP_DIR = "/root/wzrysjglz"


def bail(msg):
    print(f"\n❌ {msg}")
    print("Usage: $env:VPS_HOST='ip'; $env:VPS_PORT='port'; $env:VPS_PASS='pass'; py deploy.py")
    sys.exit(1)


def run(ssh, cmd, timeout=30):
    print(f"  $ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    for line in out.split("\n"):
        if line.strip():
            print(f"    {line}")
    if exit_code != 0:
        err = stderr.read().decode().strip()
        for line in err.split("\n"):
            if line.strip():
                print(f"    ! {line}")
    return exit_code, out


def main():
    if not HOST or not PASS:
        bail("Missing VPS_HOST, VPS_PORT, or VPS_PASS env vars")

    print(f"Connecting to {USER}@{HOST}:{PORT} ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS,
                look_for_keys=False, allow_agent=False, timeout=15)
    print("Connected.\n")

    run(ssh, "uname -a")

    ec, _ = run(ssh, "docker --version 2>/dev/null || true", timeout=5)
    if ec == 0 and _:
        print(f"  [OK] Docker: {_}")
    else:
        print("  → Installing Docker ...")
        run(ssh, "apt-get update -qq && apt-get install -y -qq docker.io docker-compose-v2", timeout=120)
        run(ssh, "systemctl enable --now docker")

    run(ssh, "docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || true", timeout=5)

    print(f"\nSyncing repo ...")
    ec, _ = run(ssh, f"test -d {APP_DIR} && echo 1 || echo 0", timeout=5)
    if "1" in _:
        run(ssh, f"cd {APP_DIR} && git pull --ff-only", timeout=30)
    else:
        run(ssh, f"cd /root && git clone {REPO}", timeout=60)

    print("\nBuilding & starting ...")
    run(ssh, f"cd {APP_DIR} && docker compose up -d --build", timeout=180)

    print("\nHealth check ...")
    time.sleep(6)
    ec, out = run(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/ 2>/dev/null || echo 'no_curl'", timeout=10)
    if "200" in out:
        print(f"\n[OK] Deployed! http://{HOST}:8000/  |  /admin")
    elif out == "no_curl":
        run(ssh, "apt-get install -y -qq curl", timeout=30)
        time.sleep(3)
        _, out2 = run(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/", timeout=10)
        print(f"\n{'[OK]' if out2=='200' else '[!!]'} Status: {out2}")
    else:
        print(f"\n[!!] Status: {out}")
        run(ssh, f"cd {APP_DIR} && docker compose logs --tail=20", timeout=10)

    ssh.close()


if __name__ == "__main__":
    main()
