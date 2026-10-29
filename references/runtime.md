# 运行与命令

令 SKILL 为本 SKILL.md 的父目录。使用实际绝对路径替换命令占位符；PowerShell 路径带空格需引号和调用运算符 &。

优先用工作项目已有兼容 Python 环境。缺少 Python 时调用 load_workspace_dependencies 获取 Codex bundled Python，不依赖 Windows Store 的 python 别名。推荐在当前工作目录的 .wechat-report-venv 创建 venv，避免给技能目录写输出或私密数据。

```powershell
& "Python绝对路径" -m venv "工作目录/.wechat-report-venv"
& "工作目录/.wechat-report-venv/Scripts/python.exe" -m pip install -r "SKILL/scripts/requirements.txt"
$env:PYTHONUTF8='1'
# 工作目录可另选空的测试目录；测试将创建 outputs/demo（仅虚构数据）
& "工作目录/.wechat-report-venv/Scripts/python.exe" -m unittest discover -s "SKILL/scripts" -p "test_*.py" -v
& "工作目录/.wechat-report-venv/Scripts/python.exe" "SKILL/scripts/app.py" --group "完整群名" --hours 24 --output-root "工作目录/wechat-reports"
& "工作目录/.wechat-report-venv/Scripts/python.exe" "SKILL/scripts/read_messages.py" "本次目录/messages.json"
& "工作目录/.wechat-report-venv/Scripts/python.exe" "SKILL/scripts/read_messages.py" "本次目录/messages.json" --page 1
# 会话读完所有页，写 report.json 后：
& "工作目录/.wechat-report-venv/Scripts/python.exe" "SKILL/scripts/render.py" "本次目录"
```

导出可选参数：--hours 48 / 72；--start '2026-10-28T10:00:00+08:00' --end '2026-10-29T10:00:00+08:00'；--account 为账号目录名；--group-id 为稳定 chatroom ID。不传 --end 时运行开始固定截止时间；不要在总结中再次计算“现在”。

数据目录当前自动检测 Documents/xwechat_files/*/db_storage。自定义盘路径或重定向 Documents 尚无参数支持，应检查实际路径并适配副本中的路径发现逻辑，不假称已支持。默认渲染器使用 C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe；本机路径不同则核实已安装 Chromium/Edge 后调整脚本副本。HTML 不依赖外部 CDN，PNG 使用本机微软雅黑。分图阈值 12000 CSS 像素。

密钥缺失：确认微信已登录、目标群已打开，再重新读取。字段或页验证失败停止并重新研究。快照持续变化可稍后重试。不要为获取密钥关闭保护、注入进程或使用未经核实偏移。
