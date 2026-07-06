#!/bin/bash
# 价格观察站 — 云服务器一键部署脚本
# 适用：Ubuntu 22.04 (Oracle Cloud Free Tier / 任意 VPS)
# 用法：
#   scp -i key.pem -r /workspace/price-monitor ubuntu@<IP>:~/
#   ssh -i key.pem ubuntu@<IP>
#   bash ~/price-monitor/scripts/deploy_server.sh
set -euo pipefail

echo "=== [1/6] 系统更新 ==="
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip git curl

echo "=== [2/7] 安装依赖 ==="
pip3 install --quiet requests 2>/dev/null || true

echo "=== [3/7] 初始化数据 ==="
cd ~/price-monitor
python3 scripts/backfill.py 365
python3 scripts/fetch.py
python3 scripts/build.py

echo "=== [4/7] 安装 Web 服务 (Flask) ==="
pip3 install --quiet flask
cat > ~/price-monitor/run_server.py << 'PYEOF'
from flask import Flask, send_from_directory, abort
import os
app = Flask(__name__)
PUBLIC = os.path.join(os.path.dirname(__file__), "public")

@app.route('/')
def index():
    return send_from_directory(PUBLIC, "index.html")

@app.route('/<path:path>')
def static_file(path):
    full = os.path.join(PUBLIC, path)
    if os.path.exists(full) and os.path.isfile(full):
        return send_from_directory(PUBLIC, path)
    # 尝试 .html 后缀
    if os.path.exists(full + ".html"):
        return send_from_directory(PUBLIC, path + ".html")
    abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
PYEOF

echo "=== [5/7] 配置定时任务 (每天 09:00 北京自动更新) ==="
# 写入 crontab：每天 UTC 01:00 = 北京 09:00
CRON_JOB="0 1 * * * cd ~/price-monitor && python3 scripts/fetch.py && python3 scripts/build.py >> /tmp/price.log 2>&1"
(crontab -l 2>/dev/null | grep -v "price-monitor" ; echo "$CRON_JOB") | crontab -

echo "=== [6/7] 启动服务 (后台常驻) ==="
nohup python3 ~/price-monitor/run_server.py > /tmp/price-server.log 2>&1 &
sleep 2

echo "=== [7/7] 验证 ==="
curl -s -o /dev/null -w "本地访问状态码: %{http_code}\n" http://localhost:8080/

echo ""
echo "✅ 部署完成！"
echo "   浏览器访问: http://<你的服务器公网IP>:8080/"
echo "   数据每天 09:00 自动更新"
echo "   查看日志: tail -f /tmp/price.log"
echo "   重启服务: pkill -f run_server.py && nohup python3 ~/price-monitor/run_server.py > /tmp/price-server.log 2>&1 &"
