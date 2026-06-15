# -*- coding: utf-8 -*-
"""오프라인 배포용 단일 HTML 번들 생성기.
사용:  python build_offline.py
산출:  통신회계_가이드_offline_YYYY-MM-DD.html
"""
import os, base64, io, sys, re, datetime

sys.stdout.reconfigure(encoding='utf-8')

# ───────────────── 1. 이미지 base64 dict ─────────────────
img_dict = {}
img_total_raw = 0
for f in sorted(os.listdir('img')):
    path = 'img/' + f
    if not os.path.isfile(path):
        continue
    ext = f.rsplit('.', 1)[-1].lower()
    mime = {
        'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'gif': 'image/gif', 'svg': 'image/svg+xml', 'webp': 'image/webp',
    }.get(ext, 'application/octet-stream')
    with open(path, 'rb') as fp:
        raw = fp.read()
    img_total_raw += len(raw)
    b64 = base64.b64encode(raw).decode('ascii')
    img_dict[f] = 'data:%s;base64,%s' % (mime, b64)

print('이미지 변환: %d개, raw %.1fKB' % (len(img_dict), img_total_raw / 1024))

# ───────────────── 2. data/*.js 합치기 + img 경로 치환 ─────────────────
data_files = sorted(f for f in os.listdir('data') if f.endswith('.js'))
data_blob_parts = []
for f in data_files:
    content = open('data/' + f, encoding='utf-8').read()
    # data/*.js 안의 본문에는 'img/xxx.png' 또는 src=\"img/xxx.png\" 형태
    for name, data_uri in img_dict.items():
        # JSON-encoded 본문이므로 따옴표 안에 들어있음. 단순 문자열 치환으로 안전.
        content = content.replace('img/' + name, data_uri)
    data_blob_parts.append('/* === %s === */\n%s' % (f, content))

data_blob = '\n'.join(data_blob_parts)
print('데이터 파일 인라인: %d개, 인라인 후 %.1fKB' % (len(data_files), len(data_blob) / 1024))

# ───────────────── 3. index.html 패치 ─────────────────
html = open('index.html', encoding='utf-8').read()

# (a) 동적 로딩 차단: filesToLoad.push 블록을 비활성화
dyn_pat = re.compile(
    r"const filesToLoad = \[\];\s*for \(const category in dataRegistry\) \{.*?\}\s*\)?\s*;?\s*\}",
    re.DOTALL,
)
m = dyn_pat.search(html)
if not m:
    # 더 단순한 패턴 시도
    dyn_pat2 = re.compile(
        r"const filesToLoad = \[\];[\s\S]*?filesToLoad\.push\([^)]*\)[\s\S]*?\}\s*\)[\s\S]*?\}",
        re.DOTALL,
    )
    m = dyn_pat2.search(html)

if m:
    html = html[:m.start()] + 'const filesToLoad = []; /* OFFLINE BUNDLE */' + html[m.end():]
    print('동적 로딩 블록 비활성화: OK')
else:
    print('!! 동적 로딩 블록을 찾지 못함. 수동 확인 필요.')

# (b) window.registerData 정의 직후에 인라인 데이터 삽입
anchor = 'window.registerData = function(dataArray) {\n            fullTableData.push(...dataArray);\n        }'
if anchor not in html:
    # 줄바꿈/공백 다른 변형 시도
    anchor = re.search(r'window\.registerData\s*=\s*function[\s\S]{0,200}fullTableData\.push[\s\S]{0,50}\}', html)
    if anchor:
        anchor = anchor.group(0)
    else:
        print('!! registerData 정의 위치를 찾지 못함')
        sys.exit(1)

inline_block = (
    '\n\n        /* ═══ OFFLINE INLINE DATA (auto-generated) ═══ */\n'
    + data_blob
    + '\n        /* ═══ END OFFLINE INLINE DATA ═══ */\n'
)
html = html.replace(anchor, anchor + inline_block, 1)

# (c) 오프라인 모드 표식 (HTML <head>에)
today = datetime.date.today().isoformat()
banner_comment = (
    '<!-- OFFLINE BUNDLE — 생성일: %s — '
    '데이터·이미지 전체 인라인됨. file:// 더블클릭 가능 -->\n' % today
)
html = html.replace('<head>', '<head>\n' + banner_comment, 1)

# (d) 풋터에 생성일 노트 (선택)
out_name = '통신회계_가이드_offline_%s.html' % today
open(out_name, 'w', encoding='utf-8').write(html)
out_size = os.path.getsize(out_name)
print('-' * 60)
print('산출 파일: %s' % out_name)
print('파일 크기: %.2f MB (%.0fKB)' % (out_size / 1024 / 1024, out_size / 1024))
