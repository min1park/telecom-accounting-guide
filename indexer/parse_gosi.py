# -*- coding: utf-8 -*-
"""회계분리기준 고시(제2025-23호) PDF → 조문별 entries (data/rule_2025.js)"""
import pdfplumber, re, io, os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, 'data', '[고시]전기통신사업 회계분리기준(과학기술정보통신부고시)(제2025-23호).pdf')

full = ''
with pdfplumber.open(PDF) as pdf:
    for p in pdf.pages:
        t = p.extract_text() or ''
        # 페이지 푸터 제거
        t = re.sub(r'법제처\s+\d+\s+국가법령정보센터', '', t)
        full += t + '\n'

# 헤더(고시명 반복) 제거
full = re.sub(r'전기통신사업 회계분리기준\n?\[시행[^\]]*\][^\n]*\n?', '', full)

# 조문 분리: "제N조(제목)" 또는 "제N조의M(제목)"
pat = re.compile(r'(제\d+조(?:의\d+)?\([^)]+\))')
parts = pat.split(full)
# parts: [전문, 헤더1, 본문1, 헤더2, 본문2, ...]
entries = []
for i in range(1, len(parts), 2):
    header = parts[i].strip()
    body = parts[i + 1].strip() if i + 1 < len(parts) else ''
    # 부칙 이후 잘라내기
    m = re.search(r'\n부\s*칙', body)
    if m:
        body = body[:m.start()].strip()
    body = re.sub(r'\n{3,}', '\n\n', body)
    entries.append({
        'id': '',
        'category': '회계분리기준 고시(조문)',
        'year': '2025',
        'title': header,
        'content': header + '\n' + body,
        'source_company': None,
        'source_category': '과학기술정보통신부고시 제2025-23호',
        'related_tags': [],
    })

print('파싱된 조문: %d개' % len(entries))
for e in entries[:5]:
    print(' ', e['title'], '| 본문', len(e['content']), '자')
print('  ...')
for e in entries[-3:]:
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
          '        "related_tags": []',
          '    }' + comma]
L.append(']);')
out = os.path.join(ROOT, 'data', 'rule_2025.js')
io.open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('저장:', out)
