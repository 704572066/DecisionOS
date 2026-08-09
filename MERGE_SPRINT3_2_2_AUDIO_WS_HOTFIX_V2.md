# Sprint 3-2.2 AudioWS Hotfix v2

This version no longer depends on what comes after the segment assignment.

It only looks for:

```python
segment = append_result.segment
```

and inserts immediately after it:

```python
runtime_state_service.apply_transcript_event(
    meeting,
    text,
)
```

## Apply

```bash
python scripts/apply_sprint3_2_2_audio_ws_hotfix_v2.py
```

Then inspect:

```bash
git diff src/backend/app/api/audio_ws.py
```

If successful, rebuild backend.
