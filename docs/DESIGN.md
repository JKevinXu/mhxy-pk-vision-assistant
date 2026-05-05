# MHXY PK Vision Assistant 设计文档

## 1. 背景

用户希望在梦幻西游手游 PK 中“看到对方血条”。直接显示对方真实血量会破坏公平性，并可能违反游戏协议。项目因此重构为合规训练工具：基于录像、截图、公开可见信息与人工录入，做赛后复盘和血量区间估算。

## 2. 目标与非目标

### 目标

- 提供 PK 录像/截图复盘工作流。
- 建立回合制战斗事件模型。
- 基于公开可见事件估算单位血量区间。
- 输出可解释的复盘报告，而非不可验证的“真实血量”。
- 保持本地优先，不上传敏感素材。

### 非目标

- 不显示游戏未公开的对方真实血量。
- 不读取游戏内存、封包、进程、日志私有文件。
- 不 hook、注入、修改游戏客户端。
- 不做自动战斗、自动点击、自动决策。
- 不规避反外挂或平台检测。

## 3. 用户场景

1. 玩家赛后导入自己的录屏，手动标注每回合关键事件，生成复盘总结。
2. 指挥训练时，录入预估属性和伤害结果，观察对面单位可能剩余血量区间。
3. 内容创作者对授权素材做时间线标注，输出讲解图或文字稿。

## 4. 系统架构

```text
本地录像/截图/人工输入
        |
        v
Frame/Asset Importer  ---->  Manual Annotation UI
        |                            |
        v                            v
Visible Signal Extractor       Battle Event Store
        |                            |
        +------------+---------------+
                     v
            HP Interval Engine
                     |
                     v
           Timeline + Report Export
```

### 模块说明

- Importer：读取本地视频/截图，抽帧，保存素材索引。
- Annotation UI：标注单位、回合、伤害、治疗、倒地、拉人、召唤等事件。
- Visible Signal Extractor：仅处理画面公开可见元素，例如文本、数字、图标、血条长度，不做隐藏状态恢复。
- Battle Event Store：以结构化 JSON 保存标注事件。
- HP Interval Engine：用区间而非单点表示血量，例如 `[1200, 2600]`。
- Report Export：导出 Markdown/HTML 复盘报告。

## 5. 数据模型草案

```json
{
  "match_id": "local-2026-05-05-001",
  "units": [
    {"id": "enemy_fc", "side": "enemy", "role": "方寸", "max_hp_range": [4500, 7500]},
    {"id": "ally_dt", "side": "ally", "role": "大唐", "max_hp_range": [5500, 8500]}
  ],
  "events": [
    {"turn": 1, "actor": "ally_dt", "target": "enemy_fc", "type": "damage", "amount": 1800},
    {"turn": 1, "target": "enemy_fc", "type": "visible_state", "state": "alive"}
  ]
}
```

## 6. 血量区间估算逻辑

每个单位维护：

- `max_hp_range`: 最大血量估计区间。
- `current_hp_range`: 当前血量估计区间。
- `state`: alive/down/unknown。

更新规则：

- 受到伤害 `d`：`current = [max(0, low-d), max(0, high-d)]`。
- 获得治疗 `h`：`current = [min(max_low, low+h), min(max_high, high+h)]`，如果最大血量未知则保持上界保守。
- 可见倒地：`current = [0, 0]` 或 `[0, death_threshold]`，视游戏机制定义。
- 可见存活：`current.high >= 1`，若此前区间全 0，则需要标注复活/拉人事件。

输出必须展示“估算依据”和“不确定性”，避免伪装成真实数值。

## 7. UI 设计

MVP UI 推荐 Streamlit：

- 左侧：素材导入与回合选择。
- 中间：当前帧/截图预览与事件标注。
- 右侧：单位列表、当前血量区间、关键事件摘要。
- 底部：时间线与导出按钮。

视觉原则：

- 明确标注“估算/训练/复盘”。
- 区间用渐变条显示，不用“精确血条”误导用户。
- 对不确定事件显示警告图标。

## 8. 安全与合规检查清单

每个功能 PR 必须回答：

1. 数据来源是什么？是否是用户授权的录像/截图/手工输入？
2. 是否读取或修改游戏客户端、进程、内存、封包？必须为否。
3. 是否自动操作游戏？必须为否。
4. 是否显示游戏原本隐藏的信息？必须为否。
5. 是否可能被用于实时作弊？若可能，必须降级为离线/复盘模式或删除。

## 9. 技术栈

- Python 3.10+
- Pydantic：事件与单位数据校验。
- OpenCV/Pillow：离线视频/截图处理，可选。
- Streamlit：MVP 本地 UI，可选。
- Pytest/Ruff：测试与 lint。

## 10. 里程碑

- M0：仓库、文档、合规守卫。
- M1：事件 JSON schema、血量区间引擎、单元测试。
- M2：本地 Streamlit 事件编辑器。
- M3：录像抽帧与截图导入。
- M4：Markdown/HTML 复盘报告导出。
- M5：可选 OCR，但只识别公开可见文本。
