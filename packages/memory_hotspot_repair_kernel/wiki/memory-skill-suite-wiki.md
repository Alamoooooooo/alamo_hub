# Memory Hotspot Skill Suite Wiki

## 摘要

本文档介绍一套面向内存热点问题的 skill suite，包括其设计目标、架构分层、执行方式、迁移方法和运行案例。该套件用于识别代码中的高峰值内存风险、提供行为保守的修复建议、在修复后执行独立复核，并支持在不同项目和不同宿主环境之间迁移。

与一般性能优化工具不同，这套 skill suite 的重点不是自动寻找所有性能问题，也不是替代 profiler，而是围绕“峰值内存风险”建立一套稳定、可复用、可验证的工程工作流。

当前套件由四个核心 skill 组成：

- `memory-check`
- `memory-fix`
- `memory-review`
- `memory-optimizer-agent`

四者共同形成“检查、修复、验证、复核”的闭环。为提升通用性，套件同时引入了协议层、模式库、overlay 机制和双后端执行路径。

---

## 1. 问题背景

### 1.1 为什么需要单独关注 memory hotspot

在数据处理、特征工程、因果推断、推荐排序、离线评分等场景中，任务失败常常不是由语法错误或显式逻辑错误引起，而是由峰值内存突然升高引起。此类问题通常具有以下特点：

- 小规模样本可以正常运行，规模增大后才暴露问题
- 风险常常出现在 materialization、复制放大、阻塞算子或 fallback 路径中
- 问题位置不一定是主要业务逻辑，往往隐藏在读写、转换、聚合或推理边界
- 普通 code review 可以发现一部分风险，但难以系统识别峰值内存问题

典型情况包括：

- 大型 parquet 结果一次性转为 pandas DataFrame
- 看似在做 chunking，实际仍然是全量读入后再切块
- 流式执行在关键节点退化为 eager collect
- DataFrame、NumPy array、模型输入和预测结果同时驻留内存
- 前部热点被修复后，峰值转移到排序、聚合或报表阶段

因此，memory hotspot 更适合被视为一种专门的工程审查对象，而不是零散地并入一般代码检查。

### 1.2 为什么不直接使用 profiler 替代

profiler 更适合回答运行期问题，例如：

- 真实热点是否存在
- 优化前后内存曲线如何变化
- 哪一步在运行中消耗最多内存

本套件更适合回答设计期和审查期问题，例如：

- 哪个位置最可能形成峰值
- 当前代码是否存在假 chunking 或隐藏 materialization
- 修复动作是否改变了业务行为
- 在无法完整运行真实大数据任务时，应如何组织检查和修复流程

因此，两者关系不是替代，而是互补。本套件主要承担工程组织和静态分析支持的角色。

---

## 2. 目标与边界

### 2.1 设计目标

本套件的核心目标如下：

- 结构化识别 memory hotspot，并明确热点位置、风险等级和优先顺序
- 提供行为保守的修复建议或修复动作，避免静默改变业务语义
- 在修复后执行独立复核，识别 moved peak、回归和 correctness 风险
- 支持跨项目迁移，降低在新仓库中重新设计 prompt 的成本
- 降低对单一宿主环境的依赖，使其可以在不同运行方式之间切换

### 2.2 非目标

本套件明确不承担以下职责：

- 不替代 profiler、监控系统或完整性能测试
- 不保证一次性自动修复所有内存问题
- 不以改变业务语义为代价换取内存改善
- 不要求所有项目都建立 overlay
- 不试图成为通用性能优化框架

因此，本套件应被理解为“围绕内存峰值风险的结构化工程工作流”，而不是“自动优化黑盒”。

---

## 3. 总体架构

### 3.1 四个核心 skill

#### `memory-check`

用于识别内存热点，并产出结构化的风险报告。主要关注：

- 第一处真实 materialization 在何处发生
- 最大对象在内存中可能同时存在几份
- 当前代码中有哪些 safeguard
- 哪些结论仅凭静态分析无法完全确认

#### `memory-fix`

用于针对已识别热点执行保守修复。其目标不是自由重构，而是用最小改动降低峰值内存风险，并尽量保持原有业务行为不变。

#### `memory-review`

用于对修复结果执行独立复核。它首先仍是代码审查，其次才是内存专项审查。该步骤用于识别下列问题：

- 改善是否真实成立
- 峰值是否仅被转移
- fallback、resume、overwrite 等行为是否被破坏
- 是否引入新的 correctness 风险

#### `memory-optimizer-agent`

用于组织前述三个 skill 的执行顺序。它承担调度与宿主适配职责，形成一条有限循环：

1. `check`
2. `fix`
3. `validation`
4. `review`
5. `stop or continue`

其中：

- `orchestration` 指对流程的调度与串联
- `host adapter` 指与具体运行环境相关的适配层

### 3.2 整体工作流

从功能角度看，这套系统可以概括为一条内存风险处理流水线：

1. 识别最值得优先处理的热点
2. 对热点执行保守修复
3. 进行小范围验证
4. 对修复结果做独立复核
5. 根据风险剩余情况决定是否进入下一轮

其核心价值不在于单个 prompt 的表达质量，而在于职责拆分和闭环完整性。

### 3.3 五层分层模型

为实现可迁移性，套件采用五层结构：

- `Core skill layer`：核心 skill 的职责定义
- `Protocol layer`：输出字段、判断标准和结构化协议
- `Pattern library layer`：按技术栈组织的通用模式库
- `Overlay layer`：项目专有经验与局部约束
- `Host adapter layer`：与执行环境相关的适配层

可以将其理解为：

- 顶层定义“做什么”
- 中间层定义“依据什么知识去做”
- 底层定义“在什么环境里做”

### 3.4 分层原因

如果不做分层，所有规则通常会堆积在单一 prompt 中，容易产生以下问题：

- 通用规则和项目特例混杂
- 在新项目中难以复用
- 宿主变化时需要整体重写
- 读者难以判断哪些是稳定方法，哪些是局部经验

分层后的职责划分如下：

- 核心 skill 负责流程分工
- 协议层负责输出一致性
- 模式库负责通用知识复用
- overlay 负责项目局部知识
- host adapter 负责宿主执行差异

### 3.5 Progressive disclosure

本套件采用渐进式披露原则。信息不集中堆叠在单一入口文件中，而是按层次组织：

- `SKILL.md`：职责、工作流、输出契约、引用路由
- `references/`：协议、模板、模式库、引用、使用说明
- `overlays/`：repo-specific 规则

这样做的收益是：

- 减少主上下文冗余
- 便于跨项目复用
- 便于宿主按需加载
- 便于长期维护

![图 1. Memory hotspot skill suite 的总体架构与五层知识分层](./assets/memory-skill-suite-architecture.svg)

**图 1** 展示了整体工作流和五层分层模型。上半部分对应四个核心 skill 的闭环关系，下半部分对应知识组织结构。

---

## 4. 工程结构

### 4.1 主目录

当前在 skill hub 中的 package 开发源目录位于：

`packages/memory_hotspot_repair_kernel/`

主要目录包括：

- `memory-check/`
- `memory-fix/`
- `memory-review/`
- `memory-optimizer-agent/`
- `references/`
- `scripts/`

### 4.2 单个 skill 的基本结构

每个核心 skill 基本遵循相同布局：

- `SKILL.md`
- `agents/openai.yaml`
- `references/`

统一结构有助于：

- 迁移
- 同步
- 自动化读取
- 维护一致性

### 4.3 关键文件

最值得阅读的入口文件包括：

- `memory-check/SKILL.md`
- `memory-check/references/decision-protocol.md`
- `memory-check/references/source-citations.md`
- `memory-fix/references/remediation-protocol.md`
- `memory-review/references/review-protocol.md`
- `memory-optimizer-agent/SKILL.md`
- `memory-optimizer-agent/references/host-adapter.md`
- `memory-optimizer-agent/references/generic.run.yaml`
- `memory-optimizer-agent/references/generic.prompt_bundle.yaml`
- `scripts/sync_to_codex_home.py`

与运行证据相关的产物包括：

- `summary.md`
- `prompt_bundle/README.md`
- `validation/validation.json`

这些路径表示运行产物的典型形态，而不是当前分享仓库中默认随包提供的固定目录。
在当前 `alamo_skillhub` 仓库中，`runs/` 不作为分发内容保留；运行案例主要通过文档、图示和可移植配置来说明。

---

## 5. 核心组件设计

### 5.1 `memory-check`

`memory-check` 是整套体系的入口组件。其目标不是立即修复，而是先稳定定义问题。

典型输入包括：

- target paths
- 当前代码树
- 必要时的 overlay

典型输出包括：

- `Executive Summary`
- `Stack Profile`
- `Hot Path`
- `Findings`
- `Existing Safeguards`
- `Recommended Fix Order`
- `Validation Gaps`

其判断过程受 `decision-protocol.md` 约束，常用字段包括：

- `severity`
- `pattern_id`
- `hot_path_stage`
- `why_peak_occurs`
- `confidence`
- `runtime_validation_needed`

### 5.2 `memory-fix`

`memory-fix` 的基本策略是“以最小改动换取最实际的峰值改善”。优先处理的方向包括：

- 消除 full materialization
- 将假 chunking 推回真实读边界
- 减少复制放大
- 避免将热点迁移到下游聚合或报表阶段

其输出不仅是补丁，还应说明：

- 修复了什么模式
- 为什么这样修可以降低峰值
- 哪些行为契约被保留
- 哪些问题仍然未解决

对应协议字段包括：

- `target_pattern_id`
- `mitigation_pattern`
- `contract_preserved`
- `expected_peak_effect`

### 5.3 `memory-review`

`memory-review` 的职责是在修复之后进行独立复核。其重点不只是“内存是否下降”，还包括：

- 是否出现假改善
- 是否发生 moved peak
- fallback 是否失真
- 状态恢复语义是否被破坏
- 是否引入新的 correctness 问题

典型协议字段包括：

- `finding_kind`
- `blocking_level`
- `claimed_improvement_verified`
- `new_peak_risk`

### 5.4 `memory-optimizer-agent`

`memory-optimizer-agent` 是 orchestration 层，也是 host adapter 层。其核心职责包括：

- 控制多轮 bounded loop
- 执行 preflight
- 处理 degraded mode
- 编排 validation
- 注入 overlay
- 生成 artifacts
- 支持 resume 与 partial rerun

其定位不是通用规则中心，而是宿主适配中心。换言之：

- 内存规则应保留在 `memory-check / fix / review`
- 宿主耦合逻辑应保留在 agent 层

默认 loop 为：

1. 运行 `memory-check`
2. 选择最高价值修复目标
3. 运行 `memory-fix`
4. 执行 focused validation
5. 运行 `memory-review`
6. 决定是否继续

默认最多执行 2 轮。仅在明确要求更激进优化时提升到 3 轮。

---

## 6. 协议层、模式库与 overlay

### 6.1 协议层

协议层用于将判断和修复结果约束为稳定结构，减少纯 prose 输出带来的不稳定性。其主要价值包括：

- 统一字段表达
- 提高跨轮次可比较性
- 支持后续评估与自动分析

三个主要协议文件分别对应：

- `decision-protocol.md`
- `remediation-protocol.md`
- `review-protocol.md`

### 6.2 模式库

模式库按技术栈分组，而不是按项目分组。覆盖内容通常包括：

- Universal patterns
- pandas
- DuckDB
- Arrow / Parquet
- CSV
- NumPy
- Polars
- model inference
- GC / cleanup

这样做的原因是技术栈经验更稳定、更适合跨项目复用。

### 6.3 Overlay 机制

overlay 指只对某个项目、某条 pipeline 或某类局部实现有意义的补充规则层。
它用于承载项目专有、重复出现且高价值的局部规则。它适合存放：

- repo-specific 热点模式
- 行为契约
- validation hints
- 特殊 review targets

不适合存放：

- 通用 pandas 规则
- 通用 DuckDB 规则
- 通用 Arrow / NumPy / Polars 规则

当前仓库中提供了一个真实 example overlay：

- `segment-causal-pipeline-v2`

对应文件包括：

- `examples/memory_hotspot_repair_kernel/segment_causal_pipeline_v2/overlays/memory-check/`
- `examples/memory_hotspot_repair_kernel/segment_causal_pipeline_v2/overlays/memory-fix/`
- `examples/memory_hotspot_repair_kernel/segment_causal_pipeline_v2/overlays/memory-review/`

主要描述的热点形态包括：

- broad parquet scan
- fake chunking
- frame / NumPy / prediction 同时存在
- ranking 或 report 成为新峰值

此外还提供了：

- `packages/memory_hotspot_repair_kernel/references/overlay-pattern.md`
- `packages/memory_hotspot_repair_kernel/references/generic-overlay-template.md`

用于支持新项目快速建立 overlay。

需要强调的是：

- `packages/` 中保留的是通用、可迁移的核心能力
- `examples/` 中保留的是 repo-specific overlay 和示例配置
- example overlay 不会自动并入 core package 的默认规则集

![图 2. Core 规则与 overlay 规则的职责边界](./assets/memory-skill-suite-overlay.svg)

**图 2** 展示了 core 与 overlay 的职责分界。该边界直接决定套件是否具有可迁移性。

---

## 7. 执行后端

### 7.1 `codex` backend

早期主要执行路径是 `codex` backend，其优点包括：

- 自动化程度高
- 可以在 orchestrator 内完成完整闭环
- 产物可直接落入 `runs/` 目录

但实际运行中也暴露出明显问题：

- `codex.cmd` 在 Linux/WSL 下不兼容
- 某些 CLI 参数透传位置错误会导致失败
- preflight 可能受到 auth 或 app-server 问题阻塞

因此，它是可用后端，但不应是唯一后端。

### 7.2 `prompt-bundle` backend

为降低宿主耦合，后续引入 `prompt-bundle` backend。该后端不直接执行模型，而是生成一整轮宿主无关的提示包：

- `check.prompt.md`
- `fix.prompt.md`
- `review.prompt.md`
- `bundle.json`
- `README.md`

其优势包括：

- 降低对 Codex runtime 的依赖
- 提供可分享、可归档的 prompt 产物
- 允许外部宿主复用工作流

### 7.3 degraded mode

`degraded mode` 指在完整自动执行条件不满足时，系统退化为保留部分能力的执行状态。

当 `codex` backend 的 preflight 失败但允许退化执行时，系统进入 degraded mode。该模式不能替代完整闭环，但仍具有以下价值：

- 可继续执行本地 validation
- 可继续生成 artifacts
- 可记录宿主故障原因

因此，它对于区分环境问题和代码问题仍然重要。

![图 3. Codex backend 与 prompt-bundle backend 的执行路径与产物对比](./assets/memory-skill-suite-backends.svg)

**图 3** 对比了两类后端的依赖、流程和输出产物。二者共享核心规则，但不共享运行条件。

---

## 8. 配置与轮次控制

### 8.1 核心字段

配置体系主要围绕以下字段组织：

- `workspace_root`
- `target_paths`
- `execution_backend`
- `profiles`
- `validation_commands`
- `check_prompt_extra`
- `fix_prompt_extra`
- `review_prompt_extra`

### 8.2 profile 设计

当前标准 profiles 为：

- `fast = 1轮`
- `default = 2轮`
- `aggressive = 3轮`

需要注意：

- 从方法论层面，默认 loop 上限仍为 2 轮
- 从具体配置层面，可以用 `default_profile` 覆盖默认执行 profile

### 8.3 配置示例

在当前通用 prompt-bundle 配置中：

- `execution_backend: prompt-bundle`
- `default_profile: fast`
- `fast.max_rounds: 1`
- `default.max_rounds: 2`
- `aggressive.max_rounds: 3`

这意味着该 starter config 的默认行为是执行 1 轮 prompt-bundle 导出，而不是自动执行 2 轮闭环。

设计原因是：

- 先提供最稳妥的迁移入口
- 先验证知识结构，再验证宿主自动化

---

## 9. Validation 与依赖诊断

### 9.1 为什么 validation 不能只有 pass/fail

单纯的 pass/fail 在工程上信息不足。validation 失败可能来自：

- 代码逻辑错误
- smoke 输入不正确
- shell 风格不兼容
- 解释器命令不存在
- 缺少第三方依赖

因此，失败原因必须进一步解释。

### 9.2 已处理的可移植性问题

实际迭代中已处理过多类执行层问题，包括：

- `python` 与 `python3` 差异
- PowerShell 风格 here-string 在 bash 下失败
- 配置中混入 Windows 风格命令

这些问题虽小，但直接决定系统是否能够跨环境迁移。

### 9.3 dependency diagnostics

后续补充了一层 dependency diagnostics，用于从 validation stderr 中提取高信号依赖错误。例如当前已可稳定识别：

- `ModuleNotFoundError: No module named 'duckdb'`

该信息会写入：

- `validation.json`
- `summary.md`
- prompt-bundle 的 `README.md`

其意义在于首次将“环境问题”和“代码问题”系统地拆开。

---

## 10. 真实运行案例

### 10.1 案例目的

仅有设计说明不足以证明该套件具备实际工程价值。因此，本节选取一轮历史真实运行，用于说明：

- 套件如何在受限宿主环境中仍然产生有效产物
- validation 失败如何被正确解释
- prompt-bundle 模式为何是可用的迁移路径

### 10.2 案例概况

该轮运行的关键状态如下：

- 运行模式：`prompt-bundle`
- 运行状态：`completed`
- 使用 profile：`fast`
- 实际执行轮数：`1`
- 停止原因：`prompt_bundle_generated`

其含义是：系统未在当时宿主中自动完成完整闭环，而是优先稳定导出一整套可迁移的提示包，并执行本地最小验证。

这一案例用于说明工作流和判断逻辑，不表示当前分享仓库默认包含同名运行目录。

### 10.3 实际执行过程

该轮运行可以还原为以下步骤：

1. 读取配置，解析 target paths、profile 和 backend
2. 识别当前使用的是 `prompt-bundle` 模式
3. 导出 `check.prompt.md`、`fix.prompt.md`、`review.prompt.md`、`bundle.json` 和 `README.md`
4. 执行本地 validation
5. 将 validation 失败进一步分类为依赖问题而不是代码回归

该轮运行的成功点不在于自动修复代码，而在于：

- 在宿主受限时仍生成可用工件
- 对失败原因做出可执行解释

### 10.4 诊断结果

summary 中记录的高信号信息包括：

- `Validation passed: False`
- `Dependency diagnostics: duckdb`
- `Decision: prompt_bundle_only`

这些信息表明：

- validation 未完全通过
- 关键原因是环境缺少 `duckdb`
- 系统因此停止在 prompt bundle 导出阶段，而不是误判为代码损坏并继续盲目执行

### 10.5 `README.md` 的作用

该轮产物中的 `prompt_bundle/README.md` 明确说明了：

- 按 `check -> fix -> review` 的顺序交给外部宿主执行
- 如果宿主不支持 skill token，可删除 token 但保留正文指令
- validation 结果应结合依赖诊断一起解释

因此，prompt-bundle 的产物不仅是三份 prompt，而是一套可继续执行的宿主无关工件集合。

### 10.6 案例图示

![图 5. 一次真实 prompt-bundle 运行案例的过程与结果](./assets/memory-skill-suite-run-case.svg)

**图 5** 展示了该轮运行的输入、执行过程、validation 信号和输出结果。重点不在于本地目录结构，而在于流程与判断逻辑本身。

### 10.7 结论

该案例说明，系统已能够从“依赖宿主完整执行能力”过渡到“在宿主受限时仍能导出可继续推进的工程工件”。对于通用 skill 的设计而言，这一点比单次自动修复成功更重要。

---

## 11. 同步与部署

### 11.1 为什么需要同步

这里的“同步”主要针对 Codex 安装路径。

repo 内 skill 是开发源；全局 skill 库是 Codex 读取已安装 skill 的目录。如果没有同步机制，容易出现：

- repo 内已更新
- 全局 skill 库仍是旧版本
- 使用效果与源码状态不一致

对于非 Codex 宿主，不需要这一步。那类场景直接使用 `packages/memory_hotspot_repair_kernel/` 作为便携方法包即可。

### 11.2 同步脚本

Codex 安装路径使用的同步脚本为：

`packages/memory_hotspot_repair_kernel/scripts/sync_to_codex_home.py`

其职责是将以下四个 skill：

- `memory-check`
- `memory-fix`
- `memory-review`
- `memory-optimizer-agent`

同步到：

- `$CODEX_HOME/skills`
- 默认即 `~/.codex/skills`

并显式跳过：

- `runs/`
- `__pycache__`
- `.pyc`

### 11.3 分发视角下的理解

从分发角度看，应将这一步理解为“可选安装方式”，而不是“唯一使用方式”。

对于 Codex 用户：

- 可以将四个 skill 同步到 `$CODEX_HOME/skills`
- 默认路径通常是 `~/.codex/skills`
- 安装后可直接使用 `$memory-optimizer-agent`

对于非 Codex 用户：

- 不需要安装到全局 skill 库
- 直接使用 `packages/memory_hotspot_repair_kernel/`
- 重点阅读 `PORTABLE_USAGE.md` 与 `generic.prompt_bundle.yaml`

这表明当前仓库同时支持“Codex 安装式使用”和“非 Codex 便携工作流使用”两条路径。

---

## 12. 开发历程与问题总结

### 12.1 演进过程

该套件并非一次性设计完成，而是在多轮实际使用中逐步演进而来：

1. 从 `memory-check` 起步，用于识别内存热点
2. 扩展为 `check / fix / review` 三件套
3. 加入 `memory-optimizer-agent`，统一调度多轮流程
4. 暴露宿主耦合问题，明确 agent 的 host adapter 定位
5. 引入 overlay，分离通用知识与项目专有知识
6. 引入 `prompt-bundle` backend，降低 Codex 依赖
7. 补充 generic templates，支持迁移
8. 补充 validation portability 与 dependency diagnostics

### 12.2 已确认的典型问题

已明确出现过的问题包括：

- `codex.cmd` 在 Linux/WSL 下不兼容
- `approval_policy` 参数透传位置错误
- app-server / preflight 阻塞 full mode
- `python` 与 `python3` 行为不一致
- PowerShell 风格命令在 bash 下失效
- smoke 失败本质上是依赖缺失，而不是代码问题
- repo-specific 规则被错误地写入 core skill

这些问题的共同特征是：表面上看像功能问题，实质上是宿主耦合、环境耦合或执行兼容性问题。

---

## 13. 迁移方法

### 13.1 推荐迁移路径

如果要迁移到新项目，建议采用以下顺序：

1. 复制或下载整套 package 目录
2. 从 `generic.prompt_bundle.yaml` 起步
3. 先运行 `prompt-bundle` 模式
4. 检查 `check / fix / review` prompts 是否足以表达该 repo 的热点
5. 仅在必要时补充 overlay
6. 宿主稳定后，再尝试完整自动闭环

如果目标宿主是 Codex，也可以在上述基础上增加一步：

- 使用 `scripts/sync_to_codex_home.py` 执行全局安装

其优点包括：

- 迁移门槛低
- 宿主依赖少
- 先验证知识结构，再验证执行自动化

### 13.2 何时增加 overlay

适合增加 overlay 的情况包括：

- 某种热点模式在该 repo 中反复出现
- 某项行为契约较特殊，通用规则容易误伤
- 某些 validation 或 review hint 仅对该 repo 有意义

如果只是一次性局部问题，通常不值得立即建立 overlay。

### 13.3 如何一次性使用完整流程

如果不希望分别手动调用 `memory-check`、`memory-fix`、`memory-review` 和 orchestrator，更合理的入口是：

- 直接使用 `memory-optimizer-agent`

其职责本身就是一次性组织完整流程。

### 13.4 如何理解轮次

轮次需要分两层理解：

- 方法论层：默认最多 2 轮
- 配置层：可通过 `default_profile` 选择 `fast`、`default` 或 `aggressive`

因此，某个配置文件将默认 profile 指向 `fast`，只表示“当前默认执行 1 轮”，不表示整套方法论的默认上限已变为 1 轮。

### 13.5 全局安装说明

这一步只适用于 Codex 安装式使用。

同步完成后，全局路径通常为：

- `$CODEX_HOME/skills/`
- 未设置 `CODEX_HOME` 时，通常是 `~/.codex/skills/`

在当前 WSL / Linux 环境中，若实际用户为 `root`，则 `~` 可能对应 `/root/`。这属于当前环境的具体展开结果，不应被理解为所有机器上的固定路径。

![图 4. 新项目迁移这套 suite 的推荐路径](./assets/memory-skill-suite-migration.svg)

**图 4** 展示了推荐迁移路径：先从通用 prompt-bundle 起步，再逐步引入 overlay 和完整宿主自动化。

---

## 14. 当前状态与后续方向

### 14.1 已完成

目前已完成：

- core skill suite
- protocol layer
- pattern library
- overlay system
- prompt-bundle backend
- validation portability
- dependency diagnostics
- generic run / prompt-bundle templates
- generic overlay template
- global skill sync script
- Codex 安装路径与非 Codex 便携路径的分离
- 第一轮真实 prompt-bundle 运行验证

### 14.2 部分完成

- `codex` backend 在受限宿主环境下仍可能退化
- 跨项目输出一致性仍需要更多实测

### 14.3 尚未完成

- eval corpus
- 系统化 regression detection
- 跨项目稳定性验证矩阵
- 更完整的 artifact dashboard

### 14.4 适合写成 ADR 的决策点

后续值得单独沉淀为 ADR 的决策包括：

- 为什么将 `memory-optimizer-agent` 定位为 host adapter
- 为什么协议层优先于 prose 堆积
- 为什么 overlay 必须与 core 分离
- 为什么要引入 `prompt-bundle`
- 为什么 validation portability 是架构问题
- 为什么要补 dependency diagnostics
- 为什么要提供全局同步脚本

---

## 15. 术语表

### `memory hotspot`

指在执行过程中形成明显峰值内存压力的代码位置，严重时可直接导致 OOM。

### `materialization`

指惰性结果、流式结果或查询计划被真正拉入内存并转为具体对象的过程。

### `chunking`

指分块处理。真正的 chunking 发生在读取边界；假 chunking 常常是先全量读入，再在内存中切块。

### `validation`

指较小范围的运行检查，用于判断修改后路径是否仍具备基本可运行性。

### `protocol`

本文中的协议层指“将输出约束为稳定结构的规则层”，而非网络协议。

### `pattern library`

指按技术栈组织的经验模式集合。

### `overlay`

指仅对某个项目或某条 pipeline 有意义的局部经验层。

### `host adapter`

指负责处理宿主运行环境差异的适配层。

### `prompt bundle`

指一组可交给外部宿主继续执行的提示与说明文件集合。

### `bounded loop`

指带有轮次上限和停止条件的有限循环，而不是无限优化过程。

---

## 16. 参考资料

当前整理的关键参考资料包括：

- Python `tracemalloc` 文档  
  https://docs.python.org/3/library/tracemalloc.html

- pandas `Scaling to large datasets`  
  https://pandas.pydata.org/docs/user_guide/scale.html

- DuckDB `Out of Memory Errors`  
  https://duckdb.org/docs/stable/guides/troubleshooting/oom_errors.html

- DuckDB `Memory Management in DuckDB`  
  https://duckdb.org/2024/07/09/memory-management.html

- Polars `Streaming`  
  https://docs.pola.rs/user-guide/concepts/streaming/

这些资料主要用于支撑以下类型的通用规则：

- 为什么 blocking operator 易形成峰值
- 为什么 pandas 中间对象会放大内存压力
- 为什么流式执行与 eager collect 的差异重要
- 为什么 spill、temp directory、thread count 会影响 DuckDB 峰值行为

---

## 17. 结语

这套 memory hotspot skill suite 的核心价值，不在于“是否自动优化了某段代码”，而在于它将一类高度经验化的内存问题整理成了一套可复用、可迁移、可验证、可归档的工程结构。

从当前状态看，它已经完成了从单项目 prompt 到通用 skill suite 的转变。它既可以作为 Codex 中的可安装 skill 包使用，也可以作为更通用宿主环境中的便携 workflow 使用。后续仍可以继续补充评估语料、稳定性验证和更完整的可视化工件，但作为一套可分享、可迁移的工程方案，其基本形态已经成立。
