# 微信群记录总结 Skill

一个可复用的 Codex skill：读取本人已登录 Windows 微信的本地已同步群聊记录，由当前 Codex 会话读完消息后生成中文总结、离线网页和 PNG 长图。无需额外模型 API Key。

## 使用

将本仓库克隆或下载到个人技能目录 `~/.codex/skills/wechat-group-report`（Windows 通常位于用户目录下）。然后在支持加载该 skill 的 Codex 会话中调用：

> 使用 $wechat-group-report，读取“完整微信群名”最近 48 小时记录，生成网页版和 PNG 总结报告。

默认最近 24 小时，也支持 48/72 小时、带时区的指定起止时间。缺少群名会询问；重名群按稳定 ID 消歧，多个账号需要选择。完整流程见 [SKILL.md](SKILL.md)，安装依赖和脚本命令见 [运行说明](references/runtime.md)。

## 输出

每次独立目录包含 messages.json、messages.txt、report.json、summary.md、index.html、report.png；超长内容输出编号分图。网页无需启动服务，核心样式不依赖远程脚本或字体。重要结论带消息来源引用，默认折叠摘录。

独立执行 app.py 仅导出消息；总结由使用本 skill 的 Codex 会话完成，render.py 将消息与会话编写的 report.json 渲染为报告。没有独立自动总结模型服务。

## 已验证范围

- Windows 微信 4.1.15.13，Python 3.12，Microsoft Edge。
- 真实运行验证过联系人库、两个消息分片的 HMAC/SQLite 校验和指定群 24 小时导出。其他微信版本需要重新验证，不能保证通用兼容。
- 非空加密 WAL 的真实正向回放、多图超长真实聊天尚未完成实测。源码已校验 WAL 头、salt、滚动 checksum 并仅采用提交事务。
- 附带 6 项虚构数据测试，覆盖解析、输出转义、渲染、时间边界、异常清理与无效引用拒绝。虚构测试不代表真实读取兼容成功。
- 当前默认数据路径为 Documents/xwechat_files/*/db_storage，默认使用标准 Edge 安装路径。自定义路径需适配。

## 数据范围与边界

仅处理本人已登录账号的本地数据。原数据库只读，使用临时副本，密钥不写入日志或配置。底层解密完整必要分片，查询只取指定群和时间窗口。DB/WAL 连续字节比对是稳定性检查，并非跨分片全局事务快照保证。

仅本地已同步记录，不等于该群完整历史。未解析图片、视频、语音或表情内容。建议、决定、收到、同意和执行完成需要分别判断；缺少负责人和截止时间时保留“未明确”。不自动发布报告或发送给他人。

临时明文使用上下文与显式关闭连接清理；强制终止、断电或操作系统拒绝删除仍可能残留，运行后应核查本次临时目录。报告本身含群聊摘录，公开分享前自行核对内容。

## 开发验证

在已安装 requirements.txt 的 Python 环境中执行（请在临时工作目录运行，测试会创建 outputs/demo）：

```powershell
python -m unittest discover -s /absolute/path/to/wechat-group-report/scripts -p "test_*.py" -v
```

## 开源许可与来源

本项目采用 [Apache-2.0](LICENSE)。复用的 wechat-cli 固定源码提交及本地修改见 [NOTICE](NOTICE) 和 [来源说明](references/provenance.md)。本仓库不包含真实聊天导出、数据库、密钥或运行报告。与腾讯/微信无隶属关系。
