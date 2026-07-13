# -*- coding: utf-8 -*-
"""
가이드라인 지식베이스 인덱서 (Phase 1)

data/*.js 52개 entry를 순회하며 자산·기능·역무·수익·비용 태그를 자동 추출하여
guideline_index.json 생성.

사용:  python indexer/build_guideline_index.py
"""
import json, io, os, sys, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
TERMS_PATH = os.path.join(ROOT, 'indexer', 'standard_terms.json')
OUT_PATH = os.path.join(ROOT, 'indexer', 'guideline_index.json')

# ────────────── 표준 용어 사전 로드 ──────────────
with io.open(TERMS_PATH, encoding='utf-8') as fp:
    TERMS = json.load(fp)

# category별 alias → (표준용어, code) 매핑 만들기 (긴 alias 우선)
def build_alias_map(cat_dict):
    m = []
    for std_name, entry in cat_dict.items():
        if std_name.startswith('_'):
            continue
        code = entry.get('code', '')
        for alias in entry.get('aliases', []):
            m.append((alias, std_name, code))
    # 긴 alias 먼저 매칭 (부분매칭 오탐 줄이기)
    m.sort(key=lambda x: -len(x[0]))
    return m

ALIAS_MAPS = {
    cat: build_alias_map(TERMS[cat])
    for cat in ['asset', 'function', 'service', 'revenue', 'cost']
}

# ────────────── 태그 추출 ──────────────
def extract_tags(text):
    """text에서 각 카테고리 태그 (표준용어명 + 코드 + 발견 횟수) 추출"""
    result = {}
    for cat, alias_map in ALIAS_MAPS.items():
        hits = defaultdict(int)
        for alias, std, code in alias_map:
            cnt = text.count(alias)
            if cnt > 0:
                hits[(std, code)] += cnt
        # 빈도 내림차순으로 정렬
        result[cat] = [
            {"term": std, "code": code, "count": cnt}
            for (std, code), cnt in sorted(hits.items(), key=lambda x: -x[1])
        ]
    return result

# ────────────── 결정 유형 자동 분류 ──────────────
DECISION_KEYWORDS = {
    '분류': ['역무분류','기능분류','서비스분류','역무별 분류','기능별 분류','기능·서비스 분류','오분류'],
    '배부': ['배부','배부기준','안분','할당','대응','배분'],
    '인식': ['인식','수익 인식','비용 인식','손익 인식','회계처리'],
    '원가': ['원가','원가 인정','원가로 인정','통신원가','전기통신사업 원가'],
    '검증/지적': ['지적','과징금','시정명령','위반','오류','오기입'],
    '범위': ['범위','포함','제외','대상 여부','포함 여부','제외 여부'],
}

def classify_decision(text):
    scores = {}
    for typ, kws in DECISION_KEYWORDS.items():
        s = sum(text.count(k) for k in kws)
        if s > 0:
            scores[typ] = s
    if not scores:
        return []
    return [t for t, _ in sorted(scores.items(), key=lambda x: -x[1])][:3]

# ────────────── 결론(☞) 추출 ──────────────
def extract_conclusion(text):
    """☞ 이후 문장을 결론으로 추출 (첫 200자)"""
    conclusions = []
    for line in text.split('\n'):
        if '☞' in line:
            idx = line.index('☞')
            c = line[idx:].strip()
            conclusions.append(c[:200])
    return conclusions

# ────────────── 원본 PDF 라벨 (index.html getSourceLabel과 동일 로직) ──────────────
# 내용 검증 기반 매핑(2026-07): 각 항목의 본문을 in-project PDF 전문과 대조하여
# 실제 수록 위치를 확정. '수록 위치 + 원 안건 출처' 형식. 헤더가 아닌 내용으로 검증.
_GF = {  # in-project 가이드라인 실제 파일명
    '2017.12': '[가이드라인]2017.12_영업보고서_작성_참고자료.pdf',
    '2018.03': '[가이드라인]2018.03_영업보고서_작성_참고자료.pdf',
    '2020.04': '[가이드라인]2020.04_영업보고서_작성_참고자료.pdf',
    '2021.05': '[가이드라인]2021.05_영업보고서_작성_참고자료.pdf',
    '2022.04': '[가이드라인]2022.04_영업보고서_작성_참고자료.pdf',
    '2023.04': '[가이드라인]2023.04_영업보고서_작성_참고자료.pdf',
}
_HS = '[해설서]2026_회계분리기준_해설서(2026.4.).pdf'
# (category, FY) → 수록 가이드라인 버전키 ('해설서'=해설서 2026.04)  [내용 검증 완료]
_COMMITTEE = {'2012':'2017.12','2013':'2017.12','2014':'2017.12','2015':'2017.12',
              '2016':'2017.12','2017':'2018.03','2018':'2020.04','2019':'2021.05',
              '2020':'2022.04','2021':'2023.04','2022':'해설서','2023':'해설서','2024':'해설서'}
_QNA = {'2011':'해설서','2012':'2017.12','2013':'2017.12','2014':'2017.12','2015':'2017.12',
        '2016':'2017.12','2017':'2018.03','2018':'2018.03','2019':'2020.04','2020':'2021.05',
        '2021':'2022.04','2022':'2023.04','2023':'해설서','2024':'해설서'}
_ONEFILE = {'2014':'2017.12','2016':'2017.12','2018':'2020.04','2019':'2021.05',
            '2020':'2022.04','2021':'2023.04','2022':'해설서'}

def _pub(ver, y, section):
    base = _HS if ver == '해설서' else _GF.get(ver)
    if not base:
        return None
    return '%s 수록 — FY%s %s' % (base, y, section)

def get_source_pdf(category, year, source_company):
    y = str(year) if year else ''
    co = source_company or ''
    # 고시 원문
    if '고시' in category:
        return '[고시]전기통신사업 회계분리기준(과학기술정보통신부고시)(제2025-23호).pdf'
    # 지적사항 — 해설서 2026.04에 전 연도(고시 조문별) 수록
    if '영업보고서 검증' in category or '지적사항' in category:
        return '%s 수록 — FY%s 영업보고서 검증결과 지적사항 (조문별)' % (_HS, y)
    # 회계전문위원회 회의 결과
    if '회계전문위원회' in category:
        lbl = _pub(_COMMITTEE.get(y), y, '회계전문위원회 회의 결과')
        return lbl or '[자문단] FY%s 회계전문위원회 회의 결과 (프로젝트 외 원본)' % y
    # 회계처리 일원화 방안
    if '회계처리 일원화' in category:
        lbl = _pub(_ONEFILE.get(y), y, '회계처리 일원화 방안')
        return lbl or '[자문단] FY%s 회계처리 일원화 방안 (프로젝트 외 원본)' % y
    # 질의 회신
    if '질의' in category:
        if y == '2020' and co == 'SK브로드밴드':
            return '[사전질의]2020회계연도전기통신사업회계제도질의답변서_SK브로드밴드(배포용).pdf (프로젝트 외 원본)'
        if y == '2025' and co:
            return '[질의회신]2025회계연도 전기통신사업 회계제도 질의 답변서_%s.pdf (프로젝트 외 원본)' % co
        lbl = _pub(_QNA.get(y), y, '질의회신')
        if lbl:
            return lbl
        co_lbl = (' _' + co) if co else ''
        return '[질의회신] FY%s%s (프로젝트 외 원본, 출처 미상)' % (y, co_lbl)
    # 작성 주의사항 / 참고자료 — 해당 연도 가이드라인
    guide_ver = {'2016':'2017.12','2017':'2018.03','2019':'2020.04',
                 '2020':'2021.05','2021':'2022.04','2022':'2023.04'}.get(y)
    if '영업보고서 작성 주의' in category:
        return (_pub(guide_ver, y, '작성 주의사항')) or '[가이드라인] FY%s 작성 주의사항 (출처 확인 필요)' % y
    if '참고자료' in category:
        return (_pub(guide_ver, y, '참고자료')) or '[가이드라인] FY%s 참고자료 (출처 확인 필요)' % y
    if '해설서' in category:
        return _HS
    return ''

# ────────────── 메인 인덱싱 ──────────────
index = []
stats = {'total': 0, 'with_asset': 0, 'with_function': 0, 'with_service': 0,
         'with_revenue': 0, 'with_cost': 0, 'with_any': 0, 'no_tag': 0}

data_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.js'))
for fname in data_files:
    src = os.path.join(DATA_DIR, fname)
    t = io.open(src, encoding='utf-8').read()
    try:
        arr = json.loads('[' + t.split('[', 1)[1].rsplit(']', 1)[0] + ']')
    except Exception as ex:
        print('SKIP (parse fail):', fname, ex)
        continue

    for idx, e in enumerate(arr):
        title = e.get('title', '')
        content = e.get('content', '')
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        text = title + '\n' + content

        tags = extract_tags(text)
        stats['total'] += 1
        for cat in ['asset', 'function', 'service', 'revenue', 'cost']:
            if tags[cat]:
                stats['with_' + cat] += 1
        any_tag = any(tags[c] for c in ['asset', 'function', 'service', 'revenue', 'cost'])
        if any_tag:
            stats['with_any'] += 1
        else:
            stats['no_tag'] += 1

        idx_entry = {
            "id": "%s#%d" % (fname.replace('.js', ''), idx),
            "source_file": fname,
            "index_in_file": idx,
            "title": title,
            "category": e.get('category', ''),
            "year": str(e.get('year', '')),
            "source_company": e.get('source_company'),
            # entry에 전수 감사로 확정한 source_pdf가 있으면 그것을 사용, 없으면 그룹 매핑 폴백
            "source_pdf": e.get('source_pdf') or get_source_pdf(e.get('category', ''), e.get('year', ''), e.get('source_company', '')),
            "tags": tags,
            "decision_types": classify_decision(text),
            "conclusions": extract_conclusion(content),
            "excerpt": re.sub(r'\s+', ' ', content)[:300],
            "content_length": len(content),
        }
        index.append(idx_entry)

# ────────────── 저장 ──────────────
with io.open(OUT_PATH, 'w', encoding='utf-8') as fp:
    json.dump({
        "_meta": {
            "version": "0.1",
            "total_entries": len(index),
            "stats": stats,
            "categories": ['asset', 'function', 'service', 'revenue', 'cost'],
        },
        "entries": index,
    }, fp, ensure_ascii=False, indent=1)

# ────────────── 리포트 ──────────────
print('─' * 60)
print('인덱싱 완료: %d entries' % stats['total'])
print('─' * 60)
for cat in ['asset', 'function', 'service', 'revenue', 'cost']:
    v = stats['with_' + cat]
    print('  %s 태그 보유: %3d entries (%.0f%%)' % (cat, v, v * 100 / stats['total']))
print('  ─── 최소 1개 태그: %d, 완전 무태그: %d' % (stats['with_any'], stats['no_tag']))
print('─' * 60)
print('산출: %s (%.1f KB)' % (OUT_PATH, os.path.getsize(OUT_PATH) / 1024))
