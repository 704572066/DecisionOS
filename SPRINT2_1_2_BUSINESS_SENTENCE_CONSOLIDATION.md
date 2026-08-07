# Sprint 2-1.2：Business Sentence Consolidation

## 目标

在 Sprint 2-1.1 的去重、降噪和实体修复基础上，将相邻业务片段整理为完整、
稳定、适合后续 Retriever 的业务陈述。

## 新增能力

- 修正 `100分18%`、`百分之18` 等百分比 ASR 噪声；
- 合并价格、付款、交付等相邻业务句；
- 过滤无主题、无实体、无数值、无业务动作的低信息密度口语；
- 识别并降权/排除 `下降18%`、`客户要求整体价格` 等不完整片段；
- 为清洗后的完整业务句补充句号；
- 新增清洗指标：
  - `consolidatedSentences`
  - `incompleteSegments`
- Builder 版本升级为 `context-builder-v0.1.2`。

## 理想结果

原始：

```text
客户要求整体价格下降18%
并希望付款周期延长到180天
客户要求整体价格下降18%
并希望副感周期延长到180天
客户要求整体价格下降100分18%
下降18%
你不要觉得你一买
客户要求整体价格
```

清洗：

```text
客户要求整体价格下降18%，并希望付款周期延长到180天。
```

## 合并

覆盖：

```text
src/backend/app/context/cleaner.py
src/backend/app/context/models.py
```

新增：

```text
tests/test_business_sentence_consolidation.py
examples/context/sprint2-1-2-noisy-transcript.txt
```

不需要数据库迁移。

## 部署

```bash
git add -A
git commit -m "fix: consolidate business transcript sentences"
git push

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  build --no-cache backend

docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  up -d
```

## 验证

```bash
curl http://127.0.0.1/api/meetings/实际会议ID/context
```

检查：

- `builderVersion` 为 `context-builder-v0.1.2`；
- `cleanTranscriptWindow` 尽量收敛为完整业务陈述；
- `100分18%` 不再出现；
- `你不要觉得你一买` 不再出现；
- `下降18%`、`客户要求整体价格` 等残片不再单独出现；
- `18%` 和 `180天` 仍能被 facts 提取；
- references 不退化。
