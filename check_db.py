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
    print(f"$ {c}")
    s, o, e = ssh.exec_command(c, timeout=t)
    out = o.read().decode().strip()
    if out: print(out[:1500])
    if e.read().decode().strip(): print("(stderr has output)")

r("docker exec wzrysjglz find /app -name '*.db' -type f 2>/dev/null")
r("docker exec wzrysjglz ls -la /app/data/")
r("docker exec wzrysjglz ls -la /app/*.db 2>/dev/null")
r("docker exec wzrysjglz ls /app/seed.py 2>/dev/null")
r("docker exec wzrysjglz find /app -name 'seed.py' 2>/dev/null")
ssh.close()
