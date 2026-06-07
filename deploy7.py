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

def r(c, t=15):
    s, o, e = ssh.exec_command(c, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    print(out[:2000])
    if err:
        print(f"ERR: {err[:200]}")

r('curl -s -o /dev/null -w "STATUS: %{http_code}, SIZE: %{size_download} bytes" http://localhost:8000/')
r('curl -s -o /dev/null -w "STATUS: %{http_code}" http://localhost:8000/admin')
r('curl -s -o /dev/null -w "STATUS: %{http_code}" http://localhost:8000/pvp')
r('curl -s -o /dev/null -w "STATUS: %{http_code}" http://localhost:8000/pve')
r('curl -s http://localhost:8000/api/v1/posts/pvp | head -c 300')
ssh.close()
