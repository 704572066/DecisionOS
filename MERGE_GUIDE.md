# 合并指南

将本目录内容复制到现有 DecisionOS 仓库根目录：

```bash
cp -R DecisionOS_Demo_Baseline/* /path/to/DecisionOS/
cp DecisionOS_Demo_Baseline/.env.example /path/to/DecisionOS/
```

然后：

```bash
cd /path/to/DecisionOS
cp .env.example .env
docker compose up --build
```

建议提交信息：

```bash
git add -A
git commit -m "feat: add DecisionOS v0.1 demo baseline"
git push
```
