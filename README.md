# UVQA Viewer

Run the local dataset viewer:

```bash
cd /mnt/u14157_ic_nlp_001_files_nfs/nlpdata1/home/mamooler/video_reasoning/unanswerable_videoqa
python website/server.py --host 127.0.0.1 --port 8008
```

Then open `http://127.0.0.1:8008`.

The server indexes `generated_data/*/{video,audio}/gemini_results.jsonl` and resolves
local media files for playback.
