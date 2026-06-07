import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(
    os.environ["VPS_HOST"],
    port=int(os.environ.get("VPS_PORT", "22")),
    username=os.environ["VPS_USER"],
    password=os.environ["VPS_PASS"],
    look_for_keys=False, allow_agent=False, timeout=15
)

def r(c, t=30):
    s, o, e = ssh.exec_command(c, timeout=t)
    ec = s.channel.recv_exit_status()
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    print(f"--- {c} ---")
    if out: print(out[:2000])
    if err: print(f"ERR: {err[:500]}")
    print()

r("docker ps -a --filter name=wzrysjglz")
r("docker compose -f /root/wzrysjglz/docker-compose.yml ps")
r("ls -la /root/wzrysjglz/docker-compose.yml")
r("cat /root/wzrysjglz/docker-compose.yml")
ssh.close()
