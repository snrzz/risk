# 风险预警系统 - 快速部署指南

## 一、执行部署（5分钟完成）

### Linux服务器（Ubuntu/Debian/CentOS）

```bash
# 1. 下载一键部署脚本
cd /opt
sudo curl -O https://raw.githubusercontent.com/snrzz/risk/main/deploy.sh
sudo chmod +x deploy.sh

# 2. 执行部署（需要root权限）
sudo ./deploy.sh
```

### macOS本地测试

```bash
# 1. 克隆项目
git clone https://github.com/snrzz/risk.git
cd risk

# 2. 执行部署
chmod +x deploy.sh
./deploy.sh
```

---

## 二、部署后访问

| 服务 | 地址 | 说明 |
|-----|------|------|
| Web UI | http://localhost:3000 | 浏览器访问 |
| API | http://localhost:8000 | 后端API |
| API文档 | http://localhost:8000/api/docs/ | Swagger文档 |

---

## 三、登录信息

```
邮箱: admin@example.com
密码: Admin123!@#
```

---

## 四、验证部署

```bash
# 检查服务状态
curl http://localhost:8000/api/risk/dashboard/
# 预期返回JSON数据

curl http://localhost:3000
# 预期返回HTML页面
```

---

## 五、Docker部署（备选方案）

```bash
# 克隆项目
git clone https://github.com/snrzz/risk.git
cd risk

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 六、常用命令

| 操作 | 命令 |
|-----|------|
| 查看日志 | `tail -f /var/log/risk-deploy.log` |
| 重启后端 | `sudo systemctl restart risk-backend` |
| 重启前端 | `sudo systemctl restart risk-frontend` |
| 停止服务 | `sudo systemctl stop risk-backend risk-frontend` |
| 查看状态 | `systemctl status risk-backend risk-frontend` |

---

## 七、问题排查

### 端口被占用
```bash
# 查看占用端口的进程
lsof -i :8000
lsof -i :3000

# 杀掉占用进程
kill -9 <PID>
```

### 数据库迁移失败
```bash
cd /opt/risk-system
source venv/bin/activate
python manage.py migrate --run-syncdb
```

### 前端无法访问
```bash
# 检查前端进程
ps aux | grep vite

# 重启前端
cd /opt/risk-system/frontend
nohup npm run dev -- --host 0.0.0.0 > /dev/null 2>&1 &
```

### API返回500错误
```bash
# 查看Django日志
tail -f /var/log/risk/django.log
```

---

## 八、配置修改

### 修改端口

编辑 `/opt/risk-system/.env`:
```env
PORT=8080  # 改为8080
```

### 修改数据库

生产环境建议使用PostgreSQL，修改配置:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/risk_db
```

### 配置Redis缓存

```env
REDIS_URL=redis://localhost:6379/0
```

---

## 九、开启HTTPS（生产环境）

```bash
# 1. 安装certbot
sudo apt install certbot python3-certbot-nginx

# 2. 获取证书
sudo certbot --nginx -d your-domain.com

# 3. 自动续期测试
sudo certbot renew --dry-run
```

---

## 十、数据备份

```bash
# 备份数据库
pg_dump -U risk_user risk_db > backup_$(date +%Y%m%d).sql

# 备份数据目录
tar -czf risk_data_$(date +%Y%m%d).tar.gz /opt/risk-system/data
```

---

## 十一、更新升级

```bash
cd /opt/risk-system
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build
sudo systemctl restart risk-backend risk-frontend
```

---

## 技术支持

- GitHub Issues: https://github.com/snrzz/risk/issues
- 详细文档: /opt/risk-system/docs/
- API文档: http://localhost:8000/api/docs/
