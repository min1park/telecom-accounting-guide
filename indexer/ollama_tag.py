# -*- coding: utf-8 -*-
"""수익원장 그룹별 적요 실질 태깅 — Ollama 로컬 LLM 브릿지 v0.1

용법:
  python indexer/ollama_tag.py <원장.csv> [--model qwen3:8b] [--limit 50]

동작:
  1. 원장을 계정×형태×역무 그룹으로 요약 (적요·거래처 top-3 포함)
  2. 각 그룹을 Ollama에 보내 실질 태그 + 형태 적정성 초안 판정
  3. 산출: <원장>_ollama태깅.csv

주의: 판정 '초안'임 — 최종 판정은 검증인(CPA) 확인 필요.
"""
import csv, io, os, sys, json, argparse, time
import urllib.request
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = 'http://localhost:11434/api/generate'

# ── 이번 검토(FY2025 수익원장)에서 확립된 판정 지식 내장 ──
SYSTEM_KNOWLEDGE = """당신은 전기통신사업 회계분리기준(과기정통부 고시)·해설서에 정통한 회계법인 외부검증인이다.
수익원장의 그룹(계정×형태×역무)을 보고 거래 실질을 태깅하고 형태 분류의 적정성 초안을 판단하라.

## 확립된 판정 선례 (반드시 준수)
- 낙전수입(쿠폰·선불 미사용 소멸)은 '기타영업수익' 형태가 적정 (FY2013 자문단 결정, FY2019 지적)
- 임대폰·모뎀·AP 등 장치 임대 사용료와 그 위약금은 '장치비수익' 형태가 적정 (FY2022 지적)
- 요금할인 해지위약금은 '기타요금수익' (FY2016·2019·2021 지적)
- 사은품 반환금·연체료·연체가산금은 '기타영업수익' (FY2015·2016·2017·2020 지적)
- MVNO 판매활성화장려금 — 받는 쪽(MVNO)은 '기타영업수익' 총액 인식(순액 차감 금지, FY2018·2019 지적)이며 역무 할당은 월별 신규가입자 수 비율(FY2024 전문위). 주는 쪽(MNO)은 수익이 아니라 비용 — 판매영업기능(광고선전비외의 판매촉진비)이며 역무 배부는 도매제공수익 비율(FY2024 전문위)
- OutBound 국제로밍·에그 활용 로밍 수익은 '기타요금수익' (FY2020·2024 지적/질의)
- 요금수익 성격을 '기타영업수익'으로 분류하면 지적 대상 (FY2013·2018·2020 지적) — 단, 위 예외(낙전 등) 확인
- 기본료의 형태는 약관 성격 기준: 종량제 요금제→기본료(종량제요금수익), 정액제→정액요금수익 (FY2019·2022 지적)
- SMS/MMS 수익은 종량/초과_SMS/MMS 형태가 적정 (FY2019·2020 지적)
- '조정전표' 적요는 결산 조정 — 원거래 형태를 따라야 하므로 근거 전표 소명 필요
- 공통역무(S9xx: NSA공통·5G패킷공통 등)에 계상된 그룹은 형태 적정 여부와 별개로 태그를 '배부확인'으로 — 세대별 배부 완결 확인 필요 (FY2020 지적: 5G 관련을 공통 분류하여 지적)
- 매출에누리·매출할인·수익조정 계정은 원 수익의 차감(음수 계정) — 원 수익과 동일한 형태로 분류하는 것이 적정 (에누리 계정명과 형태명이 달라 보여도 원 수익 형태를 따랐다면 '적정')
- '도매제공' 태그는 MVNO 등 재판매사업자에게 망을 도매로 제공한 수익에 한정 — 솔루션·장비 판매는 '기타영업'
- 계정명과 형태명이 표면상 달라 보여도 형태가 거래 실질에 부합하면 '적정' (계정은 재무회계 체계라 판단 대상 아님 — 형태·역무만 판단)
- [비용] 기능 분류는 비용의 발생 원인·부서 실질 기준 (고시 제17조·제18조): 광고선전비→판매영업(광고선전), 판매촉진비·장려금·모집수수료→판매영업(판매촉진), 콜센터·고객상담→고객서비스, 기지국·중계기·전송·선로 관련 수선비/임차료/회선료/전력비→설비운영(설비사용료 등), 사무실 임차료·회계/인사/법무 등 지원부서 비용→일반관리, 연구개발비→연구개발
- [비용] 인건비·경비의 기능은 코스트센터(부서)의 주된 업무를 따름 (마케팅팀→판매영업, 회계팀→일반관리, Infra/네트워크팀→설비운영) — 부서 실질과 기능 불일치 시 검토필요 (FY2016 지적: 마케팅 부서 인건비를 판매영업기능으로 분류하여야)
- [비용] 통신망 전력·수도광열은 설비운영, 일반 사옥분은 일반관리 (FY2013·2014·2015·2018 지적: 전력비 기능·배부 오류 반복)
- [비용] 통신실·기지국 임차료는 설비운영 계열, 사무실 임차료는 일반관리·사업지원 (FY2013·2014 지적: 통신실 지급임차료 기능 분류 오류)
- [비용] 비용의 공통역무(S9xx) 계상은 공통비 배부 제도상 정상 흐름 — 기말 배부 완결과 배부기준의 합리성(고시 제19조~제33조)만 확인 대상
- [비용] 비용 원장의 형태(급여·경비·수선비·임차료·지급수수료·광고선전비 등)는 비용 성격 분류 — 수익 형태 기준(요금수익·기타영업수익 등)을 비용에 적용하지 말 것. 지급수수료·위탁수수료 형태는 용역 대가의 정상 형태
- [비용] 수선비·유지보수 비용의 형태는 '수선비'가 정상 — 설비사용료 형태(회선료·설비 임차 대가)와 혼동하지 말 것. 계정명과 형태명이 같은 성격이면 적정

## 출력 형식 (JSON만, 다른 텍스트 금지)
{"tag": "<실질태그>", "form_check": "적정|검토필요|판단불가", "func_check": "적정|검토필요|정보없음", "svc_check": "적정|검토필요|정보없음", "reason": "<근거 한 문장>"}

func_check(기능 적정성): 입력에 '기능명'이 있을 때만 판단 — 비용의 발생 원인·부서(코스트센터) 실질과 기능 계열이 부합하면 적정 (예: 광고선전비인데 기능이 일반관리면 검토필요). 기능 정보가 없으면 "정보없음".

svc_check(역무 적정성): 입력에 '서비스 계층' 정보가 있을 때만 판단 — 계정·적요의 실질과 역무 계열이 부합하면 적정, 어긋나면 검토필요 (예: 인터넷 수익 계정인데 역무가 이동통신 계열). 계층 정보가 없으면 "정보없음".

입력에 '관련 가이드라인 조항'이 주어지면 그 결론을 판단 근거로 우선 활용하고, reason에 해당 연도를 인용하라.
reason은 60자 이내 한 문장으로 간결하게.

tag는 반드시 아래 목록 중 하나만 사용 (형태명·계정명을 tag로 복사 금지):
일반요금, 매출에누리, 낙전, 장치임대, 해지위약금, 사은품반환, 연체료, 판매활성화장려금, 로밍, 접속정산, 도매제공, 포인트결제, 조정전표, 임직원자가소비, 내부거래, 배부확인, 기타영업, 판단불가
(예: 정액요금·종량제·SMS 등 통상의 요금수익은 모두 "일반요금")"""


def num(s):
    s = (s or '').replace(',', '').replace('"', '').strip()
    try:
        return float(s)
    except Exception:
        return 0.0


def summarize_ledger(path):
    """원장 CSV → 계정×형태×역무 그룹 요약"""
    groups = {}
    with io.open(path, encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            if len(r) < 12:
                continue
            key = (r[0].strip(), r[1].strip(), r[7].strip(), r[8].strip(), r[9].strip(), r[10].strip())
            g = groups.setdefault(key, {'cnt': 0, 'amt': 0.0,
                                        'descs': defaultdict(float), 'vendors': defaultdict(float)})
            g['cnt'] += 1
            a = num(r[11])
            g['amt'] += a
            if r[5].strip():
                g['descs'][r[5].strip()[:50]] += abs(a)
            if r[6].strip():
                g['vendors'][r[6].strip()[:30]] += abs(a)
    return groups


def rule_pretag(key, g):
    """결정론 프리패스 — 명확한 규칙은 LLM 없이 태깅 (일관성 보장).
    return (tag, form_check, reason) or None(→LLM으로)"""
    acct_name, form_name, svc_code = key[1], key[3], key[4]
    top_descs = ' '.join(sorted(g['descs'], key=g['descs'].get, reverse=True)[:3])

    svc_name = key[5]
    # 1. 공통역무 — 형태 이전에 역무 배부가 쟁점.
    #    코드 체계는 회사마다 다르므로(S914/T914 등) 서비스명 '공통'으로 감지
    if svc_code.startswith('S9') or '공통' in svc_name:
        extra = ''
        if '매출에누리' in acct_name or '매출할인' in acct_name:
            extra = ' (매출에누리 계정 — 원 수익 형태 준용 여부도 함께)'
        return ('배부확인', '검토필요',
                '공통역무(%s %s) 계상 — 세대·역무별 배부 완결 확인 필요%s [룰]' % (svc_code, svc_name, extra))
    # 1.5 로밍 — 방향별 형태 상이 (Outbound→기타요금수익 FY2020·2024 / Inbound→정액요금수익 FY2021)
    if '로밍' in acct_name or '로밍' in top_descs:
        low = (acct_name + ' ' + top_descs).lower()
        outbound = ('아웃바운드' in low) or ('outbound' in low) or ('해외로밍' in low)
        inbound = ('인바운드' in low) or ('inbound' in low)
        if outbound:
            ok = '기타요금' in form_name
            return ('로밍', '적정' if ok else '검토필요',
                    'OutBound 로밍은 기타요금수익 형태 (FY2020·2024) — 현재 %s [룰]' % form_name)
        if inbound:
            ok = '정액' in form_name
            return ('로밍', '적정' if ok else '검토필요',
                    'InBound 로밍은 정액요금수익 형태 (FY2021 지적) — 현재 %s [룰]' % form_name)
        return ('로밍', '검토필요',
                '로밍 수익 — In/Outbound 방향에 따라 형태 상이 (Out→기타요금, In→정액) 방향 확인 필요 [룰]')
    # 2. 매출에누리·매출할인 — 원 수익 차감, 원 형태 준용이면 적정
    if '매출에누리' in acct_name or '매출할인' in acct_name:
        return ('매출에누리', '적정',
                '원 수익의 차감 계정 — 원 수익과 동일 형태(%s) 준용은 적정 [룰]' % form_name)
    # 3. 조정전표
    if '조정전표' in top_descs:
        return ('조정전표', '검토필요',
                '결산 조정전표 — 원거래 형태 준용 여부 근거 전표 소명 필요 [룰]')
    # 4. 낙전
    if '낙전' in top_descs:
        ok = '기타영업' in form_name
        return ('낙전', '적정' if ok else '검토필요',
                '낙전수입은 기타영업수익 형태가 적정 (FY2013 자문단) — 현재 형태 %s [룰]' % form_name)
    # 5. 해지위약금 — 단말·장치 관련이면 장치비, 그 외(요금할인 등)는 기타요금수익
    #    (임대 룰보다 먼저 — "임대모뎀 해지위약금" 같은 적요가 임대로 오태깅되지 않게)
    both = acct_name + ' ' + top_descs
    if '위약금' in both:
        if any(k in both for k in ('단말', '모뎀', 'AP', '셋탑', '장비', '공유기')):
            ok = '장치' in form_name
            return ('해지위약금', '적정' if ok else '검토필요',
                    '단말·장치 관련 위약금은 장치비수익 (FY2023·2024 지적) — 현재 %s [룰]' % form_name)
        ok = '기타요금' in form_name
        return ('해지위약금', '적정' if ok else '검토필요',
                '요금할인 해지위약금은 기타요금수익 (FY2016·2019·2021 지적) — 현재 %s [룰]' % form_name)
    # 6. 연체료·연체가산금 → 기타영업수익
    if '연체' in both:
        ok = '기타영업' in form_name
        return ('연체료', '적정' if ok else '검토필요',
                '연체료·연체가산금은 기타영업수익 (FY2015·2016·2020 지적) — 현재 %s [룰]' % form_name)
    # 7. 임대폰·장치 임대
    if '임대폰' in top_descs or ('임대' in top_descs and '장치' in form_name):
        ok = '장치' in form_name
        return ('장치임대', '적정' if ok else '검토필요',
                '장치 임대 사용료는 장치비수익 형태가 적정 (FY2022 지적) — 현재 형태 %s [룰]' % form_name)
    return None


def ask_ollama(model, prompt, timeout=120):
    body = json.dumps({
        'model': model,
        'prompt': prompt,
        'system': SYSTEM_KNOWLEDGE,
        'stream': False,
        'format': 'json',
        'options': {'temperature': 0.1, 'num_predict': 200},
    }).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.loads(resp.read().decode('utf-8'))
    return out.get('response', '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ledger')
    ap.add_argument('--model', default='qwen3:8b')
    ap.add_argument('--limit', type=int, default=0, help='그룹 수 제한 (테스트용)')
    ap.add_argument('--min-amt', type=float, default=0, help='절대금액 하한 (원)')
    args = ap.parse_args()

    print('원장 요약 중:', args.ledger)
    groups = summarize_ledger(args.ledger)
    items = sorted(groups.items(), key=lambda x: -abs(x[1]['amt']))
    if args.min_amt:
        items = [x for x in items if abs(x[1]['amt']) >= args.min_amt]
    if args.limit:
        items = items[:args.limit]
    print('대상 그룹: %d개 (모델: %s)' % (len(items), args.model))

    out_path = os.path.splitext(args.ledger)[0] + '_ollama태깅.csv'
    t0 = time.time()
    with io.open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['계정', '계정명', '형태', '형태명', '역무', '서비스명',
                    '행수', '금액합계', '적요top3', '거래처top3',
                    'AI태그', 'AI형태판정', 'AI근거'])
        for i, (key, g) in enumerate(items):
            descs = sorted(g['descs'].items(), key=lambda x: -x[1])[:3]
            vendors = sorted(g['vendors'].items(), key=lambda x: -x[1])[:3]
            desc_s = ' / '.join(d for d, _ in descs)
            ven_s = ' / '.join(v for v, _ in vendors)
            amt_s = '{:,.0f}'.format(g['amt'])
            prompt = (
                '계정명: %s\n형태명: %s\n역무: %s(%s)\n'
                '행수: %d, 금액합계: %s원\n적요(대표): %s\n거래처(대표): %s\n'
                '이 그룹의 실질을 태깅하고 형태 분류 적정성을 판단하라.'
                % (key[1], key[3], key[5], key[4], g['cnt'], amt_s, desc_s or '(없음)', ven_s or '(없음)'))
            # 결정론 룰 프리패스 — 매치되면 LLM 스킵
            pre = rule_pretag(key, g)
            if pre:
                tag, chk, reason = pre
            else:
                tag, chk, reason = '판단불가', '판단불가', ''
                try:
                    resp = ask_ollama(args.model, prompt)
                    j = json.loads(resp)
                    tag = j.get('tag', '판단불가')
                    chk = j.get('form_check', '판단불가')
                    reason = (j.get('reason', '') or '') + ' [LLM]'
                except Exception as ex:
                    reason = 'ERROR: %s' % ex
            w.writerow([key[0], key[1], key[2], key[3], key[4], key[5],
                        g['cnt'], int(g['amt']), desc_s, ven_s, tag, chk, reason])
            if (i + 1) % 10 == 0 or i == len(items) - 1:
                el = time.time() - t0
                print('  %d/%d 완료 (%.0f초 경과, 그룹당 %.1f초)'
                      % (i + 1, len(items), el, el / (i + 1)))
    print('산출:', out_path)


if __name__ == '__main__':
    main()
