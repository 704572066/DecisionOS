from pathlib import Path


def insert(path, marker, code):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if code.strip() in text:
        print('already:', path)
        return
    if marker not in text:
        raise RuntimeError(f'marker not found: {path}')
    p.write_text(text.replace(marker, marker + '\n' + code), encoding='utf-8')
    print('patched:', path)

root = Path('.')

insert(
 'src/backend/app/decision_board/models.py',
 'class DecisionBoard(BaseModel):',
 '    signals: list[dict] = Field(default_factory=list)\n'
)

insert(
 'src/backend/app/decision_board/engine.py',
 'class DecisionBoardEngine:',
 '    # Sprint 3-3.1 Decision Signal Runtime\n'
)

insert(
 'src/frontend/src/main.tsx',
 '  recentEvents: Array<{eventId:string;type:string;',
 '  signals: Array<{level:string;type:string;title:string;message:string}>;'
)

print('Sprint 3-3.1 patch complete')
