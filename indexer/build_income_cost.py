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
    '  /* 계정명 키워드 → 허용 형태 접두어 (핵심 매칭 축)\n'
    '     구계정(음성통화수익-정액 등)과 신계정(무선전화_기본료 등) 모두 지원 */\n'
    '  ACCT_NAME_FORM: {\n'
    '    /* ─── MVNO 최우선 (도매제공수익) ─── */\n'
    '    "MVNO":                    ["FC74","FC70"],\n'
    '    /* ─── 접속료수익 (긴 키워드 우선) ─── */\n'
    '    "국제로밍접속료":          ["FC73"],\n'
    '    "지능망접속료":            ["FC73"],\n'
    '    "SMS접속료":               ["FC73"],\n'
    '    "시내접속료":              ["FC73"],\n'
    '    "시외접속료":              ["FC73"],\n'
    '    "국제접속료":              ["FC73"],\n'
    '    "기타접속료":              ["FC73"],\n'
    '    "유선접속료":              ["FC73"],\n'
    '    "무선접속료":              ["FC73"],\n'
    '    "망접속수익":              ["FC73"],\n'
    '    "이동망접속":              ["FC73"],\n'
    '    "시내망접속":              ["FC73"],\n'
    '    "국제망접속":              ["FC73"],\n'
    '    "기타망접속":              ["FC73"],\n'
    '    "접속료수익":              ["FC73"],\n'
    '    "상호접속":                ["FC73"],\n'
    '    "접속료":                  ["FC52","FC73"],\n'
    '    /* ─── 요금수익 (구계정) ─── */\n'
    '    "요금수익":                ["FC70","FC71","FC72"],\n'
    '    "기본료":                  ["FC70","FC71"],\n'
    '    "통화료":                  ["FC70","FC71"],\n'
    '    "음성통화수익":            ["FC70","FC71"],\n'
    '    "통화수익":                ["FC70","FC71"],\n'
    '    "Data통화수익":            ["FC70","FC72"],\n'
    '    "Data정보이용수익":        ["FC70","FC72"],\n'
    '    "Data정액":                ["FC70","FC72"],\n'
    '    "데이터수익":              ["FC70","FC72"],\n'
    '    "데이타":                  ["FC70","FC72"],\n'
    '    "부가서비스수익":          ["FC70","FC72"],\n'
    '    "부가서비스":              ["FC70","FC72"],\n'
    '    "폰메일":                  ["FC70","FC72"],\n'
    '    "컬러링":                  ["FC70","FC72"],\n'
    '    "정보료":                  ["FC70","FC72"],\n'
    '    "인터넷수익":              ["FC70","FC72"],\n'
    '    "디지털홈수익":            ["FC70","FC72"],\n'
    '    "로밍수익":                ["FC70","FC71"],\n'
    '    "로밍":                    ["FC70","FC71"],\n'
    '    "연체료수익":              ["FC70","FC79"],\n'
    '    "번호이동수수료":          ["FC70","FC79"],\n'
    '    "고객충성제도":            ["FC70"],\n'
    '    /* ─── 요금수익 (신계정 카테고리) ─── */\n'
    '    "국제이용료":              ["FC70","FC71"],\n'
    '    "시내이용료":              ["FC70","FC71"],\n'
    '    "시외이용료":              ["FC70","FC71"],\n'
    '    "LM이용료":                ["FC70","FC71"],\n'
    '    "지능망이용료":            ["FC70","FC71"],\n'
    '    "BIZ메시징이용료":         ["FC70","FC72"],\n'
    '    "메시징이용료":            ["FC70","FC72"],\n'
    '    "데이터(TRAFFIC)이용료":   ["FC70","FC72"],\n'
    '    "플랫폼이용료":            ["FC70","FC72"],\n'
    '    "콘텐츠이용료":            ["FC70","FC72"],\n'
    '    "부가서비스이용료":        ["FC70","FC72"],\n'
    '    "기타서비스이용료":        ["FC70","FC72"],\n'
    '    "서비스이용료":            ["FC70","FC72"],\n'
    '    "인터넷전용회선이용료":    ["FC70","FC72"],\n'
    '    "일반전용회선이용료":      ["FC70","FC72"],\n'
    '    "이용료":                  ["FC70","FC72"],\n'
    '    "통화서비스":              ["FC70","FC71"],\n'
    '    "로밍서비스":              ["FC70","FC71"],\n'
    '    "콘텐츠":                  ["FC70","FC72"],\n'
    '    "메시징":                  ["FC70","FC72"],\n'
    '    "데이터":                  ["FC70","FC72"],\n'
    '    "설치/이전료":             ["FC70","FC79"],\n'
    '    "설치료":                  ["FC70","FC79"],\n'
    '    "가입료":                  ["FC70","FC79"],\n'
    '    "장치료":                  ["FC70","FC76"],\n'
    '    "구축형":                  ["FC70","FC79"],\n'
    '    "WiBro":                   ["FC70","FC71"],\n'
    '    /* ─── 특수 계정 ─── */\n'
    '    "USF":                     ["FC70","FC79"],\n'
    '    "공중전화통화료차익":      ["FC70","FC79"],\n'
    '    /* ─── 조정/할인 (원 계정 형태 유지) ─── */\n'
    '    "포인트":                  ["FC70","FC71","FC72"],\n'
    '    /* ═══════════════════ 비 용 (COST) 계정 ═══════════════════ */\n'
    '    /* ─── 일반화 형태소 (회사별 접미사 차이 흡수: 임차료/임차비, 보험료/보험비 등) ─── */\n'
    '    "여비":                    ["FC69"],\n'
    '    "임차비":                  ["FC63"],\n'
    '    "임차":                    ["FC63"],\n'
    '    "렌탈":                    ["FC63"],\n'
    '    "전략매장임차비":          ["FC63"],\n'
    '    "수당":                    ["FC60"],\n'
    '    "급료":                    ["FC60"],\n'
    '    "계약급여":                ["FC60"],\n'
    '    "성과급":                  ["FC60"],\n'
    '    "직책":                    ["FC60"],\n'
    '    "역할급":                  ["FC60"],\n'
    '    "체제비":                  ["FC60","FC69"],\n'
    '    "보조비":                  ["FC61"],\n'
    '    "지원비":                  ["FC61","FC69"],\n'
    '    "의료비지원":              ["FC61"],\n'
    '    "교육비지원금":            ["FC61","FC69"],\n'
    '    "상조회비":                ["FC61"],\n'
    '    "상호부조":                ["FC61"],\n'
    '    "국민연금":                ["FC61"],\n'
    '    "건강보험":                ["FC61"],\n'
    '    "고용보험":                ["FC61"],\n'
    '    "산재보험":                ["FC61"],\n'
    '    "직장단체보험":            ["FC61"],\n'
    '    "복지후생":                ["FC61"],\n'
    '    "체육행사":                ["FC61"],\n'
    '    "야식비":                  ["FC61"],\n'
    '    "건강진단":                ["FC61"],\n'
    '    "의류비":                  ["FC61"],\n'
    '    "매칭그랜트":              ["FC61"],\n'
    '    "근로복지기금":            ["FC61"],\n'
    '    "기금출연금":              ["FC69"],\n'
    '    "기금":                    ["FC61","FC69"],\n'
    '    "보험비":                  ["FC69","FC61"],\n'
    '    "전력비":                  ["FC50","FC51","FC69"],\n'
    '    "연료비":                  ["FC50","FC69"],\n'
    '    "상하수도비":              ["FC50","FC69"],\n'
    '    "정산부담금":              ["FC52"],\n'
    '    "부담금":                  ["FC69","FC61"],\n'
    '    "접속비":                  ["FC52"],\n'
    '    "서비스구입비":            ["FC53"],\n'
    '    "콘텐츠구입비":            ["FC66"],\n'
    '    "상품구입비":              ["FC50","FC79"],\n'
    '    "획득수수료":              ["FC65"],\n'
    '    "획득판촉비":              ["FC65"],\n'
    '    "판매활동비":              ["FC65"],\n'
    '    "IT유지보수":              ["FC66"],\n'
    '    "개발위탁비":              ["FC66"],\n'
    '    "유지위탁비":              ["FC66"],\n'
    '    "용역수수료":              ["FC66"],\n'
    '    "용역비":                  ["FC66"],\n'
    '    "도급비":                  ["FC66"],\n'
    '    "자문":                    ["FC66"],\n'
    '    "수수료":                  ["FC66","FC69"],\n'
    '    "교육위탁":                ["FC69","FC66"],\n'
    '    "교육":                    ["FC69"],\n'
    '    "운영비":                  ["FC69"],\n'
    '    "택배":                    ["FC66","FC69"],\n'
    '    "운반비":                  ["FC66","FC69"],\n'
    '    "자료조사비":              ["FC69"],\n'
    '    "자료수집비":              ["FC69"],\n'
    '    "소송":                    ["FC69"],\n'
    '    "구독비":                  ["FC69"],\n'
    '    "용품비":                  ["FC69"],\n'
    '    "구입비":                  ["FC69"],\n'
    '    "점용":                    ["FC63","FC69"],\n'
    '    "발간비":                  ["FC69"],\n'
    '    "발송비":                  ["FC69"],\n'
    '    "활동비":                  ["FC69"],\n'
    '    "협력비":                  ["FC69"],\n'
    '    "피해보상":                ["FC69"],\n'
    '    "배상금":                  ["FC69"],\n'
    '    "면허세":                  ["FC69"],\n'
    '    "지역개발세":              ["FC69"],\n'
    '    "자동차세":                ["FC69"],\n'
    '    "가산세":                  ["FC69"],\n'
    '    "인지세":                  ["FC69"],\n'
    '    "등기비":                  ["FC69"],\n'
    '    "감정비":                  ["FC69"],\n'
    '    "세탁비":                  ["FC69"],\n'
    '    "보로금":                  ["FC69"],\n'
    '    "정비비":                  ["FC50","FC69"],\n'
    '    "가설비":                  ["FC50","FC51"],\n'
    '    "보전비":                  ["FC50","FC69"],\n'
    '    "품질개선비":              ["FC50","FC51"],\n'
    '    "물자비":                  ["FC50","FC69"],\n'
    '    "단말관리비":              ["FC50","FC69"],\n'
    '    "모뎀관리비":              ["FC50","FC69"],\n'
    '    "지식재산권":              ["FC69","FC66"],\n'
    '    "협회":                    ["FC69"],\n'
    '    "회비":                    ["FC69"],\n'
    '    "잡비":                    ["FC69"],\n'
    '    "차량":                    ["FC69"],\n'
    '    "가산금":                  ["FC60"],\n'
    '    "전파사용":                ["FC52","FC69"],\n'
    '    "인수공":                  ["FC50","FC51"],\n'
    '    /* ─── 접속료비용 (망접속) ─── */\n'
    '    "SMS비용":                 ["FC52"],\n'
    '    "이동망접속":              ["FC52","FC73"],\n'
    '    "망접속":                  ["FC52"],\n'
    '    "이동접속":                ["FC52"],\n'
    '    "보편적역무":              ["FC52"],\n'
    '    "전파사용료":              ["FC52","FC69"],\n'
    '    /* ─── 회선료 (도매제공대가/설비임차) ─── */\n'
    '    "회선료":                  ["FC53","FC63"],\n'
    '    "전용회선료":              ["FC53","FC63"],\n'
    '    /* ─── 인건비 (임원급여·기본급·수당·계약직·주식보상) ─── */\n'
    '    "임원급여":                ["FC60"],\n'
    '    "기본급":                  ["FC60"],\n'
    '    "특별상여금":              ["FC60"],\n'
    '    "초과근무수당":            ["FC60"],\n'
    '    "야간근무수당":            ["FC60"],\n'
    '    "휴일근무수당":            ["FC60"],\n'
    '    "연월차수당":              ["FC60"],\n'
    '    "기타수당":                ["FC60"],\n'
    '    "계약직급여":              ["FC60"],\n'
    '    "용역직인건비":            ["FC60","FC66"],\n'
    '    "주식보상비용":            ["FC60"],\n'
    '    "퇴직급여":                ["FC60"],\n'
    '    "장기근속":                ["FC60"],\n'
    '    /* ─── 복리후생 (법정지원금·일반복리·후생복리) ─── */\n'
    '    "급여성복리비":            ["FC61"],\n'
    '    "법정지원금":              ["FC61"],\n'
    '    "일반복리":                ["FC61"],\n'
    '    "후생복리":                ["FC61"],\n'
    '    "복지시설":                ["FC61"],\n'
    '    "특근자석식비":            ["FC61"],\n'
    '    "동적요소관리비":          ["FC61"],\n'
    '    /* ─── 감가상각 ─── */\n'
    '    "건물상각":                ["FC62"],\n'
    '    "기계장치상각":            ["FC62"],\n'
    '    "비품상각":                ["FC62"],\n'
    '    "소프트웨어상각":          ["FC62"],\n'
    '    "상각":                    ["FC62"],\n'
    '    "대손상각비":              ["FC69"],\n'
    '    /* ─── 임차료 ─── */\n'
    '    "기지국임차료":            ["FC63"],\n'
    '    "중계기임차료":            ["FC63"],\n'
    '    "사무실임차료":            ["FC63"],\n'
    '    "전산장비임차료":          ["FC63"],\n'
    '    "통신설비임차료":          ["FC63"],\n'
    '    "전주임차료":              ["FC63"],\n'
    '    "사무집기임차료":          ["FC63"],\n'
    '    "차량임차료":              ["FC63"],\n'
    '    "기타임차료":              ["FC63"],\n'
    '    "지하철점용료":            ["FC63"],\n'
    '    /* ─── 광고선전비 (매체·특수매체·사내방송) ─── */\n'
    '    "TV광고비":                ["FC64"],\n'
    '    "신문광고비":              ["FC64"],\n'
    '    "잡지광고비":              ["FC64"],\n'
    '    "협찬광고비":              ["FC64"],\n'
    '    "매체일반광고비":          ["FC64"],\n'
    '    "특수매체광고비":          ["FC64"],\n'
    '    "일반광고비":              ["FC64"],\n'
    '    "광고비":                  ["FC64"],\n'
    '    "사내방송제작비":          ["FC64"],\n'
    '    /* ─── 판매촉진비/판매활성화 (모집·유지·기변·계약획득원가) ─── */\n'
    '    "판촉행사비용":            ["FC65"],\n'
    '    "판촉물":                  ["FC65"],\n'
    '    "판촉비":                  ["FC65"],\n'
    '    "고객모집수수료":          ["FC65"],\n'
    '    "고객신규지원":            ["FC65"],\n'
    '    "고객유지수수료":          ["FC65"],\n'
    '    "고객기변수수료":          ["FC65"],\n'
    '    "고객기변지원":            ["FC65"],\n'
    '    "모집수수료":              ["FC65"],\n'
    '    "관리수수료":              ["FC65"],\n'
    '    "유지수수료":              ["FC65"],\n'
    '    "계약획득원가":            ["FC65"],\n'
    '    /* ─── 위탁수수료 (모집·관리·수납·금융·용역) ─── */\n'
    '    "위탁신규모집":            ["FC65","FC66"],\n'
    '    "위탁자동납부":            ["FC66"],\n'
    '    "위탁선불카드":            ["FC66"],\n'
    '    "위탁기타모집":            ["FC65","FC66"],\n'
    '    "위탁신규관리":            ["FC66"],\n'
    '    "위탁업무관리":            ["FC66"],\n'
    '    "위탁자국수납":            ["FC66"],\n'
    '    "위탁부대비용":            ["FC66"],\n'
    '    "위탁":                    ["FC66"],\n'
    '    "정보제공수수료":          ["FC66"],\n'
    '    "정보제공부대경비":        ["FC66"],\n'
    '    "공중전화수수료":          ["FC66"],\n'
    '    "ROAMING수수료":           ["FC66"],\n'
    '    "무선국검사수수료":        ["FC66"],\n'
    '    "채권추심위임수수료":      ["FC66"],\n'
    '    "카드결제수수료":          ["FC66"],\n'
    '    "자동납부수수료":          ["FC66"],\n'
    '    "GIRO수수료":              ["FC66"],\n'
    '    "금융수수료":              ["FC66"],\n'
    '    /* ─── 용역비 (O/S·연구·조사·외주) ─── */\n'
    '    "경영연구용역비":          ["FC66"],\n'
    '    "시장조사용역비":          ["FC66"],\n'
    '    "사옥관리용역비":          ["FC66"],\n'
    '    "IT O/S용역비":            ["FC66"],\n'
    '    "고객센터OS용역비":        ["FC66"],\n'
    '    "고객센터 O/S용역비":      ["FC66"],\n'
    '    "지점 O/S용역비":          ["FC66"],\n'
    '    "기지국O/S용역비":         ["FC66"],\n'
    '    "미납관리 O/S용역비":      ["FC66"],\n'
    '    "전용선 O/S 용역비":       ["FC66"],\n'
    '    "청구서발송O/S용역비":     ["FC66"],\n'
    '    "솔루션판매용역비":        ["FC66"],\n'
    '    "외주용역비":              ["FC66"],\n'
    '    "연구개발용역비":          ["FC66"],\n'
    '    "자문수수료":              ["FC66"],\n'
    '    "택배/운반료":             ["FC66"],\n'
    '    "일반수수료":              ["FC66"],\n'
    '    "부대경비":                ["FC69","FC66"],\n'
    '    /* ─── 수선비 (설비 → 매출원가, 사옥·집기 → 판관비) ─── */\n'
    '    "교환시설수선비":          ["FC50","FC51"],\n'
    '    "기지국수선비":            ["FC50","FC51"],\n'
    '    "중계기수선비":            ["FC50","FC51"],\n'
    '    "전송시설수선비":          ["FC50","FC51"],\n'
    '    "전산장비수선비":          ["FC50","FC51"],\n'
    '    "사옥수리비":              ["FC69"],\n'
    '    "사무집기수선비":          ["FC69"],\n'
    '    "수선비":                  ["FC50","FC51","FC69"],\n'
    '    /* ─── 자가사용 통신비 (판관비 or 제외) ─── */\n'
    '    "자가사용통신비":          ["FC69"],\n'
    '    "요금청구통신비":          ["FC69"],\n'
    '    "일반통신비":              ["FC69"],\n'
    '    /* ─── 수도광열·소모품 ─── */\n'
    '    "수도광열비":              ["FC50","FC51","FC69"],\n'
    '    "소모품비":                ["FC50","FC51","FC69"],\n'
    '    /* ─── 세금과공과 ─── */\n'
    '    "재산세":                  ["FC69"],\n'
    '    "종합부동산세":            ["FC69"],\n'
    '    "사업소세":                ["FC69"],\n'
    '    "협회비":                  ["FC69"],\n'
    '    "세금과공과":              ["FC69"],\n'
    '    /* ─── 차량비 ─── */\n'
    '    "차량유류대":              ["FC69"],\n'
    '    "차량제세공과":            ["FC69"],\n'
    '    "차량수선비":              ["FC69"],\n'
    '    "차량주차비":              ["FC69"],\n'
    '    "차량경비":                ["FC69"],\n'
    '    /* ─── 도서인쇄 ─── */\n'
    '    "도서구입비":              ["FC69"],\n'
    '    "간행물구독비":            ["FC69"],\n'
    '    "영업용인쇄비":            ["FC69"],\n'
    '    "사무용인쇄비":            ["FC69"],\n'
    '    /* ─── 보험료·피해보상 ─── */\n'
    '    "화재보험료":              ["FC69"],\n'
    '    "배상책임보험료":          ["FC69"],\n'
    '    "보험료":                  ["FC69"],\n'
    '    "피해보상비":              ["FC69"],\n'
    '    /* ─── 교육훈련·채용 ─── */\n'
    '    "국내교육훈련비":          ["FC69"],\n'
    '    "해외교육훈련비":          ["FC69"],\n'
    '    "교육훈련비":              ["FC69"],\n'
    '    "신규채용모집비":          ["FC69"],\n'
    '    /* ─── 여비교통 ─── */\n'
    '    "시내출장비":              ["FC69"],\n'
    '    "시외출장비":              ["FC69"],\n'
    '    "해외출장비":              ["FC69"],\n'
    '    "부임여비":                ["FC69"],\n'
    '    /* ─── 회의·업추·접대·경조 ─── */\n'
    '    "회의비":                  ["FC69"],\n'
    '    "업무추진비":              ["FC69"],\n'
    '    "노사협의비":              ["FC69"],\n'
    '    "경조사비":                ["FC69"],\n'
    '    "법인카드접대비":          ["FC69"],\n'
    '    "현금접대비":              ["FC69"],\n'
    '    "세금계산서접대비":        ["FC69"],\n'
    '    "계산서접대비":            ["FC69"],\n'
    '    "접대비":                  ["FC69"],\n'
    '    /* ─── 행사·포상·임원실·기타 판관비 ─── */\n'
    '    "사내행사비":              ["FC69"],\n'
    '    "포상비":                  ["FC69"],\n'
    '    "임원실유지비":            ["FC69"],\n'
    '    "조사분석비":              ["FC69","FC66"],\n'
    '    "정보이용료":              ["FC69","FC66"],\n'
    '    "Network비용":             ["FC50","FC51"],\n'
    '    /* ─── 스포츠단 (사업외 or 판촉) ─── */\n'
    '    "스포츠단":                ["FC79","FC65"],\n'
    '    /* ─── 매출원가 ─── */\n'
    '    "매출원가":                ["FC50","FC51"],\n'
    '    "배출원가":                ["FC50","FC51"],\n'
    '    "국내상품매출원가":        ["FC50","FC79"],\n'
    '    /* ═══════════════════ 이 하 수 익 (REVENUE) ═══════════════════ */\n'
    '    /* ─── 매출에누리·매출할인·수익조정·할증수익 (원 계정 차감/조정) ─── */\n'
    '    "매출에누리":              ["FC70","FC71","FC72"],\n'
    '    "매출할인":                ["FC70","FC71","FC72"],\n'
    '    "할인차금":                ["FC70","FC71","FC72"],\n'
    '    "수익조정":                ["FC70","FC71","FC72","FC79"],\n'
    '    "할증수익":                ["FC70","FC71","FC72"],\n'
    '    "할인":                    ["FC70","FC71","FC72"],\n'
    '    /* ─── 도매제공수익 ─── */\n'
    '    "도매제공수익":            ["FC74"],\n'
    '    "도매수익":                ["FC74"],\n'
    '    /* ─── 내부거래수익 ─── */\n'
    '    "내부거래수익":   ["FC75"],\n'
    '    /* ─── 임대수익 (회선설비·단말임대·부동산 등) ─── */\n'
    '    "회선설비임대":            ["FC76"],\n'
    '    "임대수익":                ["FC76","FC79"],\n'
    '    "장치비수익":              ["FC76"],\n'
    '    "단말기임대료":            ["FC76"],\n'
    '    "단말임대수익":            ["FC76"],\n'
    '    "임대료수익":              ["FC76"],\n'
    '    "임대료":                  ["FC76","FC79"],\n'
    '    "결합할인":                ["FC76"],\n'
    '    /* ─── 단말판매 (통신단말 판매 → 기타영업/사업외) ─── */\n'
    '    "단말기판매":              ["FC79"],\n'
    '    "단말판매":                ["FC79"],\n'
    '    /* ─── 기타영업수익 (구계정) ─── */\n'
    '    "광고수익":                ["FC79"],\n'
    '    "솔루션판매":              ["FC79"],\n'
    '    "판매대행수수료":          ["FC79"],\n'
    '    "Payment수수료":           ["FC79"],\n'
    '    "App.판매수수료":          ["FC79"],\n'
    '    "인증플랫폼수익":          ["FC79"],\n'
    '    "Hardware판매수익":        ["FC79"],\n'
    '    "위치정보수수료":          ["FC79"],\n'
    '    "스포츠단운영수익":        ["FC79"],\n'
    '    "국내상품매출":            ["FC79"],\n'
    '    "상품판매":                ["FC79"],\n'
    '    /* ─── 기타영업수익 (신계정) ─── */\n'
    '    "SI용역수익":              ["FC79"],\n'
    '    "IDC/CLoud":               ["FC79"],\n'
    '    "IDC":                     ["FC79"],\n'
    '    "수납대행수수료":          ["FC79"],\n'
    '    "부동산임대수익":          ["FC79","FC76"],\n'
    '    "관리비":                  ["FC79","FC69","FC50"],\n'
    '    "전기료":                  ["FC79"],\n'
    '    "전략매장":                ["FC79"],\n'
    '    "기타잡이익":              ["FC79"],\n'
    '    "기타영업수익":            ["FC79"],\n'
    '    "기타수익":                ["FC79"],\n'
    '    "기타":                    ["FC70","FC79","FC69"],\n'
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

# ─────────── 12.4. 미분류 계정 리포트 (회사 무관 자동화의 핵심) ───────────
UNMAPPED_FN = (
    '\n'
    '/* 미분류 계정 탐지: ACCT_NAME_FORM 키워드에 안 걸리는 계정명을 금액순으로 보고.\n'
    '   새 회사 원장 투입 시 커버리지 확인 → UI 룰 JSON에 키워드 몇 개만 추가하면 됨 */\n'
    'function findUnmappedAccounts(rows, map, cfg){\n'
    '  var uniq = {};\n'
    '  rows.forEach(function(r){\n'
    '    var an = map.acctName ? String(r[map.acctName]||"").trim() : "";\n'
    '    if(!an) return;\n'
    '    if(!uniq[an]) uniq[an] = {cnt:0, amt:0};\n'
    '    uniq[an].cnt++;\n'
    '    uniq[an].amt += Math.abs(map.amt?num(r[map.amt]):0);\n'
    '  });\n'
    '  var kws = Object.keys(cfg.ACCT_NAME_FORM||{});\n'
    '  var out = [];\n'
    '  Object.keys(uniq).forEach(function(an){\n'
    '    var clean = an.replace(/^\\(폐지\\)\\s*/, "");\n'
    '    var hit = null;\n'
    '    for(var i=0;i<kws.length;i++){ if(clean.indexOf(kws[i])>=0){hit=kws[i];break;} }\n'
    '    if(!hit) out.push({name:an, cnt:uniq[an].cnt, amt:uniq[an].amt});\n'
    '  });\n'
    '  out.sort(function(a,b){return b.amt-a.amt;});\n'
    '  return out;\n'
    '}\n'
)
marker_um = '/* ══════════════ 룰 엔진 ══════════════ */'
if marker_um in new_html:
    new_html = new_html.replace(marker_um, UNMAPPED_FN + '\n' + marker_um, 1)
    print('(10) 미분류 계정 탐지 함수 삽입 OK')
else:
    print('!! (10) 미분류 함수 마커 못 찾음')

# 미분류 리포트 렌더: R_GL 카드 계산부 직후에 삽입
UNMAPPED_RENDER = (
    '\n'
    '  /* ─── 미분류 계정 리포트 (커버리지 확인) ─── */\n'
    '  var unmapped = findUnmappedAccounts(DATA.rows, MAP, CFG);\n'
    '  LAST.unmapped = unmapped;\n'
    '  if (unmapped.length){\n'
    '    var umCard = document.createElement("div");\n'
    '    umCard.className = "rc MED";\n'
    '    umCard.innerHTML = "<span class=\'sev\'>MED</span><h3>R_UM. 미분류 계정</h3><div class=\'n\'>"+fmt(unmapped.length)+"<span style=\'font-size:12px\'> 계정</span></div><div class=\'m\'>키워드 사전에 없음 — 확인 필요</div>";\n'
    '    umCard.onclick = function(){ var t=el("sec_R_UM"); if(t) t.scrollIntoView({behavior:"smooth"}); };\n'
    '    cards.appendChild(umCard);\n'
    '  }\n'
)
marker_umr = '  /* R_GL 매칭 실행 (카드·섹션 공용) */'
if marker_umr in new_html:
    new_html = new_html.replace(marker_umr, UNMAPPED_RENDER + '\n' + marker_umr, 1)
    print('(11) 미분류 카드 삽입 OK')
else:
    print('!! (11) 미분류 카드 마커 못 찾음')

# 미분류 상세 섹션: R_GL 섹션 뒤에
UNMAPPED_SECTION = (
    '\n'
    '  /* ─── R_UM 미분류 계정 상세 ─── */\n'
    '  if (unmapped.length){\n'
    '    var umSec = document.createElement("div"); umSec.className="rulesec"; umSec.id="sec_R_UM";\n'
    '    var umHtml = "<h3><span class=\'pill MED\'>MED</span>R_UM. 미분류 계정 — "+fmt(unmapped.length)+"개</h3>";\n'
    '    umHtml += "<div class=\'basis\'>계정명이 ACCT_NAME_FORM 키워드 사전에 매칭되지 않아 R2(계정↔형태) 검증에서 제외된 계정입니다. "+\n'
    '      "새 회사 원장이라면 정상 — 아래 계정의 성격 키워드를 [룰 설정 JSON]의 ACCT_NAME_FORM에 추가하면 다음 실행부터 검증에 포함됩니다. "+\n'
    '      "금액이 큰 계정부터 추가하는 것이 효율적입니다.</div>";\n'
    '    var umLim = Math.min(unmapped.length, 100);\n'
    '    umHtml += "<div class=\'tblwrap\'><table><thead><tr><th>계정명</th><th>행수</th><th>금액 합계</th></tr></thead><tbody>";\n'
    '    for (var ui=0; ui<umLim; ui++){\n'
    '      var u = unmapped[ui];\n'
    '      umHtml += "<tr><td><b>"+esc(u.name)+"</b></td><td class=\'num\'>"+fmt(u.cnt)+"</td><td class=\'num\'>"+fmtEok(u.amt)+"</td></tr>";\n'
    '    }\n'
    '    umHtml += "</tbody></table></div>";\n'
    '    if (unmapped.length>umLim) umHtml += "<div class=\'stat\'>※ 화면에는 100개 — 전체는 엑셀 다운로드로 확인</div>";\n'
    '    umSec.innerHTML = umHtml;\n'
    '    out.appendChild(umSec);\n'
    '  }\n'
)
marker_ums = '    out.appendChild(glSec);\n  }\n'
if marker_ums in new_html:
    new_html = new_html.replace(marker_ums, '    out.appendChild(glSec);\n  }\n' + UNMAPPED_SECTION, 1)
    print('(12) 미분류 섹션 삽입 OK')
else:
    print('!! (12) 미분류 섹션 마커 못 찾음')

# 엑셀에 미분류 시트 추가
UNMAPPED_XLSX = (
    '\n'
    '  /* R_UM 미분류 계정 시트 */\n'
    '  if (LAST.unmapped && LAST.unmapped.length){\n'
    '    var umRows = [["계정명","행수","금액 합계"]];\n'
    '    LAST.unmapped.forEach(function(u){ umRows.push([u.name, u.cnt, u.amt]); });\n'
    '    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(umRows), "R_UM_미분류계정");\n'
    '  }\n'
)
marker_umx = '  /* R_GL 시트 */'
if marker_umx in new_html:
    new_html = new_html.replace(marker_umx, UNMAPPED_XLSX + '\n  /* R_GL 시트 */', 1)
    print('(13) 미분류 엑셀 시트 OK')
else:
    print('!! (13) 미분류 엑셀 마커 못 찾음')

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
    '    /* (폐지) 접두어 및 <XXX> 조정 표기 정리 */\n'
    '    var cleanName = (acctName||"").replace(/^\\(폐지\\)\\s*/, "");\n'
    '    if (cleanName && cfg.ACCT_NAME_FORM){\n'
    '      /* 긴 키워드 우선 매칭. 매출에누리·수익조정 등도 원 계정 형태 허용 */\n'
    '      var kwSorted = Object.keys(cfg.ACCT_NAME_FORM).sort(function(a,b){return b.length-a.length;});\n'
    '      for (var kwi=0; kwi<kwSorted.length; kwi++){\n'
    '        if (cleanName.indexOf(kwSorted[kwi]) >= 0){\n'
    '          allowed = cfg.ACCT_NAME_FORM[kwSorted[kwi]].slice();  /* 복사본 (원본 CFG 오염 방지) */\n'
    '          matchedBy = "계정명 키워드 [" + kwSorted[kwi] + "]";\n'
    '          break;\n'
    '        }\n'
    '      }\n'
    '      /* 특수: 계정명에 "MVNO" 포함 → 도매제공수익(FC74) 형태 자동 허용 */\n'
    '      if (allowed && cleanName.indexOf("MVNO") >= 0 && allowed.indexOf("FC74") < 0){\n'
    '        allowed.push("FC74");\n'
    '        matchedBy += " + MVNO(도매제공 허용)";\n'
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
