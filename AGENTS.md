# Alamo Skill Hub Agent Guide

## 定位

本文件是 `alamo_skillhub` 仓库的 Agent 行事规范。

它回答的问题是：

> 当任务进入这个仓库时，应该如何理解仓库结构、如何区分可安装包与示例、如何更新 skill 文档与安装路径。

它不是项目进度日志，也不是某个 skill 的正文说明。

## 作用范围

- 适用于 `alamo_skillhub/` 下的后续 session
- 适用于 skill 设计、skill 打包、portable workflow 说明、Codex 安装说明、示例适配
- 作为 repo 根目录规范长期保留

## 仓库目标

这个仓库不是单个业务项目，而是一个 skill hub。

默认应这样理解：

- `packages/`：产品面，放可安装或可复用的 skill package
- `examples/`：示例面，放 repo-specific overlays、运行示例和适配参考

不要把 `examples/` 当成产品主入口。

## Session 启动顺序

每个新 session 建议按以下顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md`
4. 目标 package 下的主 skill 文档
5. 必要时再读 `examples/`

如果任务明确是 memory skill suite，推荐继续读：

1. `packages/memory_hotspot_repair_kernel/memory-optimizer-agent/SKILL.md`
2. `packages/memory_hotspot_repair_kernel/memory-check/SKILL.md`
3. `packages/memory_hotspot_repair_kernel/memory-fix/SKILL.md`
4. `packages/memory_hotspot_repair_kernel/memory-review/SKILL.md`

## 工作原则

1. 先判断任务是在改 package 核心，还是在改 example 适配。
2. 优先保持 package-core 与 host-specific/example-specific 内容分离。
3. 能写在 package 里的通用规则，不要写死在示例里。
4. 能写在 `references/` 的可复用方法论，不要埋在 chat 或临时说明里。
5. 安装路径、同步方法、Codex 用法与非 Codex 用法要明确区分。

## 仓库结构规则

### `packages/`

这里是产品主面。

适合放：

- `SKILL.md`
- `references/`
- 通用脚本
- 可安装同步脚本
- host-neutral prompt bundle

这里不应默认依赖某一个具体业务仓库。

### `examples/`

这里是可选参考面。

适合放：

- 某个具体 repo 的 overlays
- 示例 run config
- 示例 prompt bundle
- 演示用目录结构

这里不应该反向成为 package 的唯一真实入口。

## 文档更新规则

1. 仓库级使用说明更新到 `README.md`。
2. 非 Codex 的可移植用法更新到 `PORTABLE_USAGE.md`。
3. 某个 skill 的方法论和输出契约更新到对应 `SKILL.md` 与 `references/`。
4. 安装或同步方式变化时，更新脚本说明与 README。
5. 如果仓库定位、消费方式或结构规则变化，再更新本文件。

## 安装与同步规则

如果任务涉及 Codex 安装：

- 优先使用 package 自带同步脚本
- 不要手工复制文件后只在 chat 里说明
- 安装说明要明确：
  - 安装到哪里
  - 是否覆盖已有 skill
  - 是否依赖 `CODEX_HOME`

如果任务涉及非 Codex 复用：

- 优先更新 `PORTABLE_USAGE.md`
- 保持对 skill token 语法、host wiring、portable core 的边界说明清楚

## 设计规则

新增 skill 或新增 package 时，默认遵守：

1. core workflow 与 host adapter 分离
2. 可复用规则放 package，不放 example
3. 入口点明确，最好有推荐主入口 skill
4. Codex 使用方式与 portable 使用方式分别说明
5. 如果需要安装，给出脚本化安装路径

## 不要做的事

1. 不把 `examples/` 写成唯一产品说明。
2. 不把 repo-local 临时说明替代 `SKILL.md` 或 `references/`。
3. 不把只适用于某个业务仓库的规则误写进 package 核心。
4. 不把 Codex 专用语法误当成 portable core 的一部分。
5. 不在没有必要时把 package 设计成依赖 chat 上下文才能使用。

## 一句话

> `alamo_skillhub` 负责“把 skill 做成可安装、可复用、可迁移的包”，`packages/` 是产品面，`examples/` 是可选适配面，Agent 进入本仓库后应先守住这条边界。
