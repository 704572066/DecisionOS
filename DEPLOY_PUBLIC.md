# DecisionOS 公网服务器部署

## 服务器要求

- Linux x86_64
- Docker Engine 24+ 与 Docker Compose v2
- 建议至少 2 核 CPU、4 GB 内存、20 GB 磁盘
- 公网只开放 SSH、80；启用 HTTPS 后再开放 443
- 不开放 5432、8000、5173

## 部署

```bash
git clone -b master https://github.com/704572066/DecisionOS.git
cd DecisionOS
cp .env.prod.example .env.prod
vi .env.prod
```

必须修改：

```env
POSTGRES_PASSWORD=足够长的随机密码
PUBLIC_ORIGIN=http://你的公网IP
```

生成随机密码：

```bash
openssl rand -base64 36
```

启动：

```bash
chmod +x scripts/deploy-public.sh scripts/update-public.sh
./scripts/deploy-public.sh
```

访问：

- Web：`http://公网IP/`
- API 文档：`http://公网IP/docs`
- 健康检查：`http://公网IP/health`

## 防火墙

CentOS/RHEL：

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

Ubuntu：

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

云安全组同样只开放 80/443，不开放 5432、8000、5173。

## 检查

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f --tail=200
curl http://127.0.0.1/health
```

## 更新

```bash
./scripts/update-public.sh
```

## 安全提示

当前 Demo 尚无完整登录和权限体系，只适合受控测试。优先限制来源 IP，不上传真实合同、客户隐私或敏感数据。正式对外开放前必须加入 HTTPS、身份认证和权限控制。
