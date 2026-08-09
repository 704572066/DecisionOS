# Sprint 3-2.3.2：Decision Board Flex Height Hotfix

## 根因

`height: auto` 不能覆盖 Flexbox 的空间分配行为。

如果旧样式中存在：

```css
.board-section {
  flex: 1;
}
```

或：

```css
.board-section {
  flex-grow: 1;
}
```

那么 Risks / Actions / Todos 即使设置 `height:auto`，仍会平均分配父容器剩余高度。

## 修复

这版显式设置：

```css
.decision-board-scroll > .board-section {
  flex: 0 0 auto !important;
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
  flex-basis: auto !important;
  height: auto !important;
}
```

所以：

```text
Risks 1条  → 1条高度
Risks 2条  → 2条高度

Actions 1条 → 1条高度
Todos 3条   → 3条高度
```

只有整个 `.decision-board-scroll` 负责占据剩余空间并滚动。

## 合并

```bash
python scripts/apply_sprint3_2_3_2_patch.py

cd src/frontend
npm run build
```

浏览器部署后建议强制刷新：

```text
Ctrl + F5
```

避免浏览器缓存旧 CSS。
