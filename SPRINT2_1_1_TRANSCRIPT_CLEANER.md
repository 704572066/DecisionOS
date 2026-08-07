# Sprint 2-1.1

新增 `cleanTranscriptWindow`，保留原始 `transcriptWindow`；Context 提取和检索改用清洗文本。

修复内容：
- 重复句与高相似句合并；
- 短口语噪声过滤；
- 少量已观测 ASR 错词保守替换；
- 收紧客户/公司/项目实体识别；
- 增加 `metadata.cleaning`。

无需数据库迁移。
