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

# ─────────── 12. DEFAULT_CFG → P&L 매트릭스로 교체 ───────────
OLD_CFG = (
    'var DEFAULT_CFG = {\n'
    '  ACCT_FORM: {\n'
    '    "282100":["FC16"], "300100":["FC1010"], "301100":["FC1020"], "303100":["FC1030","FC0300"],\n'
    '    "305100":["FC01","FC02","FC03","FC04","FC05","FC06"], "306":["FC01","FC02","FC03","FC04","FC05","FC06"],\n'
    '    "307100":["FC1120"], "309100":["FC1130"], "311100":["FC11"], "313100":["FC11"],\n'
    '    "315":["FC18"], "320":["FC12"], "321":["FC12"], "322":["FC12"],\n'
    '    "330":["FC14"], "331":["FC14"], "332":["FC14"], "333":["FC14"], "336":["FC14"]\n'
    '  },\n'
    '  FORM_FUNC: {\n'
    '    "FC0100":["F011"], "FC0200":["F021","F022"], "FC0300":["F031"], "FC0400":["F041"],\n'
    '    "FC0500":["F050"], "FC0600":["F060"],\n'
    '    "FC1010":["F00","F10"], "FC1020":["F00","F10"], "FC1030":["F00","F10"],\n'
    '    "FC1120":["F00"], "FC1130":["F00","F11"], "FC1600":["F00","F10"],\n'
    '    "FC1220":["F00"], "FC1230":["F00"], "FC1241":["F00"], "FC1260":["F00","F12"],\n'
    '    "FC1400":["F13"], "FC1810":["F00","F03","F10","F11"]\n'
    '  },\n'
    '  EA_FORMS: ["FC01","FC02","FC03","FC04","FC05","FC06"],\n'
    '  COMMON_FUNCS: ["F0212","F0213","F0313","F0314","F0600"],\n'
    '  NONBIZ_SVC: ["S501"],\n'
    '  DUMMY_SVC: ["SZZZ","S000"],\n'
    '  MINORITY_SHARE: 0.10,\n'
    '  DOMINANT_SHARE: 0.70\n'
    '};'
)

NEW_CFG = (
    '/* ═══ P&L 매트릭스 초안 (계정명 키워드 기반) ═══\n'
    '   계정코드는 회사마다 다르므로 계정명(계정과목명) 키워드로 매칭.\n'
    '   ACCT_NAME_FORM: 계정명에 키워드 포함 → 허용 형태 접두어.\n'
    '   ACCT_FORM: 코드 기반 backup (회사가 통일 코드 쓸 때).\n'
    '   근거: 회계분리기준 고시 §16(수익 배부)·§17(비용 배부) + 해설서 2026.4 */\n'
    'var DEFAULT_CFG = {\n'
    '  /* 계정명 키워드 → 허용 형태 접두어 (핵심 매칭 축) */\n'
    '  ACCT_NAME_FORM: {\n'
    '    /* ─── 수익 ─── */\n'
    '    "요금수익":       ["FC70","FC71","FC72"],\n'
    '    "기본료":         ["FC70","FC71"],\n'
    '    "통화료":         ["FC70","FC71"],\n'
    '    "데이터수익":     ["FC70","FC72"],\n'
    '    "이용료":         ["FC70"],\n'
    '    "접속료수익":     ["FC73"],\n'
    '    "상호접속":       ["FC73"],\n'
    '    "도매제공수익":   ["FC74"],\n'
    '    "도매수익":       ["FC74"],\n'
    '    "내부거래수익":   ["FC75"],\n'
    '    "결합할인":       ["FC76"],\n'
    '    "장치비수익":     ["FC76"],\n'
    '    "단말임대수익":   ["FC76"],\n'
    '    "임대료수익":     ["FC76"],\n'
    '    "기타영업수익":   ["FC79"],\n'
    '    /* ─── 매출원가·설비운영비용 ─── */\n'
    '    "설비운영비용":   ["FC50","FC51"],\n'
    '    "시설운영비용":   ["FC50","FC51"],\n'
    '    "접속료비용":     ["FC52"],\n'
    '    "접속료":         ["FC52"],\n'
    '    "도매제공대가":   ["FC53"],\n'
    '    "망이용대가":     ["FC53"],\n'
    '    "내부거래비용":   ["FC54"],\n'
    '    /* ─── 판매관리비 ─── */\n'
    '    "인건비":         ["FC60","FC50"],\n'
    '    "급여":           ["FC60"],\n'
    '    "급료":           ["FC60"],\n'
    '    "임금":           ["FC60"],\n'
    '    "복리후생":       ["FC61"],\n'
    '    "감가상각":       ["FC62"],\n'
    '    "상각비":         ["FC62"],\n'
    '    "임차료":         ["FC63"],\n'
    '    "임대료":         ["FC63"],\n'
    '    "광고선전비":     ["FC64"],\n'
    '    "광고비":         ["FC64"],\n'
    '    "판매촉진비":     ["FC65"],\n'
    '    "판촉비":         ["FC65"],\n'
    '    "판매활성화":     ["FC65"],\n'
    '    "장려금":         ["FC65"],\n'
    '    "지원금":         ["FC65"],\n'
    '    "위탁수수료":     ["FC66"],\n'
    '    "용역대가":       ["FC66"],\n'
    '    "외주비":         ["FC66"],\n'
    '    "지급수수료":     ["FC66"],\n'
    '    "일반관리비":     ["FC69"]\n'
    '  },\n'
    '\n'
    '  /* 계정 접두어 → 허용 형태 (코드 통일 회사에만 backup 매칭) */\n'
    '  ACCT_FORM: {\n'
    '    /* ─── 수익 계정 (4xxxxx) ─── */\n'
    '    "40":  ["FC70","FC71","FC72"],   /* 요금수익 → 수익형태 */\n'
    '    "41":  ["FC73"],                  /* 접속료수익 */\n'
    '    "42":  ["FC74"],                  /* 도매제공수익 */\n'
    '    "43":  ["FC75"],                  /* 내부거래수익 */\n'
    '    "44":  ["FC76"],                  /* 결합할인·장치비수익 */\n'
    '    "49":  ["FC79"],                  /* 기타영업수익 */\n'
    '    /* ─── 매출원가·설비운영비용 (5xxxxx) ─── */\n'
    '    "50":  ["FC50","FC51"],           /* 설비운영비용 (인건비·경비·감가상각) */\n'
    '    "51":  ["FC52"],                  /* 접속료비용 */\n'
    '    "52":  ["FC53"],                  /* 도매제공대가 */\n'
    '    "53":  ["FC54"],                  /* 내부거래비용 */\n'
    '    /* ─── 판매관리비 (6xxxxx) ─── */\n'
    '    "60":  ["FC60","FC61"],           /* 인건비·복리후생 */\n'
    '    "61":  ["FC62"],                  /* 감가상각비 */\n'
    '    "62":  ["FC63"],                  /* 임차료 */\n'
    '    "63":  ["FC64"],                  /* 광고선전비 */\n'
    '    "64":  ["FC65"],                  /* 판매촉진비·판매활성화 장려금 */\n'
    '    "65":  ["FC66"],                  /* 위탁수수료·용역대가 */\n'
    '    "69":  ["FC69"]                   /* 기타 판관비 */\n'
    '  },\n'
    '\n'
    '  /* 형태 접두어 → 허용 기능 접두어 (§17 비용의 기능분류) */\n'
    '  FORM_FUNC: {\n'
    '    /* 수익 형태는 통상 기능 F00 (설비운영에서 발생하는 수익) */\n'
    '    "FC70": ["F00"],                  /* 요금수익 → 설비운영 */\n'
    '    "FC71": ["F00"], "FC72": ["F00"],\n'
    '    "FC73": ["F00"],                  /* 접속료수익 → 설비운영 */\n'
    '    "FC74": ["F00"],                  /* 도매제공수익 → 설비운영 */\n'
    '    "FC75": ["F00"],                  /* 내부거래수익 → 설비운영 */\n'
    '    "FC76": ["F00","F01"],            /* 장치비수익 → 설비운영/판매영업 */\n'
    '    "FC79": ["F00","F03"],            /* 기타영업수익 → 설비운영/일반관리 */\n'
    '    /* 원가·설비운영비용 → F00 */\n'
    '    "FC50": ["F00","F04"],            /* 인건비: 설비운영 or 네트워크운영 */\n'
    '    "FC51": ["F00"],                  /* 설비 경비 */\n'
    '    "FC52": ["F00"],                  /* 접속료비용 */\n'
    '    "FC53": ["F00"],                  /* 도매제공대가 */\n'
    '    "FC54": ["F00"],                  /* 내부거래비용 */\n'
    '    /* 판관비 → 기능 F01~F06 */\n'
    '    "FC60": ["F01","F02","F03","F04","F05","F06"],  /* 인건비: 어느 기능이든 가능 */\n'
    '    "FC61": ["F01","F02","F03","F04","F05","F06"],  /* 복리후생 */\n'
    '    "FC62": ["F00","F04"],            /* 감가상각비: 설비 or NW운영 */\n'
    '    "FC63": ["F00","F02","F03"],      /* 임차료: 설비/사업지원/일반관리 */\n'
    '    "FC64": ["F011"],                 /* 광고선전비 → F011 */\n'
    '    "FC65": ["F012"],                 /* 판매촉진비·판매활성화 장려금 → F012 */\n'
    '    "FC66": ["F01","F02","F03"],      /* 위탁수수료 */\n'
    '    "FC69": ["F02","F03"]             /* 기타 → 사업지원/일반관리 */\n'
    '  },\n'
    '\n'
    '  /* 전기통신사업 형태 접두어 — 사업외 역무(S501)와 결합 시 지적 대상 */\n'
    '  EA_FORMS: ["FC50","FC51","FC52","FC53","FC54","FC60","FC61","FC62","FC63","FC64","FC65","FC66"],\n'
    '\n'
    '  /* 공통성 기능 — 단일 역무 직귀속 시 근거 확인 필요 */\n'
    '  COMMON_FUNCS: ["F00","F02","F03","F06"],\n'
    '\n'
    '  /* 사업외 역무 */\n'
    '  NONBIZ_SVC: ["S501","F010"],\n'
    '\n'
    '  /* 더미·미매핑 역무 */\n'
    '  DUMMY_SVC: ["SZZZ","S000","Z120"],\n'
    '\n'
    '  MINORITY_SHARE: 0.10,\n'
    '  DOMINANT_SHARE: 0.70\n'
    '};'
)

if OLD_CFG in new_html:
    new_html = new_html.replace(OLD_CFG, NEW_CFG, 1)
    print('(8) P&L 매트릭스 CFG 교체 OK')
else:
    print('!! (8) DEFAULT_CFG 마커 못 찾음')

# ─────────── 12.5. R2 로직: 계정명 우선 매칭 (계정코드 fallback) ───────────
OLD_R2 = (
    '    /* R2 */\n'
    '    var allowed = prefixLookup(cfg.ACCT_FORM, acct);\n'
    '    if(allowed && form && !startsAny(form, allowed))\n'
    '      hits.R2.push({r:r, note:"계정 "+acct+(acctName?"("+acctName+")":"")+" 허용형태 ["+allowed.join(",")+"] ↔ 실제 "+form});'
)
NEW_R2 = (
    '    /* R2: 계정명 우선 매칭 (계정코드는 회사마다 다름) */\n'
    '    var allowed = null, matchedBy = "";\n'
    '    if (acctName && cfg.ACCT_NAME_FORM){\n'
    '      /* 긴 키워드부터 확인 (요금수익 > 수익) */\n'
    '      var kwSorted = Object.keys(cfg.ACCT_NAME_FORM).sort(function(a,b){return b.length-a.length;});\n'
    '      for (var kwi=0; kwi<kwSorted.length; kwi++){\n'
    '        if (acctName.indexOf(kwSorted[kwi]) >= 0){\n'
    '          allowed = cfg.ACCT_NAME_FORM[kwSorted[kwi]];\n'
    '          matchedBy = "계정명 키워드 [" + kwSorted[kwi] + "]";\n'
    '          break;\n'
    '        }\n'
    '      }\n'
    '    }\n'
    '    /* 계정명으로 못 잡히면 계정코드 접두어 backup */\n'
    '    if (!allowed){\n'
    '      allowed = prefixLookup(cfg.ACCT_FORM, acct);\n'
    '      if (allowed) matchedBy = "계정코드 [" + acct + "]";\n'
    '    }\n'
    '    if (allowed && form && !startsAny(form, allowed))\n'
    '      hits.R2.push({r:r, note: matchedBy + " 허용형태 ["+allowed.join(",")+"] ↔ 실제 "+form + (acctName?" ("+acctName+")":"")});'
)
if OLD_R2 in new_html:
    new_html = new_html.replace(OLD_R2, NEW_R2, 1)
    print('(9) R2 계정명 우선 매칭 로직 OK')
else:
    print('!! (9) R2 마커 못 찾음')

# ─────────── 13. RULE_META basis 문구를 P&L 맥락으로 수정 ───────────
new_html = new_html.replace(
    '{id:"R1", sev:"HIGH", name:"사업외 역무 × 전기통신설비", basis:"역무가 사업외(S501 등)인데 형태·기능이 전기통신설비(FC01~FC06)로 유지됨. 사업외 자산의 형태·기능 오분류는 2024년 회계전문위 시정명령 선례와 동일 패턴 — 사업외 실체(임대·매각·타용도) 및 코드 전환 여부 확인 필요."}',
    '{id:"R1", sev:"HIGH", name:"사업외 역무 × 전기통신사업 형태", basis:"역무가 사업외(S501 등)인데 형태가 전기통신사업 수익/비용(FC5·6 계열)로 유지됨. 사업외 거래의 형태·기능 오분류 — 실체(임대·매각·타용도 매출/비용) 확인. 회계분리기준 §5(사업 구분) 위반 후보."}', 1)
new_html = new_html.replace(
    '{id:"R2", sev:"HIGH", name:"계정결정 ↔ 형태코드 불일치 (재무회계 준용)", basis:"재무 계정(감사 확정)과 통신 형태코드의 연쇄 불일치. 해설서 §15: 비품 계정 → 지원자산 형태(B계열)만 가능, 설비 계정 → 전기통신설비 형태. 형태·기능만 정정하고 계정은 유지(재무회계 준용)."}',
    '{id:"R2", sev:"HIGH", name:"계정명 ↔ 형태코드 불일치 (재무회계 준용)", basis:"계정명(계정과목명)의 성격과 통신 형태코드의 연쇄 불일치. 계정코드는 회사마다 다르지만 계정명은 통상 명명 규칙을 따름 — \'요금수익\'→수익형태(FC7·), \'광고선전비\'→FC64, \'감가상각\'→FC62 등. 계정명 우선 매칭, 코드는 backup. 형태·기능만 정정하고 계정은 유지."}', 1)
new_html = new_html.replace(
    '{id:"R3", sev:"MED",  name:"형태코드 ↔ 기능코드 불일치", basis:"형태(설비 실체)와 기능(수행 기능)의 조합이 기준상 허용 조합을 벗어남. 예: 전송설비(FC0200)인데 기능이 전원(F0600). 회계기준 §13 기능분류 연쇄 위반 후보."}',
    '{id:"R3", sev:"MED",  name:"형태코드 ↔ 기능코드 불일치", basis:"형태(수익/비용 성격)와 기능(수행 기능)의 조합이 기준상 허용 조합을 벗어남. 예: 광고선전비 형태인데 기능이 설비운영(F00). §17 비용의 기능분류 연쇄 위반 후보."}', 1)
new_html = new_html.replace(
    '{id:"R4", sev:"INFO", name:"공통성 설비의 단일역무 직귀속", basis:"전송(기-교/교-교)·선로·전원 등 여러 역무가 공용하는 설비가 특정 역무에 100% 직귀속됨. 전용 설비라는 직귀속 근거(회선 전용성 등) 문서화 여부 확인."}',
    '{id:"R4", sev:"INFO", name:"공통성 비용의 단일역무 직귀속", basis:"설비운영(F00)·사업지원(F02)·일반관리(F03)·R&D(F06) 등 여러 역무 공용이 통상인 기능이 특정 역무에 100% 직귀속됨. 직귀속 근거(전용성) 문서화 여부 확인 — §16·§17 배부기준 위반 후보."}', 1)
new_html = new_html.replace(
    '{id:"R5", sev:"HIGH", name:"데이터 정합 이상", basis:"취득금액 0인데 상각·장부가 존재, 장부가>취득가, 비정상 음수 등. 대체증감·소급조정 이력 또는 원장 오류 → 건별 소명 필요."}',
    '{id:"R5", sev:"HIGH", name:"데이터 정합 이상", basis:"금액 0(더미·조정), 음수 금액(환입·취소·차감) 등 비정상 데이터. 원장 정합성 및 조정 이력 → 건별 소명 필요."}', 1)
new_html = new_html.replace(
    '{id:"R6", sev:"MED",  name:"동일 세분류 내 소수(대세 일탈) 조합", basis:"동일 자산세분류의 지배적 형태·기능 조합(70%↑)과 다른 소수(10%↓) 조합. \'동일 자재=동일 코드\' 일관성 원칙 위반 후보 — 분산 등록·오배정 여부 확인."}',
    '{id:"R6", sev:"MED",  name:"동일 계정 내 소수(대세 일탈) 조합", basis:"동일 계정의 지배적 형태·기능 조합(70%↑)과 다른 소수(10%↓) 조합. \'동일 계정=동일 성격\' 일관성 원칙 위반 후보 — 오분개·특수 거래(구분 필요) 여부 확인."}', 1)

# 검토 근거 하단 문구도 갱신
new_html = new_html.replace(
    '① 전기통신사업 회계분리기준 제13조(설비 기능분류)·제15조(지원기능/일반자산) 및 해설서(2026.4) — 계정·형태·기능 연쇄 일관성 ·\n'
    '    ② 회계전문위원회 2024-4차 결정 — 사업외 자산의 형태·기능 오분류 시정명령 선례 ·\n'
    '    ③ 전자표준지침서 — 표준 기능코드(F)·보고서 서비스코드(S) 체계 및 회사코드 매핑 제출 의무 ·\n'
    '    ④ 동일 자재/세분류 = 동일 코드 일관성 원칙',
    '① 전기통신사업 회계분리기준 제5조(사업 구분)·제16조(수익 배부)·제17조(비용 배부) 및 해설서(2026.4) — 계정·형태·기능 연쇄 일관성 ·\n'
    '    ② 회계전문위원회 결정 선례 — 판매활성화 장려금 배부(2024), 결합할인 표기(2024), 사업외 수익·비용 구분(2023) ·\n'
    '    ③ 전자표준지침서 — 표준 기능코드(F)·보고서 서비스코드(S) 체계 ·\n'
    '    ④ 동일 계정 = 동일 코드 일관성 원칙 (동일 계정 내 대세 일탈 감지)', 1)

# 룰 설정 JSON 안내 문구 갱신
new_html = new_html.replace(
    'ACCT_FORM: 계정결정(앞자리 매칭) → 허용 형태코드 접두어. FORM_FUNC: 형태코드 → 허용 기능코드 접두어.\n'
    '      EA_FORMS: 전기통신설비 형태 접두어. COMMON_FUNCS: 공통성 설비 기능(직귀속 시 확인 플래그). NONBIZ_SVC: 사업외 역무코드.',
    'ACCT_NAME_FORM: 계정명 키워드 → 허용 형태 접두어 (핵심 매칭 — 회사코드 무관).\n'
    '      ACCT_FORM: 계정코드 접두어 → 허용 형태 (계정명 매칭 실패 시 backup).\n'
    '      FORM_FUNC: 형태코드 → 허용 기능코드 접두어 (§17 비용의 기능분류).\n'
    '      EA_FORMS: 전기통신사업 형태 접두어. COMMON_FUNCS: 공통성 기능(직귀속 시 확인). NONBIZ_SVC: 사업외 역무.', 1)

# ─────────── 저장 ───────────
out_path = os.path.join(ROOT, '수익비용_자동검토_v1.html')
io.open(out_path, 'w', encoding='utf-8').write(new_html)
print('─' * 60)
print('산출: %s' % out_path)
print('크기: %.1f KB' % (os.path.getsize(out_path)/1024))
