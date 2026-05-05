# MHXY PK Vision Assistant 设计文档

## 1. 背景

用户希望在梦幻西游手游 PK 中“看到对方血条”。直接显示对方真实血量会破坏公平性，并可能违反游戏协议。项目因此重构为合规训练工具：基于录像、截图、公开可见信息与人工录入，做赛后复盘和血量区间估算。

## 2. 目标与非目标

### 目标

- 提供 PK 录像/截图复盘工作流。
- 面向 macOS + MuMu 模拟器场景提供只读画面导入与 ROI 标定方案。
- 建立回合制战斗事件模型。
- 基于公开可见事件估算单位血量区间。
- 输出可解释的复盘报告，而非不可验证的“真实血量”。
- 保持本地优先，不上传敏感素材。

### 非目标

- 不显示游戏未公开的对方真实血量。
- 不读取游戏内存、封包、进程、日志私有文件。
- 不 hook、注入、修改游戏客户端或 MuMu 模拟器。
- 不做自动战斗、自动点击、自动决策。
- 不通过 ADB、Accessibility、LaunchAgent 或脚本对游戏执行操作。
- 不规避反外挂或平台检测。

## 3. 用户场景

1. 玩家赛后导入自己的录屏，手动标注每回合关键事件，生成复盘总结。
2. 指挥训练时，录入预估属性和伤害结果，观察对面单位可能剩余血量区间。
3. 内容创作者对授权素材做时间线标注，输出讲解图或文字稿。
4. 玩家在 macOS 的 MuMu 模拟器中运行游戏，用 MuMu 窗口截图或 macOS 录屏做离线复盘。
5. 玩家复用既有师门任务库中成熟的截图、Retina 坐标换算、OpenCV 模板匹配经验，但仅用于只读画面识别。

## 4. 系统架构

```text
MuMu 窗口截图 / macOS 录屏 / OBS-QuickTime 录像 / 人工输入
        |
        v
Capture/Asset Importer  ---->  ROI Calibration  ---->  Manual Annotation UI
        |                            |                         |
        v                            v                         v
Visible Signal Extractor       Template Registry        Battle Event Store
        |                            |                         |
        +------------+---------------+-------------------------+
                     v
            HP Interval Engine
                     |
                     v
           Timeline + Report Export
```

### 模块说明

- Capture/Asset Importer：读取 MuMu 窗口截图、本地录屏或 OBS/QuickTime 录像，抽帧并保存素材索引。
- ROI Calibration：记录 MuMu 窗口位置、游戏画面区域、Retina 缩放因子、常用 ROI，例如回合区、单位区、状态图标区。
- Template Registry：管理只读模板素材与元数据，例如模板路径、适用分辨率、置信度阈值、是否仅用于公开可见 UI。
- Annotation UI：标注单位、回合、伤害、治疗、倒地、拉人、召唤等事件。
- Visible Signal Extractor：仅处理画面公开可见元素，例如文本、数字、图标、血条长度，不做隐藏状态恢复。
- Battle Event Store：以结构化 JSON 保存标注事件。
- HP Interval Engine：用区间而非单点表示血量，例如 `[1200, 2600]`。
- Report Export：导出 Markdown/HTML 复盘报告。

### MuMu 模拟器适配

模拟器场景只作为输入采集便利项，不作为客户端插件入口。已知运行环境是 macOS + MuMu，且用户已有 `JKevinXu/GameAutomation` 师门任务仓库，可借鉴其中的只读视觉工程经验。

#### 可复用经验

- 应用定位：MuMu 默认路径可按 `/Applications/MuMuPlayer.app` 检查，但本项目不负责启动或控制游戏。
- macOS 权限：截图/录屏需要 Screen Recording 权限；PK Vision Assistant 不应要求 Accessibility 权限，因为它不点击或控制游戏。
- Retina 坐标：用逻辑屏幕尺寸和物理截图尺寸计算缩放因子，避免模板匹配坐标与 UI 显示坐标错位。
- 模板匹配：可使用 OpenCV `matchTemplate` 识别公开可见 UI 元素，并保存 best confidence、匹配位置和 debug 截图。
- 模板目录：将 MuMu/梦幻西游公开 UI 模板放在 `assets/templates/mumu/`，不要混入会鼓励自动点击的命名，例如 `click_*`。

#### MVP 采集流程

1. 用户手动打开 MuMu 和游戏，并进入需要复盘的录像/战斗画面。
2. 工具请求选择一个截图、录屏文件，或选择 MuMu 窗口区域。
3. 工具读取帧并计算 Retina 缩放因子。
4. 用户手动标定 ROI：游戏画面区域、回合文本区域、己方/敌方单位区域、状态图标区域。
5. 工具仅在 ROI 内做公开可见信息识别，并把结果作为“候选标注”交给用户确认。
6. 用户确认后写入事件表，再进入血量区间估算。

#### 明确禁止

- 不读取 MuMu 或游戏进程内存。
- 不 hook MuMu 渲染层或 macOS 图形 API。
- 不使用 ADB 与游戏交互。
- 不使用 PyAutoGUI/Accessibility 对游戏窗口点击、拖拽、滚动、键盘输入。
- 不使用 LaunchAgent 定时执行游戏操作。
- 不把模板匹配结果直接转成游戏操作。

## 5. 数据模型草案

```json
{
  "match_id": "local-2026-05-05-001",
  "capture": {
    "source_type": "mumu_recording",
    "file_path": "data/local/match-001.mov",
    "emulator": "MuMuPlayer",
    "screen_scale_factor": 2.0,
    "game_roi": {"x": 120, "y": 80, "width": 1280, "height": 720}
  },
  "templates": [
    {
      "id": "turn_indicator",
      "path": "assets/templates/mumu/turn_indicator.png",
      "roi": "turn_area",
      "confidence_threshold": 0.8,
      "visible_only": true
    }
  ],
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
- 中间：当前帧/截图预览、ROI 框选、事件标注。
- 右侧：单位列表、当前血量区间、模板匹配候选、关键事件摘要。
- 底部：时间线、debug confidence、导出按钮。

视觉原则：

- 明确标注“估算/训练/复盘”。
- 区间用渐变条显示，不用“精确血条”误导用户。
- 对不确定事件显示警告图标。
- 模板识别结果默认是“候选”，需要用户确认后才进入事件表。
- 任何画面叠加都不得命名为“对方真实血条”，只能命名为“估算区间/复盘标注”。

## 8. 安全与合规检查清单

每个功能 PR 必须回答：

1. 数据来源是什么？是否是用户授权的录像/截图/手工输入？
2. 是否读取或修改游戏客户端、进程、内存、封包？必须为否。
3. 是否自动操作游戏？必须为否。
4. 是否显示游戏原本隐藏的信息？必须为否。
5. 是否可能被用于实时作弊？若可能，必须降级为离线/复盘模式或删除。
6. 如果运行在 MuMu 模拟器中，是否使用了 ADB、进程注入、窗口 hook、内存/封包读取？必须为否。
7. 是否需要 Accessibility 权限或 PyAutoGUI 点击游戏？必须为否。
8. 是否从 `GameAutomation` 迁移了自动点击、LaunchAgent 定时执行或任务流程？必须为否；只允许迁移截图、Retina 缩放、模板匹配等只读视觉技术。

## 9. 技术栈

- Python 3.10+
- Pydantic：事件与单位数据校验。
- OpenCV/Pillow：离线视频/截图处理、模板匹配、debug 图输出，可选。
- PyAutoGUI：仅可用于截图和读取屏幕尺寸；不得用于点击或键盘输入。
- Streamlit：MVP 本地 UI，可选。
- Pytest/Ruff：测试与 lint。

## 10. 里程碑

- M0：仓库、文档、合规守卫。
- M1：事件 JSON schema、血量区间引擎、单元测试。
- M2：本地 Streamlit 事件编辑器。
- M3：MuMu 录屏/截图导入、Retina 缩放检测、ROI 标定。
- M4：只读模板匹配候选标注与 debug confidence 输出。
- M5：Markdown/HTML 复盘报告导出。
- M6：可选 OCR，但只识别公开可见文本。
