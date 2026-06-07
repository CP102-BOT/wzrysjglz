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
    ec = s.channel.recv_exit_status()
    out = o.read().decode().strip()
    if out:
        print(out)
    if ec != 0:
        err = e.read().decode().strip()
        if err:
            print(f"ERR: {err[:500]}")
    return ec, out

r("cd /root/wzrysjglz && docker compose logs --tail=50", 15)
r("cd /root/wzrysjglz && docker compose ps", 10)
ssh.close()
