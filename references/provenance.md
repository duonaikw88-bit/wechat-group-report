# 来源与实测边界

复用来源：https://github.com/TheRaptors/wechat-cli ，固定提交 6770e1e0c0847e193fb3e3b22e4cd6b93de9aacc，Apache-2.0。完整许可证附于 scripts/vendor/LICENSE-wechat-cli。

附带 vendor 是该提交中所需 Python 模块的子集，包含 scanner_windows/common、crypto、messages/key_utils。scanner_windows 本地修改：屏蔽输出，修正 Windows 64 位 ctypes API 签名。app.py 在调用前将 save_results 替换为仅返回内存映射，限制扫描数据库集合。不要直接运行 vendor 中的扫描入口；上游 common.save_results 会写密钥。

Config.Cipher 指针结构与 XOR 掩码来自上述固定源码，不是本 skill 猜测；仅 HMAC 验证通过的候选密钥可用。上游 WAL 函数没有完整校验提交与 checksum，本地 app.py 自行实现，不调用它。

此前本机实测：Windows 微信 4.1.15.13，Python 3.12，Edge；contact.db 与两个 message_N.db 校验通过，指定群完整名唯一匹配，24 小时窗口读出两条本地消息。有效提交 WAL 帧数为 0，真实非空 WAL 回放未验证，长报告多图路径此前未以真实长群聊验证。虚构数据测试不能证明真实微信读取成功。升级客户端后重新检查来源、版本和 schema。

曾在初版未关闭 SQLite 连接时留下临时明文联系人库；附带代码已使用 contextlib.closing，但运行后仍须检查本次清理。不要复制原项目 outputs、真实 messages.json、密钥、账号目录或历史临时明文库进 skill。
