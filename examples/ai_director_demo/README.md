# AI Director Phase 2 demo

This demo accepts only a topic and a source-linked factual brief. It does not
contain a hand-authored Storyboard. The brief is metadata and claims only; the
source documents are not copied into the repository.

```powershell
$PinkPigPython = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
& $PinkPigPython generate_video.py `
  --topic-file examples/ai_director_demo/topic.txt `
  --factual-brief examples/ai_director_demo/factual_brief.json `
  --director-provider codex-cli `
  --output-name pink_pig_modbus_ai_demo.mp4
```

The two cited sources are first-party Modbus Organization specifications. The
final media is still subject to the local quality report and human factual
review policy.
