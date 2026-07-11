# -*- coding: utf-8 -*-
"""회계분리기준 고시(제2025-23호) → 조문별 entries (data/rule_2025.js)

원문 소스: indexer/gosi_2025_source.txt
  = 고시 .doc(제2025-23호, 20250526) Word 문단 단위 추출본.
  Word가 조/항/호/목 논리 단위로 문단을 나누므로 PDF 물리적 줄바꿈(문장중간 분절)이 없음.
  (과거: data/[고시]...pdf를 pdfplumber로 추출 → '상\\n각누계액','서비\\n스' 등 분절 발생하여 폐기)
갱신 시: G:\\...\\통신회계\\...(제2025-23호)(20250526).doc 를 Word COM으로 재추출하여 원문 갱신.
"""
import io, os, re, json, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'indexer', 'gosi_2025_source.txt')

full = io.open(SRC, encoding='utf-8').read()
m0 = re.search(r'제1조\(목적\)', full)
if m0:
    full = full[m0.start():]

pat = re.compile(r'(제\d+조(?:의\d+)?\([^)]+\))')
CHAP = re.compile(r'^\s*제\d+장\b')                  # 장 헤더(조 사이 삽입) → 본문 아님
CUT = re.compile(r'^\s*(부칙|별지|\[별지|별표|\[별표)')  # 이후는 조문 본문 아님

def clean_body(body):
    out = []
    for ln in body.split('\n'):
        s = ln.rstrip()
        if CUT.match(s):
            break
        if CHAP.match(s):
            continue
        out.append(s)
    txt = '\n'.join(out).strip()
    return re.sub(r'\n{2,}', '\n', txt)

parts = pat.split(full)
entries = []
for i in range(1, len(parts), 2):
    header = parts[i].strip()
    body = clean_body(parts[i + 1] if i + 1 < len(parts) else '')
    entries.append({
        'id': '', 'category': '회계분리기준 고시(조문)', 'year': '2025',
        'title': header, 'content': header + '\n' + body,
        'source_company': None, 'source_category': '과학기술정보통신부고시 제2025-23호',
        'related_tags': [],
    })

print('파싱된 조문: %d개' % len(entries))
for e in entries[:3] + entries[-2:]:
    print(' ', e['title'], '| 본문', len(e['content']), '자')

def jstr(s): return json.dumps(s, ensure_ascii=False)
L = ['window.registerData([']
for i, e in enumerate(entries):
    comma = ',' if i < len(entries) - 1 else ''
    L += ['    {', '        "id": ' + jstr(e['id']) + ',',
          '        "category": ' + jstr(e['category']) + ',',
          '        "year": ' + jstr(e['year']) + ',',
          '        "title": ' + jstr(e['title']) + ',',
          '        "content": ' + jstr(e['content']) + ',',
          '        "source_company": ' + jstr(e['source_company']) + ',',
          '        "source_category": ' + jstr(e['source_category']) + ',',
          '        "related_tags": []', '    }' + comma]
L.append(']);')
out = os.path.join(ROOT, 'data', 'rule_2025.js')
io.open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('저장:', out)
