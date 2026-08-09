# Sprint 3-2.2 audio_ws Hotfix

The original 3-2.2 patch expected an outdated marker in `audio_ws.py`.

This hotfix targets the current structure:

```python
append_result = append_final_segment(...)
segment = append_result.segment
await send_json_safe(...)
```

It inserts:

```python
runtime_state_service.apply_transcript_event(
    meeting,
    text,
)
```

immediately after the persisted segment is available.

## Apply

```bash
python scripts/apply_sprint3_2_2_audio_ws_hotfix.py
```

Then:

```bash
git diff src/backend/app/api/audio_ws.py
```

Expected changes:

1. import `runtime_state_service`
2. call `apply_transcript_event(meeting, text)` after `segment = append_result.segment`

Then continue with the Sprint 3-2.2 merge/deploy steps.
