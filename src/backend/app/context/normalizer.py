import re
WS=re.compile(r'[ \t]+')
def normalize(text:str)->str:
 return '\n'.join(WS.sub(' ',x).strip() for x in (text or '').replace('\r\n','\n').split('\n') if x.strip())
def recent_window(text:str,max_chars:int)->str:
 t=normalize(text)
 if len(t)<=max_chars:return t
 s=t[-max_chars:]
 pos=[s.find(x) for x in ('。','！','？','\n') if s.find(x)>=0]
 return s[min(pos)+1:].strip() if pos else s
