# DecisionOS Demo Baseline

这是 DecisionOS V0.1 的可运行 Demo 基线，验证以下闭环：

1. 导入历史企业知识；
2. 创建会议并持续追加文本；
3. 根据当前议题检索历史知识；
4. 返回带来源的主动提醒；
5. 确认并保存 Decision、Task、Evidence；
6. 下一次会议可再次检索已沉淀内容。

## 启动

```bash
cp .env.example .env
docker compose up --build
```

访问：

- 前端：http://localhost:5173
- API：http://localhost:8000/docs

## 演示步骤

1. 点击“导入示例知识”；
2. 点击“创建会议”；
3. 输入：`客户要求整体价格下降18%，并希望付款周期延长到90天。`；
4. 点击“分析当前内容”；
5. 查看历史折扣、付款周期和利润率规则提醒；
6. 填写并保存决策与任务；
7. 创建下一次会议，检索刚才沉淀的决策。

## 模型行为

- 未配置 OpenAI-compatible 接口时，系统使用确定性规则生成 Demo 提醒，保证离线可演示；
- 配置 `OPENAI_BASE_URL`、`OPENAI_API_KEY` 和 `OPENAI_MODEL` 后，可启用大模型增强总结。

## 合并到现有仓库

将本压缩包内容复制到 DecisionOS 仓库根目录。它不会修改现有 `docs/` 文档。
