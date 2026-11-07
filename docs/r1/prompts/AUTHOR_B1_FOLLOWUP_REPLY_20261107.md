# Author follow-up replies — 7 November 2026

The author replied in this conversation to the C3 temporary-root cleanup and B1 STATUS publication questions:

> 允许，但仅限这一类：C3 脚本在本次运行中自己用 mkdtemp 创建的临时根目录，满足以下全部条件：
> 1. 位于测试专用 TMPDIR 之下，前缀是 r1_c3_dryrun_ / r1_c3_smoke_ 这类合成运行前缀，并带有 .dryrun 标记文件；
> 2. 删除前，脚本已把 *.log、*.json* 和 fake_calls.jsonl 复制到输出目录，summary.json 里有记录；
> 3. 删除记录写进你的报告：路径、大小、对应的输出目录。
> 不满足上述任一条件的目录，用 --keep 重跑或保留原样，报告给我。正式实验输出、标签、审计、远端文件、仓库内文件仍禁止删除；仓库内要删的东西照旧移到 _to_delete/。

Asked whether this B1 may push STATUS to `mac-b1-20261107` and use the TASL-7 marker as Track P's authoritative signal, while retaining handover, no-preemption, and other launch conditions, the author replied:

> 允许此次采用功能分支 STATUS（建议）
