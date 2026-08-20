<div align="center">

![logo](https://proxy.mooncc.cn/https://raw.githubusercontent.com/MoonCC233/astrbot_plugin_dailycheck/main/logo.png)

# astrbot_plugin_dailycheck（每日抽签）

</div>

将 `astrbot_plugin_jrrp`（今日人品）与 `astrbot_plugin_jrys`（今日运势）合并为单一插件，保留两插件全部核心功能，统一命令注册，整合配置项，避免命令冲突。

## 插件结构

```
astrbot_plugin_dailycheck/
├── main.py              # 统一 Star 类，注册全部命令，整合 jrrp + jrys 逻辑
├── painter.py           # 今日运势卡片图片生成（来自 jrys）
├── _conf_schema.json    # 整合后的配置项 Schema
├── metadata.yaml        # 插件元信息
├── requirements.txt     # 依赖：Pillow, requests
├── jrys.json            # 运势文案数据（来自 jrys）
├── font/                # 卡片字体（MiSans-Medium.ttf）
└── backgroundFolder/    # 运势卡片背景图
```

## 命令列表

| 命令 | 功能 | 来源 |
|------|------|------|
| `/jrrp` | 获取今日人品值（0-100，按用户+日期固定，每天一次） | jrrp |
| `/jrys` | 生成今日运势卡片（图片或文本） | jrys |
| `/今日运势` | `/jrys` 的中文别名 | jrys |
| `/运势` | `/jrys` 的中文别名 | jrys |
| `/jrys_last` | 发送上次生成的运势卡片 | jrys |

> 命令无冲突：`jrrp` 与 `jrys` 系列互不相同；中文别名 `今日运势`/`运势` 通过 `@filter.command("jrys", alias=["今日运势", "运势"])` 一致映射，避免重复注册。

额外行为：私聊中发送包含「今日运势」或「运势」的消息，可在开启 `auto_trigger` 后自动触发运势卡片（仅私聊）。

## 配置说明

配置文件位于 AstrBot 后台插件配置页，对应 `_conf_schema.json`：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `send_image` | bool | `true` | 运势以图片卡片发送；关闭则发送纯文本运势信息 |
| `use_avatar` | bool | `false` | 在运势卡片上绘制用户头像（依赖 `requests` 库且需平台支持获取头像） |
| `auto_trigger` | bool | `false` | 私聊中发送含「今日运势」或「运势」的消息时自动触发运势卡片 |

也可直接在 `_conf_schema.json` 同级目录修改用户配置（JSON 示例）：

```json
{
  "send_image": true,
  "use_avatar": false,
  "auto_trigger": false
}
```

## 安装

1. 将本插件目录 `astrbot_plugin_dailycheck/` 整体放入 AstrBot 的 `plugins/` 目录（与 `_conf_schema.json` 同级）。
2. 安装依赖（首次启用时 AstrBot 通常会自动安装，也可手动执行）：

   ```bash
   pip install -r requirements.txt
   ```

3. 在 AstrBot 后台「插件管理」中启用插件并重启 / 重载。

> 本插件由原 `astrbot_plugin_jrrp`（今日人品）与 `astrbot_plugin_jrys`（今日运势）合并而来。`jrrp` 原无配置项、无外部资源依赖；`jrys` 的 `jrys.json`、字体、背景图已一并迁移至本插件目录。

## 使用示例

- 查询人品：

  ```
  用户：/jrrp
  机器人：你今天的人品值为：87
  ```

- 查询运势（以下任一命令等价）：

  ```
  /jrys
  /今日运势
  /运势
  ```

  默认返回一张运势卡片图片（含星级、幸运方位/颜色/数字/禁忌），若关闭 `send_image` 则返回纯文本。

- 查看上次卡片：

  ```
  /jrys_last
  ```

## 常见问题（FAQ）

- **运势卡片生成失败 / 背景图缺失？** 确认 `backgroundFolder/` 与 `font/MiSans-Medium.ttf` 已随插件一并部署，且 `Pillow` 已正确安装。
- **头像不显示？** 开启 `use_avatar` 后，需平台事件能提供头像 URL 且 `requests` 依赖可用；部分平台不支持获取头像时会自动跳过。
- **想新增运势文案？** 编辑 `jrys.json`，每条为包含 `star`、`title`、`text`、`lucky`、`lucky_color`、`lucky_num`、`avoid` 字段的对象，随机抽取其一。
- **命令被旧插件重复注册？** 合并后请停用 / 删除原 `astrbot_plugin_jrrp` 与 `astrbot_plugin_jrys`，避免双插件冲突。

## 目录结构总览

```
astrbot_plugin_dailycheck/
├── main.py              # 统一 Star 类，注册全部命令，整合 jrrp + jrys 逻辑
├── painter.py           # 今日运势卡片图片生成（来自 jrys）
├── _conf_schema.json    # 整合后的配置项 Schema
├── metadata.yaml        # 插件元信息
├── requirements.txt     # 依赖：Pillow, requests
├── jrys.json            # 运势文案数据（来自 jrys）
├── logo.png             # 插件图标（透明背景）
├── font/                # 卡片字体（MiSans-Medium.ttf）
└── backgroundFolder/    # 运势卡片背景图
```
