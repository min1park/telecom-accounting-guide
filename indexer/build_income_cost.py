# -*- coding: utf-8 -*-
"""수익비용_자동검토_v1.html 빌드

자산 v2를 베이스로 개조:
- 그룹키: 세분류 → 계정+형태+기능+역무 조합
- 판단 근거: 자산명 → 적요·BM·CC·거래처·계정명
- R_GL 매칭 로직 그대로 재사용 (인덱스 공용)
"""
import io, os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# v2를 베이스로 시작 (v2에는 이미 인덱스 인라인 + R_GL 로직 있음)
v2_path = os.path.join(ROOT, '자산원장_자동검토_v2.html')
new_html = io.open(v2_path, encoding='utf-8').read()

# ─────────── 1. 헤더/타이틀 변경 ───────────
new_html = new_html.replace(
    '<title>통신회계 자산원장 자동검토</title>',
    '<title>통신회계 수익·비용 원장 자동검토</title>', 1)
new_html = new_html.replace(
    '<h1>통신회계 자산원장 자동검토<span class="badge">v2.0 · GL 매칭</span></h1>',
    '<h1>통신회계 수익·비용 원장 자동검토<span class="badge">v1.0 · GL 매칭</span></h1>', 1)
new_html = new_html.replace(
    '자산원장 자동검토 v2.0 · 가이드라인 매칭(GL) 층 추가 (1,857 entry 인덱스)',
    '수익·비용 원장 자동검토 v1.0 · 계정+형태+기능+역무 그룹핑 + 가이드라인 매칭 (1,857 entry 인덱스)', 1)

# ─────────── 2. FIELDS 재정의 (자산원장 필드 → 수익비용 필드) ───────────
OLD_FIELDS = (
    'var FIELDS = [\n'
    '  {key:"acct",  label:"계정결정(코드)",  req:true,  find:function(h){return /계정/.test(h) && !/내역|명/.test(h);}},\n'
    '  {key:"acctName",label:"계정명",       req:false, find:function(h){return /계정/.test(h) && /내역|명/.test(h);}},\n'
    '  {key:"subclass",label:"자산세분류",   req:false, find:function(h){return /세분류/.test(h);}},\n'
    '  {key:"form",  label:"형태코드",       req:true,  find:function(h){return /형태/.test(h) && !/명/.test(h);}},\n'
    '  {key:"formName",label:"형태명",       req:false, find:function(h){return /형태명/.test(h);}},\n'
    '  {key:"func",  label:"기능코드",       req:true,  find:function(h){return /기능/.test(h) && !/명/.test(h);}},\n'
    '  {key:"funcName",label:"기능명",       req:false, find:function(h){return /기능명/.test(h);}},\n'
    '  {key:"svc",   label:"역무(서비스)코드",req:true, find:function(h){return (/역무/.test(h)&&!/명/.test(h)) || /서비스코드/.test(h);}},\n'
    '  {key:"svcName",label:"서비스명",      req:false, find:function(h){return /서비스명|역무명/.test(h);}},\n'
    '  {key:"cnt",   label:"건수",           req:false, find:function(h){return /개수|건수/.test(h);}},\n'
    '  {key:"acq",   label:"취득금액",       req:true,  find:function(h){return /취득/.test(h);}},\n'
    '  {key:"dep",   label:"당기상각액",     req:false, find:function(h){return /당기상각/.test(h);}},\n'
    '  {key:"book",  label:"장부가액",       req:false, find:function(h){return /장부/.test(h) && !/기초/.test(h);}}\n'
    '];'
)

NEW_FIELDS = (
    'var FIELDS = [\n'
    '  {key:"acct",  label:"계정과목(코드)",  req:true,  find:function(h){return /계정/.test(h) && !/내역|명/.test(h);}},\n'
    '  {key:"acctName",label:"계정명",       req:false, find:function(h){return /계정/.test(h) && /내역|명/.test(h);}},\n'
    '  {key:"form",  label:"형태코드",       req:true,  find:function(h){return /형태/.test(h) && !/명/.test(h);}},\n'
    '  {key:"formName",label:"형태명",       req:false, find:function(h){return /형태명/.test(h);}},\n'
    '  {key:"func",  label:"기능코드",       req:true,  find:function(h){return /기능/.test(h) && !/명/.test(h);}},\n'
    '  {key:"funcName",label:"기능명",       req:false, find:function(h){return /기능명/.test(h);}},\n'
    '  {key:"svc",   label:"역무(서비스)코드",req:true, find:function(h){return (/역무/.test(h)&&!/명/.test(h)) || /서비스코드/.test(h);}},\n'
    '  {key:"svcName",label:"서비스명",      req:false, find:function(h){return /서비스명|역무명/.test(h);}},\n'
    '  {key:"desc",  label:"적요",            req:false, find:function(h){return /적요|내역|설명|비고|Description|memo/i.test(h);}},\n'
    '  {key:"bm",    label:"BM",              req:false, find:function(h){return /^BM|BM코드|사업단위|상품/i.test(h);}},\n'
    '  {key:"cc",    label:"코스트센터(CC)",  req:false, find:function(h){return /코스트|Cost.*Center|^CC|부서|부문/i.test(h);}},\n'
    '  {key:"vendor",label:"거래처",          req:false, find:function(h){return /거래처|Vendor|Supplier|Customer|공급자|매입처|매출처/i.test(h);}},\n'
    '  {key:"cnt",   label:"건수",            req:false, find:function(h){return /개수|건수/.test(h);}},\n'
    '  {key:"amt",   label:"금액",            req:true,  find:function(h){return /금액|Amount|합계/.test(h) && !/취득|장부|상각/.test(h);}}\n'
    '];'
)

if OLD_FIELDS in new_html:
    new_html = new_html.replace(OLD_FIELDS, NEW_FIELDS, 1)
    print('(1) FIELDS 재정의 OK')
else:
    print('!! (1) FIELDS 마커 못 찾음')

# ─────────── 3. rowToTags 확장 (판단 근거 텍스트 필드 변경) ───────────
OLD_TAG = (
    '  ["subclass","formName","funcName","svcName","acctName"].forEach(function(k){\n'
    '    if (map[k] && r[map[k]] != null) textParts.push(String(r[map[k]]));\n'
    '  });'
)
NEW_TAG = (
    '  /* 수익·비용 판단 근거 텍스트: 적요·BM·CC·거래처·계정명·형태명·기능명·서비스명 */\n'
    '  ["desc","bm","cc","vendor","acctName","formName","funcName","svcName"].forEach(function(k){\n'
    '    if (map[k] && r[map[k]] != null) textParts.push(String(r[map[k]]));\n'
    '  });'
)
if OLD_TAG in new_html:
    new_html = new_html.replace(OLD_TAG, NEW_TAG, 1)
    print('(2) rowToTags 필드 확장 OK')
else:
    print('!! (2) rowToTags 마커 못 찾음')

# ─────────── 4. guidelineMatchBySubclass → guidelineMatchByAccount ───────────
OLD_MATCH = (
    '/* 세분류(subclass) 단위 그룹핑 → 대세 자산 대표로 매칭.\n'
    '   세분류 없으면 형태|기능|역무 조합으로 fallback 그룹핑 */\n'
    'function guidelineMatchBySubclass(rows, map, K){\n'
    '  var groups = {};\n'
    '  var hasSubclass = !!map.subclass;\n'
    '  rows.forEach(function(r){\n'
    '    var sc = hasSubclass ? String(r[map.subclass]||"").trim() : "";\n'
    '    if (!sc){\n'
    '      var form = map.form ? String(r[map.form]||"").trim() : "";\n'
    '      var func = map.func ? String(r[map.func]||"").trim() : "";\n'
    '      var svc  = map.svc  ? String(r[map.svc] ||"").trim() : "";\n'
    '      sc = (form||"?")+"|"+(func||"?")+"|"+(svc||"?");\n'
    '      if (sc === "?|?|?") return;\n'
    '    }\n'
    '    if (!groups[sc]) groups[sc] = {sample:r, cnt:0, acq:0, forms:{}, funcs:{}, svcs:{}};\n'
    '    var g = groups[sc]; g.cnt++;\n'
    '    var acq = map.acq ? num(r[map.acq]) : 0; g.acq += Math.abs(acq);\n'
    '    if (map.form)  { var f=String(r[map.form]||""); if(f) g.forms[f]=(g.forms[f]||0)+1; }\n'
    '    if (map.func)  { var f=String(r[map.func]||""); if(f) g.funcs[f]=(g.funcs[f]||0)+1; }\n'
    '    if (map.svc)   { var f=String(r[map.svc]||"");  if(f) g.svcs[f]=(g.svcs[f]||0)+1; }\n'
    '  });'
)

NEW_MATCH = (
    '/* 수익·비용용 그룹핑: 계정+형태+기능+역무 조합 단위.\n'
    '   각 그룹의 대표: 건수·금액, 적요 최빈, 거래처 최빈, BM·CC 대세 */\n'
    'function guidelineMatchBySubclass(rows, map, K){\n'
    '  var groups = {};\n'
    '  rows.forEach(function(r){\n'
    '    var acct = map.acct ? String(r[map.acct]||"").trim() : "";\n'
    '    var form = map.form ? String(r[map.form]||"").trim() : "";\n'
    '    var func = map.func ? String(r[map.func]||"").trim() : "";\n'
    '    var svc  = map.svc  ? String(r[map.svc] ||"").trim() : "";\n'
    '    var key = (acct||"?")+"|"+(form||"?")+"|"+(func||"?")+"|"+(svc||"?");\n'
    '    if (key === "?|?|?|?") return;\n'
    '    if (!groups[key]) groups[key] = {sample:r, cnt:0, acq:0, forms:{}, funcs:{}, svcs:{},\n'
    '                                       accts:{}, descs:{}, vendors:{}, bms:{}, ccs:{}};\n'
    '    var g = groups[key]; g.cnt++;\n'
    '    var amt = map.amt ? num(r[map.amt]) : 0; g.acq += Math.abs(amt);\n'
    '    if (acct) g.accts[acct] = (g.accts[acct]||0)+1;\n'
    '    if (form) g.forms[form] = (g.forms[form]||0)+1;\n'
    '    if (func) g.funcs[func] = (g.funcs[func]||0)+1;\n'
    '    if (svc)  g.svcs[svc]   = (g.svcs[svc]  ||0)+1;\n'
    '    if (map.desc)   { var v=String(r[map.desc]  ||"").trim(); if(v) g.descs[v]  =(g.descs[v]  ||0)+1; }\n'
    '    if (map.vendor) { var v=String(r[map.vendor]||"").trim(); if(v) g.vendors[v]=(g.vendors[v]||0)+1; }\n'
    '    if (map.bm)     { var v=String(r[map.bm]    ||"").trim(); if(v) g.bms[v]    =(g.bms[v]    ||0)+1; }\n'
    '    if (map.cc)     { var v=String(r[map.cc]    ||"").trim(); if(v) g.ccs[v]    =(g.ccs[v]    ||0)+1; }\n'
    '  });'
)
if OLD_MATCH in new_html:
    new_html = new_html.replace(OLD_MATCH, NEW_MATCH, 1)
    print('(3) 그룹핑 함수 변경 OK (계정+형태+기능+역무)')
else:
    print('!! (3) 그룹핑 함수 마커 못 찾음')

# ─────────── 5. 그룹 결과 필드 확장 (subclass → key, 적요·거래처 반영) ───────────
OLD_OUT = (
    '    if (top.length > 0){\n'
    '      var mostForm = Object.keys(g.forms).sort(function(a,b){return g.forms[b]-g.forms[a];})[0]||"";\n'
    '      var mostFunc = Object.keys(g.funcs).sort(function(a,b){return g.funcs[b]-g.funcs[a];})[0]||"";\n'
    '      var mostSvc  = Object.keys(g.svcs ).sort(function(a,b){return g.svcs[b] -g.svcs[a] ;})[0]||"";\n'
    '      out.push({subclass:sc, cnt:g.cnt, acq:g.acq, form:mostForm, func:mostFunc, svc:mostSvc, tags:tags, matches:top});\n'
    '    }\n'
    '  });'
)
NEW_OUT = (
    '    if (top.length > 0){\n'
    '      var topN = function(d,n){ return Object.keys(d).sort(function(a,b){return d[b]-d[a];}).slice(0,n||1); };\n'
    '      out.push({\n'
    '        subclass: key,\n'
    '        cnt: g.cnt, acq: g.acq,\n'
    '        acct: topN(g.accts)[0]||"", form: topN(g.forms)[0]||"", func: topN(g.funcs)[0]||"", svc: topN(g.svcs)[0]||"",\n'
    '        descTop:   topN(g.descs, 3),\n'
    '        vendorTop: topN(g.vendors, 3),\n'
    '        bmTop:     topN(g.bms, 2),\n'
    '        ccTop:     topN(g.ccs, 2),\n'
    '        tags: tags, matches: top\n'
    '      });\n'
    '    }\n'
    '  });'
)
if OLD_OUT in new_html:
    new_html = new_html.replace(OLD_OUT, NEW_OUT, 1)
    print('(4) 그룹 결과 필드 확장 OK')
else:
    print('!! (4) 그룹 결과 마커 못 찾음')

# ─────────── 6. R_GL 표 컬럼·렌더 변경 (수익·비용용) ───────────
OLD_TBL = (
    '    glHtml += "<div class=\'tblwrap\'><table><thead><tr><th>세분류</th><th>대세 형태·기능·역무</th><th>건수</th><th>취득금액</th><th>매칭된 태그</th><th>관련 조항 (top-5)</th></tr></thead><tbody>";'
)
NEW_TBL = (
    '    glHtml += "<div class=\'tblwrap\'><table><thead><tr><th>계정·형태·기능·역무</th><th>대세 적요 / 거래처 / BM·CC</th><th>건수</th><th>금액</th><th>매칭된 태그</th><th>관련 조항 (top-5)</th></tr></thead><tbody>";'
)
if OLD_TBL in new_html:
    new_html = new_html.replace(OLD_TBL, NEW_TBL, 1)
    print('(5) 표 헤더 변경 OK')

OLD_ROW = (
    '      glHtml += "<tr><td><b>"+esc(g.subclass)+"</b></td><td>"+esc(g.form+" · "+g.func+" · "+g.svc)+"</td>"+\n'
    '        "<td class=\'num\'>"+fmt(g.cnt)+"</td><td class=\'num\'>"+fmtEok(g.acq)+"</td>"+\n'
    '        "<td style=\'font-size:10px;color:#667;white-space:normal;max-width:180px\'>"+esc(tagList.slice(0,6).join(", "))+(tagList.length>6?" …":"")+"</td>"+\n'
    '        "<td style=\'white-space:normal;max-width:520px\'>"+matchHtml+"</td></tr>";'
)
NEW_ROW = (
    '      var codeCell = "<b>"+esc(g.acct)+"</b><br><span style=\'font-size:10px;color:#556\'>"+esc(g.form+" · "+g.func+" · "+g.svc)+"</span>";\n'
    '      var descCell = "";\n'
    '      if (g.descTop.length)   descCell += "<div><b>적요:</b> "+esc(g.descTop.join(" / "))+"</div>";\n'
    '      if (g.vendorTop.length) descCell += "<div><b>거래처:</b> "+esc(g.vendorTop.join(" / "))+"</div>";\n'
    '      if (g.bmTop.length||g.ccTop.length) descCell += "<div style=\'color:#667\'><b>BM/CC:</b> "+esc((g.bmTop.join(",")||"-")+" / "+(g.ccTop.join(",")||"-"))+"</div>";\n'
    '      glHtml += "<tr><td style=\'white-space:normal;max-width:180px\'>"+codeCell+"</td>"+\n'
    '        "<td style=\'font-size:11px;white-space:normal;max-width:280px\'>"+descCell+"</td>"+\n'
    '        "<td class=\'num\'>"+fmt(g.cnt)+"</td><td class=\'num\'>"+fmtEok(g.acq)+"</td>"+\n'
    '        "<td style=\'font-size:10px;color:#667;white-space:normal;max-width:180px\'>"+esc(tagList.slice(0,6).join(", "))+(tagList.length>6?" …":"")+"</td>"+\n'
    '        "<td style=\'white-space:normal;max-width:520px\'>"+matchHtml+"</td></tr>";'
)
if OLD_ROW in new_html:
    new_html = new_html.replace(OLD_ROW, NEW_ROW, 1)
    print('(6) 표 row 변경 OK')

# ─────────── 7. 카드 라벨 변경 ───────────
new_html = new_html.replace(
    '<h3>R_GL. 가이드라인 매칭</h3><div class=\'n\'>"+fmt(glResults.length)+"<span style=\'font-size:12px\'> 세분류</span></div>',
    '<h3>R_GL. 가이드라인 매칭</h3><div class=\'n\'>"+fmt(glResults.length)+"<span style=\'font-size:12px\'> 그룹</span></div>', 1)
new_html = new_html.replace(
    '가이드라인 조항 매칭 (세분류 단위)',
    '가이드라인 조항 매칭 (계정+형태+기능+역무 그룹)', 1)
new_html = new_html.replace(
    '각 자산 세분류(subclass)의 대표 자산을 표준 용어 사전으로 태깅 후, guideline_index (1,857 entry)와 대조하여 관련도 top-5 조항을 매칭. 지적이 아니라 참고: 회사 원장 검토·조서 작성 시 근거 조항 인용용.',
    '각 그룹(계정·형태·기능·역무 조합)의 적요·거래처·BM·CC 정보를 표준 용어 사전으로 태깅 후, guideline_index (1,857 entry)와 대조하여 관련도 top-5 조항을 매칭. 지적이 아니라 참고: 회사 원장 검토·조서 작성 시 근거 조항 인용용.', 1)
new_html = new_html.replace(
    '세분류 "+fmt(glResults.length)+"개 매칭',
    '그룹 "+fmt(glResults.length)+"개 매칭', 1)
new_html = new_html.replace(
    '<div class=\'stat\'>※ 화면에는 100개 세분류',
    '<div class=\'stat\'>※ 화면에는 100개 그룹', 1)

# ─────────── 8. 엑셀 시트 헤더 변경 ───────────
new_html = new_html.replace(
    '    var glHead = ["세분류","대세 형태","대세 기능","대세 역무","건수","취득금액",\n'
    '                  "매칭된 태그","순위","관련 조항 ID","카테고리","연도","제목","점수","매칭 태그","결정 유형","결론","출처 PDF"];',
    '    var glHead = ["그룹키(계정|형태|기능|역무)","대세 계정","대세 형태","대세 기능","대세 역무","적요 상위","거래처 상위","BM 상위","CC 상위","건수","금액",\n'
    '                  "매칭된 태그","순위","관련 조항 ID","카테고리","연도","제목","점수","매칭 태그","결정 유형","결론","출처 PDF"];', 1)
new_html = new_html.replace(
    '        glRows.push([g.subclass, g.form, g.func, g.svc, g.cnt, g.acq, tagStr, i+1,\n'
    '          m.entry.id, m.entry.category, m.entry.year, m.entry.title, m.score,\n'
    '          m.matched.join("; "), (m.entry.decision_types||[]).join(","),\n'
    '          (m.entry.conclusions[0]||""), m.entry.source_pdf]);',
    '        glRows.push([g.subclass, g.acct, g.form, g.func, g.svc,\n'
    '          (g.descTop||[]).join(" / "), (g.vendorTop||[]).join(" / "),\n'
    '          (g.bmTop||[]).join(","), (g.ccTop||[]).join(","),\n'
    '          g.cnt, g.acq, tagStr, i+1,\n'
    '          m.entry.id, m.entry.category, m.entry.year, m.entry.title, m.score,\n'
    '          m.matched.join("; "), (m.entry.decision_types||[]).join(","),\n'
    '          (m.entry.conclusions[0]||""), m.entry.source_pdf]);', 1)

# ─────────── 9. 엑셀 파일명 ───────────
new_html = new_html.replace(
    'XLSX.writeFile(wb, "자산원장_자동검토결과_"+ds+".xlsx");',
    'XLSX.writeFile(wb, "수익비용원장_자동검토결과_"+ds+".xlsx");', 1)

# ─────────── 10. 데이터 정합 룰 (R5) — 자산의 취득/상각 → 수익비용의 금액 정합 ───────────
OLD_R5 = (
    '    /* R5 */\n'
    '    if(!isContra){\n'
    '      if(acq===0 && (dep>0 || book>0)) hits.R5.push({r:r, note:"취득가 0인데 상각 "+fmt(dep)+" / 장부가 "+fmt(book)});\n'
    '      else if(acq>0 && book>acq)       hits.R5.push({r:r, note:"장부가("+fmt(book)+") > 취득가("+fmt(acq)+")"});\n'
    '      else if(acq<0)                   hits.R5.push({r:r, note:"음수 취득가 "+fmt(acq)+" (차감계정 여부 확인)"});\n'
    '    }'
)
NEW_R5 = (
    '    /* R5: 수익·비용용 정합 — 금액 0, 극단값 등 */\n'
    '    var amt = map.amt ? num(r[map.amt]) : 0;\n'
    '    if(amt===0) hits.R5.push({r:r, note:"금액 0 (더미·조정 확인)"});\n'
    '    else if(amt<0 && !isContra) hits.R5.push({r:r, note:"음수 금액 "+fmt(amt)+" (환입/취소 확인)"});'
)
if OLD_R5 in new_html:
    new_html = new_html.replace(OLD_R5, NEW_R5, 1)
    print('(7) R5 수익비용 정합 조정 OK')

# ─────────── 11. runRules 안 acq/dep/book → amt로 변경 ───────────
new_html = new_html.replace(
    '    var acq=getn(r,"acq"), dep=getn(r,"dep"), book=getn(r,"book"), cnt=map.cnt?getn(r,"cnt"):1;\n'
    '    tot.cnt+=cnt; tot.acq+=acq;',
    '    var amt=getn(r,"amt"), cnt=map.cnt?getn(r,"cnt"):1;\n'
    '    tot.cnt+=cnt; tot.acq+=amt;', 1)

# summarize 안의 취득금액→금액 라벨
new_html = new_html.replace(
    '    hs.forEach(function(h){ cnt += map.cnt?getn(h.r,"cnt"):1; acq+=getn(h.r,"acq"); book+=getn(h.r,"book"); });',
    '    hs.forEach(function(h){ cnt += map.cnt?getn(h.r,"cnt"):1; acq+=getn(h.r,"amt"); book+=getn(h.r,"amt"); });', 1)

# R6 사전 집계 안 acq → amt
new_html = new_html.replace(
    '    var sc = get(r,"subclass"); if(!sc) return;\n'
    '    var key = sc, combo = get(r,"form")+"|"+get(r,"func");\n'
    '    if(!grp[key]) grp[key]={total:0, combos:{}};\n'
    '    var a = Math.abs(getn(r,"acq"));',
    '    /* R6 사전 집계: 계정별 형태+기능 조합 점유율 (금액 기준) */\n'
    '    var sc = get(r,"acct"); if(!sc) return;\n'
    '    var key = sc, combo = get(r,"form")+"|"+get(r,"func");\n'
    '    if(!grp[key]) grp[key]={total:0, combos:{}};\n'
    '    var a = Math.abs(getn(r,"amt"));', 1)

# R6 안 subclass 참조 → acct
new_html = new_html.replace(
    '    /* R6 */\n'
    '    if(sc && dominant[sc]){\n'
    '      var d=dominant[sc], combo=form+"|"+func, share=(d.combos[combo]||0)/d.total;\n'
    '      if(combo!==d.combo && d.share>=cfg.DOMINANT_SHARE && share>0 && share<=cfg.MINORITY_SHARE && Math.abs(acq)>0)\n'
    '        hits.R6.push({r:r, note:"세분류 "+sc+" 대세("+d.combo.replace("|"," / ")+" "+(d.share*100).toFixed(0)+"%) ↔ 본 조합 "+(share*100).toFixed(1)+"%"});\n'
    '    }',
    '    /* R6 */\n'
    '    var acctSc = get(r,"acct");\n'
    '    if(acctSc && dominant[acctSc]){\n'
    '      var d=dominant[acctSc], combo=form+"|"+func, share=(d.combos[combo]||0)/d.total;\n'
    '      if(combo!==d.combo && d.share>=cfg.DOMINANT_SHARE && share>0 && share<=cfg.MINORITY_SHARE && Math.abs(amt)>0)\n'
    '        hits.R6.push({r:r, note:"계정 "+acctSc+" 대세("+d.combo.replace("|"," / ")+" "+(d.share*100).toFixed(0)+"%) ↔ 본 조합 "+(share*100).toFixed(1)+"%"});\n'
    '    }', 1)

# runRules 시작 부분 var sc=get(r,"subclass"); 제거 (수익비용에서 세분류 없음)
new_html = new_html.replace(
    '    var acct=get(r,"acct"), acctName=get(r,"acctName"), form=get(r,"form"), func=get(r,"func"), svc=get(r,"svc");\n'
    '    var sc=get(r,"subclass");',
    '    var acct=get(r,"acct"), acctName=get(r,"acctName"), form=get(r,"form"), func=get(r,"func"), svc=get(r,"svc");', 1)

# 합계 표시 문구 "취득금액 → 금액"
new_html = new_html.replace(
    '"전체 "+fmt(res.tot.rows)+"행 · 자산 "+fmt(res.tot.cnt)+"건 · 취득금액 합계 "+fmtEok(res.tot.acq)',
    '"전체 "+fmt(res.tot.rows)+"행 · 거래 "+fmt(res.tot.cnt)+"건 · 금액 합계 "+fmtEok(res.tot.acq)', 1)
new_html = new_html.replace(
    'fmt(s.cnt)+"건 · 취득 "+fmtEok(s.acq)',
    'fmt(s.cnt)+"건 · 금액 "+fmtEok(s.acq)', 1)
new_html = new_html.replace(
    '" — "+fmt(hs.length)+"행 / "+fmt(s.cnt)+"건 / 취득 "+fmtEok(s.acq)+"</h3>"',
    '" — "+fmt(hs.length)+"행 / "+fmt(s.cnt)+"건 / 금액 "+fmtEok(s.acq)+"</h3>"', 1)

# 엑셀 요약 라벨
new_html = new_html.replace(
    '["룰","심각도","룰명","지적 행수","자산건수","취득금액 합계","검토 근거"]',
    '["룰","심각도","룰명","지적 행수","거래건수","금액 합계","검토 근거"]', 1)

# ─────────── 저장 ───────────
out_path = os.path.join(ROOT, '수익비용_자동검토_v1.html')
io.open(out_path, 'w', encoding='utf-8').write(new_html)
print('─' * 60)
print('산출: %s' % out_path)
print('크기: %.1f KB' % (os.path.getsize(out_path)/1024))
