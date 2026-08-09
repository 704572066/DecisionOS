# Sprint 3-2.2.1：Runtime Fact Bootstrap Hotfix

首次 Runtime State 从 Context 初始化 `discountPercent` 与 `paymentTermDays`。
已有 Runtime State 时不会覆盖 reducer 已维护的新值。

合并：

```bash
python scripts/apply_sprint3_2_2_1_patch.py
```

无需数据库迁移。
