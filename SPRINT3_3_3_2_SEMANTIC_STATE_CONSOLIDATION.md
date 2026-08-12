# Sprint 3-3.3.2 Semantic State Consolidation

目标：在 Semantic Runtime 与后续 Active Risk Reasoning 之间增加稳定的 `decisionState`。

- `semanticHistory`: 会议中发生过的语义历史。
- `semanticState`: 各参与方当前语义立场。
- `decisionState`: 当前有效、可供风险推理消费的决策条件。

本阶段不修改 Decision Board UI，不增加 Active Risk Reasoning，不扩充正则事件规则。
