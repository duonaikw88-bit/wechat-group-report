# report.json

UTF-8 JSON，和 messages.json 放在同一个运行目录。overview 是中文简短概览；每个数组为空表示未发现明确记录。不要填充虚构事项。示例里的 ID 必须换成实际导出的 ID。

```json
{
  "overview": "概览，重要观点的详细依据见下列条目。",
  "topics": [{"text": "话题及明确结论或尚无结论", "refs": ["实际消息ID"]}],
  "todos": [{"text": "事项", "owner": "未明确", "deadline": "未明确", "status": "建议/已决定/进行中/已完成/未明确，按原文证据填写", "refs": ["实际消息ID"]}],
  "confirmed": [],
  "unresolved": [],
  "other": []
}
```

topics、confirmed、unresolved、other 的条目统一为 text + 非空 refs 数组。todos 额外含 owner、deadline、status。overview 不放独立无依据结论，应由有引用的条目支撑。不得把“收到”写成同意，把同意写成完成，或替他人确定负责人/截止时间。

messages.json 包含 metadata 和 messages。metadata 保存 group、group_id、account、start、end、timezone、interval、count、speakers、system_count、duplicates_removed、databases（含每库 WAL 帧数）、scope。messages 保存 id、local_id、server_id、timestamp（秒）、time（带时区）、sender_id、sender、raw_content、database、type、text、card、quote。系统消息不计入 speakers。昵称来自联系人映射，未保证群内专属备注。分享网页默认折叠引用，但文件本身包含引用摘录，交付前注意这属于聊天数据。

每次总结可在 report.json 附加 reading 字段记录 messages_sha256、pages_read、total_pages 和 summarizer='current Codex session'，帮助追溯是否读完同一份导出；它是过程记录，不是自动语义验证证明。
