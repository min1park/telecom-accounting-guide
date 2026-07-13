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
    '  {key:"func",  label:"기능코드",       req:false, find:function(h){return /기능/.test(h) && !/명/.test(h);}},\n'
    '  {key:"funcName",label:"기능명",       req:false, find:function(h){return /기능명/.test(h);}},\n'
    '  {key:"svc",   label:"역무(서비스)코드",req:true, find:function(h){return (/역무/.test(h)&&!/명/.test(h)) || /서비스코드/.test(h);}},\n'
    '  {key:"svcName",label:"서비스명",      req:false, find:function(h){return /서비스명|역무명/.test(h);}},\n'
    '  {key:"desc",  label:"적요",            req:false, find:function(h){return /적요|내역|설명|비고|Description|memo/i.test(h);}},\n'
    '  {key:"bm",    label:"BM",              req:false, find:function(h){return /^BM|BM코드|사업단위|상품/i.test(h);}},\n'
    '  {key:"cc",    label:"코스트센터명(CC)", req:false, find:function(h){return /(코스트|Cost.?Center|부서|부문).*명/i.test(h) || /^CC명/i.test(h);}},\n'
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
    '        subclass: sc,\n'
    '        cnt: g.cnt, acq: g.acq,\n'
    '        acct: topN(g.accts)[0]||"", form: topN(g.forms)[0]||"", func: topN(g.funcs)[0]||"", svc: topN(g.svcs)[0]||"",\n'
    '        acctName: map.acctName?String(g.sample[map.acctName]||""):"",\n'
    '        formName: map.formName?String(g.sample[map.formName]||""):"",\n'
    '        funcName: map.funcName?String(g.sample[map.funcName]||""):"",\n'
    '        svcName:  map.svcName ?String(g.sample[map.svcName] ||""):"",\n'
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
    '    "소액결제":                ["FC79"],\n'
    '    "결제대행":                ["FC79"],\n'
    '    "대행":                    ["FC79","FC66"],\n'
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
    '  /* 형태코드가 회사 자체 체계일 때: 표준 형태코드 → 형태명 키워드로 대체 검사.\n'
    '     예: 허용형태 FC70인데 실제 코드가 FI1310이면, 형태명 "정액요금수익"에\n'
    '     "요금수익" 키워드가 있으므로 통과 (지적 안 함) */\n'
    '  FORM_NAME_KEYWORDS: {\n'
    '    "FC70": ["요금수익","기본료","통화","정액","이용료","데이터","부가","정보이용"],\n'
    '    "FC71": ["요금수익","기본료","통화","음성"],\n'
    '    "FC72": ["요금수익","데이터","정보이용","부가","콘텐츠","이용료"],\n'
    '    "FC73": ["접속"],\n'
    '    "FC74": ["도매","MVNO","재판매"],\n'
    '    "FC75": ["내부거래"],\n'
    '    "FC76": ["임대","장치","결합"],\n'
    '    "FC79": ["기타","잡이익"],\n'
    '    "FC50": ["운영","원가","설비","수선","전력","유지"],\n'
    '    "FC51": ["운영","경비","수선"],\n'
    '    "FC52": ["접속","정산","전파","분담"],\n'
    '    "FC53": ["도매","망이용","회선","구입"],\n'
    '    "FC54": ["내부거래"],\n'
    '    "FC60": ["인건","급여","급료","노무","수당","퇴직"],\n'
    '    "FC61": ["복리","후생"],\n'
    '    "FC62": ["감가","상각"],\n'
    '    "FC63": ["임차","렌탈","리스"],\n'
    '    "FC64": ["광고"],\n'
    '    "FC65": ["판촉","판매촉진","장려","지원","모집","획득","유지","마케팅"],\n'
    '    "FC66": ["수수료","위탁","용역","외주","도급"],\n'
    '    "FC69": ["기타","일반","경비","관리","세금","공과"]\n'
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
    '    if (allowed && form){\n'
    '      var _pass = startsAny(form, allowed);\n'
    '      /* 회사 자체 형태코드 체계(FI1310 등) 대응: 코드 불일치 시 형태명 키워드로 대체 검사 */\n'
    '      var _fn = get(r,"formName");\n'
    '      if(!_pass && _fn && cfg.FORM_NAME_KEYWORDS){\n'
    '        for(var _ai=0; _ai<allowed.length && !_pass; _ai++){\n'
    '          var _ks = cfg.FORM_NAME_KEYWORDS[allowed[_ai]] || [];\n'
    '          for(var _ki=0; _ki<_ks.length; _ki++){ if(_fn.indexOf(_ks[_ki])>=0){ _pass=true; break; } }\n'
    '        }\n'
    '      }\n'
    '      if(!_pass)\n'
    '        hits.R2.push({r:r, note: matchedBy + " 허용형태 ["+allowed.join(",")+"] ↔ 실제 "+form+(_fn?"("+_fn+")":"")+(acctName?" / "+acctName:"")});\n'
    '    }'
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

# ─────────── 14. R7: 매핑된 컬럼만 공란 검사 (기능코드 없는 수익원장 대응) ───────────
OLD_R7 = (
    '    /* R7 */\n'
    '    if(cfg.DUMMY_SVC.indexOf(svc)>=0 || svc==="" || func==="" || form==="")\n'
    '      hits.R7.push({r:r, note:"더미/공란 코드 (역무:"+(svc||"공란")+", 기능:"+(func||"공란")+", 형태:"+(form||"공란")+")"});'
)
NEW_R7 = (
    '    /* R7: 매핑된 컬럼만 공란 검사 — 기능코드 컬럼 자체가 없는 수익원장에서 전 행 오탐 방지 */\n'
    '    if(cfg.DUMMY_SVC.indexOf(svc)>=0 || (map.svc&&svc==="") || (map.func&&func==="") || (map.form&&form===""))\n'
    '      hits.R7.push({r:r, note:"더미/공란 코드 (역무:"+(svc||"공란")+", 기능:"+(map.func?(func||"공란"):"컬럼없음")+", 형태:"+(form||"공란")+")"});'
)
if OLD_R7 in new_html:
    new_html = new_html.replace(OLD_R7, NEW_R7, 1)
    print('(14) R7 공란 검사 조건 수정 OK')
else:
    print('!! (14) R7 마커 못 찾음')

# ─────────── 15. R_GL 매칭 캐시 (동일 태그 조합 재사용 — 대용량 성능) ───────────
OLD_GLLOOP = (
    '  var out = [];\n'
    '  Object.keys(groups).forEach(function(sc){\n'
    '    var g = groups[sc];\n'
    '    var tags = rowToTags(g.sample, map);\n'
    '    var top = matchGuidelines(tags, K);\n'
)
NEW_GLLOOP = (
    '  var out = [];\n'
    '  var _glCache = {};  /* 태그 시그니처 → 매칭 결과 캐시 (그룹 수천 개여도 유니크 태그 조합은 수십 개) */\n'
    '  Object.keys(groups).forEach(function(sc){\n'
    '    var g = groups[sc];\n'
    '    var tags = rowToTags(g.sample, map);\n'
    '    var _sig = JSON.stringify(tags);\n'
    '    var top = _glCache[_sig] || (_glCache[_sig] = matchGuidelines(tags, K));\n'
)
if OLD_GLLOOP in new_html:
    new_html = new_html.replace(OLD_GLLOOP, NEW_GLLOOP, 1)
    print('(15) R_GL 매칭 캐시 OK')
else:
    print('!! (15) R_GL 캐시 마커 못 찾음')

# ─────────── 16. 비동기 실행 (대용량에서 브라우저 멈춤 방지 + 진행 표시) ───────────
OLD_RUN = (
    'el("run").onclick=function(){\n'
    '  if(!DATA && el("paste").value.trim()){ var p=parseDelimited(el("paste").value); if(p){loadRows(p,"붙여넣기 데이터");return;} }\n'
    '  execute();\n'
    '};'
)
NEW_RUN = (
    'function runAsync(){\n'
    '  var btn = el("run");\n'
    '  btn.textContent = "검토 중... (수십만 행이면 1~2분)"; btn.disabled = true;\n'
    '  el("err").textContent = "";\n'
    '  setTimeout(function(){\n'
    '    try { execute(); }\n'
    '    catch(ex){ el("err").textContent = "실행 오류: " + ex.message; }\n'
    '    finally { btn.textContent = "검토 실행"; btn.disabled = false; }\n'
    '  }, 50);\n'
    '}\n'
    'el("run").onclick=function(){\n'
    '  if(!DATA && el("paste").value.trim()){ var p=parseDelimited(el("paste").value); if(p){loadRows(p,"붙여넣기 데이터");return;} }\n'
    '  runAsync();\n'
    '};'
)
if OLD_RUN in new_html:
    new_html = new_html.replace(OLD_RUN, NEW_RUN, 1)
    print('(16a) runAsync 정의·버튼 핸들러 OK')
else:
    print('!! (16a) run 핸들러 마커 못 찾음')

OLD_LOADEXEC = (
    '  renderMap();\n'
    '  el("mapcard").classList.remove("hide");\n'
    '  execute();\n'
    '}'
)
NEW_LOADEXEC = (
    '  renderMap();\n'
    '  el("mapcard").classList.remove("hide");\n'
    '  runAsync();\n'
    '}'
)
if OLD_LOADEXEC in new_html:
    new_html = new_html.replace(OLD_LOADEXEC, NEW_LOADEXEC, 1)
    print('(16b) loadRows 비동기 실행 OK')
else:
    print('!! (16b) loadRows 마커 못 찾음')

# ─────────── 17. 대용량 안내 문구 ───────────
new_html = new_html.replace(
    '.xlsx / .csv / .txt(탭구분)</b> — 자산원장(행단위) 또는 피벗 집계표 모두 가능',
    '.xlsx / .csv / .txt(탭구분)</b> — 수익·비용 원장(행단위) 또는 피벗 집계표 모두 가능'
    '<br><span style="font-size:11px;color:#889">※ 수십만 행 이상 대용량은 붙여넣기 대신 파일 업로드 필수 — .csv/.txt가 .xlsx보다 훨씬 빠릅니다</span>', 1)
print('(17) 대용량 안내 문구 OK')

# ─────────── 18. xlsx 다중 시트: 데이터 최다 시트 자동 선택 ───────────
OLD_SHEET = (
    '        var wb=XLSX.read(new Uint8Array(e.target.result),{type:"array"});\n'
    '        var ws=wb.Sheets[wb.SheetNames[0]];\n'
    '        var arr=XLSX.utils.sheet_to_json(ws,{header:1,raw:true,defval:""});\n'
    '        arr = arr.filter(function(r){return r.some(function(c){return c!=="";});});\n'
    '        if(arr.length<2){el("err").textContent="시트에 데이터가 없습니다.";return;}\n'
    '        var head=arr[0].map(function(h){return String(h).trim();});\n'
    '        var rows=arr.slice(1).map(function(r){ var o={}; head.forEach(function(h,i){o[h]=r[i];}); return o; });\n'
    '        loadRows({headers:head,rows:rows}, f.name+" ["+wb.SheetNames[0]+"]");'
)
NEW_SHEET = (
    '        var wb=XLSX.read(new Uint8Array(e.target.result),{type:"array"});\n'
    '        /* 첫 시트가 표지·빈 시트인 파일 대응: 데이터가 가장 많은 시트 자동 선택 */\n'
    '        var bestName=null, bestArr=null;\n'
    '        for(var si=0; si<wb.SheetNames.length; si++){\n'
    '          var arr0=XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[si]],{header:1,raw:true,defval:""});\n'
    '          arr0 = arr0.filter(function(r){return r.some(function(c){return c!=="";});});\n'
    '          if(arr0.length>=2 && (!bestArr || arr0.length>bestArr.length)){ bestName=wb.SheetNames[si]; bestArr=arr0; }\n'
    '        }\n'
    '        if(!bestArr){el("err").textContent="시트에 데이터가 없습니다. (파일 내 시트: "+wb.SheetNames.join(", ")+" — 모두 빈 시트이거나 머리글만 존재)";return;}\n'
    '        var arr=bestArr;\n'
    '        var head=arr[0].map(function(h){return String(h).trim();});\n'
    '        var rows=arr.slice(1).map(function(r){ var o={}; head.forEach(function(h,i){o[h]=r[i];}); return o; });\n'
    '        loadRows({headers:head,rows:rows}, f.name+" ["+bestName+"] (시트 "+wb.SheetNames.length+"개 중 자동선택)");'
)
if OLD_SHEET in new_html:
    new_html = new_html.replace(OLD_SHEET, NEW_SHEET, 1)
    print('(18) 다중 시트 자동 선택 OK')
else:
    print('!! (18) 시트 선택 마커 못 찾음')

# ─────────── 19. CSV 따옴표 파서 (엑셀 CSV의 "1,234,567" 금액 필드 대응) ───────────
OLD_PARSE = (
    'function parseDelimited(text){\n'
    '  var lines = text.replace(/\\r/g,"").split("\\n").filter(function(l){return l.trim()!=="";});\n'
    '  if(lines.length<2) return null;\n'
    '  var delim = lines[0].indexOf("\\t")>=0 ? "\\t" : ",";\n'
    '  var head = lines[0].split(delim).map(function(h){return h.trim();});\n'
    '  var rows = [];\n'
    '  for(var i=1;i<lines.length;i++){\n'
    '    var c = lines[i].split(delim);'
)
NEW_PARSE = (
    '/* 따옴표 인식 분할: 엑셀 CSV는 쉼표 포함 금액을 "1,234,567"로 감싸므로 단순 split 불가 */\n'
    'function splitCSV(line, delim){\n'
    '  if(delim==="\\t") return line.split("\\t");\n'
    '  if(line.indexOf(\'"\')<0) return line.split(delim);\n'
    '  var out=[], cur="", q=false;\n'
    '  for(var i=0;i<line.length;i++){\n'
    '    var ch=line[i];\n'
    '    if(q){\n'
    '      if(ch===\'"\'){ if(line[i+1]===\'"\'){cur+=\'"\';i++;} else q=false; }\n'
    '      else cur+=ch;\n'
    '    } else {\n'
    '      if(ch===\'"\') q=true;\n'
    '      else if(ch===delim){ out.push(cur); cur=""; }\n'
    '      else cur+=ch;\n'
    '    }\n'
    '  }\n'
    '  out.push(cur);\n'
    '  return out;\n'
    '}\n'
    'function parseDelimited(text){\n'
    '  var lines = text.replace(/\\r/g,"").split("\\n").filter(function(l){return l.trim()!=="";});\n'
    '  if(lines.length<2) return null;\n'
    '  var delim = lines[0].indexOf("\\t")>=0 ? "\\t" : ",";\n'
    '  var head = splitCSV(lines[0], delim).map(function(h){return h.trim();});\n'
    '  var rows = [];\n'
    '  for(var i=1;i<lines.length;i++){\n'
    '    var c = splitCSV(lines[i], delim);'
)
if OLD_PARSE in new_html:
    new_html = new_html.replace(OLD_PARSE, NEW_PARSE, 1)
    print('(19) CSV 따옴표 파서 OK')
else:
    print('!! (19) CSV 파서 마커 못 찾음')

# ─────────── 20. Ollama 로컬 AI 판정 브릿지 ───────────
# 판정 지식은 ollama_tag.py의 SYSTEM_KNOWLEDGE를 빌드 타임에 추출 (단일 소스)
import re as _re
_tag_src = io.open(os.path.join(ROOT, 'indexer', 'ollama_tag.py'), encoding='utf-8').read()
_system = _re.search(r'SYSTEM_KNOWLEDGE = """(.*?)"""', _tag_src, _re.DOTALL).group(1)
_system_js = json.dumps(_system, ensure_ascii=False)

BRIDGE_JS = r'''
/* ══════════════ Phase 4-3: Ollama 로컬 AI 판정 브릿지 ══════════════ */
var OLLAMA_URL = "http://localhost:11434/api/generate";
var AI_SYSTEM = __SYSTEM_JS__;
var AI_RUNNING = false, AI_STOP = false;

/* ── 서비스코드 참조표 (선택 입력) ──
   SVC_MASTER: 코드 → {name, layer(계층구분: 0=개별, 1~=공통풀), stdCode, stdName}
   SVC_ALLOC : 공통 풀 코드 → [{code,name}] 배부 대상 */
var SVC_MASTER = {}, SVC_ALLOC = {};
function parseSvcRef(){
  SVC_MASTER = {}; SVC_ALLOC = {};
  var t1 = el("svcmaster").value.trim(), t2 = el("svcalloc").value.trim();
  if(t1){ var p = parseDelimited(t1); if(p){
    var h = p.headers;
    var iC = -1, iN = -1, iL = -1, iS = -1, iSN = -1;
    h.forEach(function(x, i){
      if(/서비스코드/.test(x) && !/FROM|TO/i.test(x) && iC < 0) iC = i;
      if(/서비스명/.test(x) && !/FROM|TO|통신회계/i.test(x) && iN < 0) iN = i;
      if(/계층/.test(x) && iL < 0) iL = i;
      if(/보고서코드/.test(x) && iS < 0) iS = i;
      if(/통신회계서비스명/.test(x) && iSN < 0) iSN = i;
    });
    if(iC >= 0){ p.rows.forEach(function(r){
      var c = String(r[h[iC]]||"").trim(); if(!c) return;
      SVC_MASTER[c] = {name: iN>=0?String(r[h[iN]]||"").trim():"",
                       layer: iL>=0?(parseInt(String(r[h[iL]]||"0"),10)||0):0,
                       stdCode: iS>=0?String(r[h[iS]]||"").trim():"",
                       stdName: iSN>=0?String(r[h[iSN]]||"").trim():""};
    }); }
  }}
  if(t2){ var p2 = parseDelimited(t2); if(p2){
    var h2 = p2.headers;
    var iF = -1, iT = -1, iTN = -1;
    h2.forEach(function(x, i){
      if(/FROM/i.test(x) && /코드/.test(x) && iF < 0) iF = i;
      if(/TO/i.test(x) && /코드/.test(x) && iT < 0) iT = i;
      if(/TO/i.test(x) && /명/.test(x) && iTN < 0) iTN = i;
    });
    if(iF >= 0 && iT >= 0){ p2.rows.forEach(function(r){
      var f = String(r[h2[iF]]||"").trim(); if(!f) return;
      (SVC_ALLOC[f] = SVC_ALLOC[f] || []).push({code: String(r[h2[iT]]||"").trim(),
                                                name: iTN>=0?String(r[h2[iTN]]||"").trim():""});
    }); }
  }}
  var nM = Object.keys(SVC_MASTER).length, nA = Object.keys(SVC_ALLOC).length;
  el("svcinfo").textContent = (nM||nA) ? ("✓ 마스터 " + nM + "개 코드 · 배부관계 " + nA + "개 공통 풀 로드됨 — AI 판정에 반영됩니다") : "";
}

/* 결정론 룰 프리패스 — indexer/ollama_tag.py rule_pretag()와 동일 로직 (JS 포팅) */
function aiRulePretag(g){
  var acctName=g.acctName||g.acct||"", formName=g.formName||g.form||"";
  var svcName=g.svcName||"", svcCode=g.svc||"";
  var topDescs=(g.descTop||[]).join(" ");
  var m = SVC_MASTER[svcCode];
  /* 참조표 있으면 계층구분으로 공통 풀 확정 (이름 추측 대체) */
  if(m && m.layer > 0){
    var alloc = (SVC_ALLOC[svcCode]||[]).map(function(a){return a.name||a.code;}).join("·");
    var extra=(acctName.indexOf("매출에누리")>=0||acctName.indexOf("매출할인")>=0)?" (매출에누리 — 원 수익 형태 준용 여부도 함께)":"";
    return {tag:"배부확인",chk:"검토필요",svc:"검토필요",
            reason:"공통 풀("+svcCode+" "+svcName+", 계층"+m.layer+") — 배부 대상: "+(alloc||"배부관계 미등록")+" — 기말 배부 완결 확인"+extra+" [룰]"};
  }
  if(m && m.name.indexOf("더미")>=0){
    return {tag:"판단불가",chk:"검토필요",svc:"검토필요",reason:"더미 서비스코드("+svcCode+") — 서비스 매핑 정비 필요 [룰]"};
  }
  if(!m && (/^S9/.test(svcCode) || svcName.indexOf("공통")>=0)){
    var extra2=(acctName.indexOf("매출에누리")>=0||acctName.indexOf("매출할인")>=0)?" (매출에누리 — 원 수익 형태 준용 여부도 함께)":"";
    return {tag:"배부확인",chk:"검토필요",svc:"검토필요",reason:"공통역무("+svcCode+" "+svcName+") 계상 — 세대·역무별 배부 완결 확인 필요"+extra2+" [룰]"};
  }
  if((acctName+topDescs).indexOf("로밍")>=0){
    var low=(acctName+" "+topDescs).toLowerCase();
    if(low.indexOf("아웃바운드")>=0||low.indexOf("outbound")>=0||low.indexOf("해외로밍")>=0)
      return {tag:"로밍",chk:(formName.indexOf("기타요금")>=0?"적정":"검토필요"),reason:"OutBound 로밍은 기타요금수익 형태 (FY2020·2024) — 현재 "+formName+" [룰]"};
    if(low.indexOf("인바운드")>=0||low.indexOf("inbound")>=0)
      return {tag:"로밍",chk:(formName.indexOf("정액")>=0?"적정":"검토필요"),reason:"InBound 로밍은 정액요금수익 형태 (FY2021 지적) — 현재 "+formName+" [룰]"};
    return {tag:"로밍",chk:"검토필요",reason:"로밍 — In/Outbound 방향별 형태 상이 (Out→기타요금, In→정액) 방향 확인 필요 [룰]"};
  }
  if(acctName.indexOf("매출에누리")>=0||acctName.indexOf("매출할인")>=0)
    return {tag:"매출에누리",chk:"적정",reason:"원 수익의 차감 계정 — 원 수익과 동일 형태("+formName+") 준용은 적정 [룰]"};
  if(topDescs.indexOf("조정전표")>=0)
    return {tag:"조정전표",chk:"검토필요",reason:"결산 조정전표 — 원거래 형태 준용 여부 근거 전표 소명 필요 [룰]"};
  if(topDescs.indexOf("낙전")>=0)
    return {tag:"낙전",chk:(formName.indexOf("기타영업")>=0?"적정":"검토필요"),reason:"낙전수입은 기타영업수익 형태가 적정 (FY2013 자문단) — 현재 "+formName+" [룰]"};
  var both=acctName+" "+topDescs;
  if(both.indexOf("위약금")>=0){
    if(/단말|모뎀|AP|셋탑|장비|공유기/.test(both))
      return {tag:"해지위약금",chk:(formName.indexOf("장치")>=0?"적정":"검토필요"),reason:"단말·장치 관련 위약금은 장치비수익 (FY2023·2024 지적) — 현재 "+formName+" [룰]"};
    return {tag:"해지위약금",chk:(formName.indexOf("기타요금")>=0?"적정":"검토필요"),reason:"요금할인 해지위약금은 기타요금수익 (FY2016·2019·2021 지적) — 현재 "+formName+" [룰]"};
  }
  if(both.indexOf("연체")>=0)
    return {tag:"연체료",chk:(formName.indexOf("기타영업")>=0?"적정":"검토필요"),reason:"연체료·연체가산금은 기타영업수익 (FY2015·2016·2020 지적) — 현재 "+formName+" [룰]"};
  if(topDescs.indexOf("임대폰")>=0||(topDescs.indexOf("임대")>=0&&formName.indexOf("장치")>=0))
    return {tag:"장치임대",chk:(formName.indexOf("장치")>=0?"적정":"검토필요"),reason:"장치 임대 사용료는 장치비수익 형태가 적정 (FY2022 지적) — 현재 "+formName+" [룰]"};
  return null;
}

/* 계정↔역무 계열 정합 (참조표 제공 시, 결정론) — LLM svc_check 오판 보완 */
function svcConsistencyCheck(g){
  var m=SVC_MASTER[g.svc]; if(!m||m.layer>0||!m.stdName) return null;
  var an=g.acctName||"";
  var fam=null, famName="";
  if(/인터넷|초고속|IPTV|백본/.test(an)){ fam=/인터넷/; famName="인터넷 계열"; }
  else if(/시내|시외|유선전화/.test(an)){ fam=/전화/; famName="전화 계열"; }
  else if(/이동전화|무선전화/.test(an)){ fam=/이동통신/; famName="이동통신 계열"; }
  else if(/회선설비|전용회선/.test(an)){ fam=/회선|전용/; famName="회선설비 계열"; }
  if(!fam) return null;
  if(!fam.test(m.stdName))
    return "계정("+an+")은 "+famName+" 실질이나 역무 표준분류는 '"+m.stdName+"' — 역무 재확인 필요 [룰]";
  return null;
}

async function aiJudgeAll(){
  if(!LAST||!LAST.glResults||!LAST.glResults.length){ el("err").textContent="먼저 [검토 실행]을 하세요."; return; }
  var btn=el("aijudge");
  if(AI_RUNNING){ AI_STOP=true; btn.textContent="중단 중..."; return; }
  var model=(el("aimodel").value||"qwen3:8b").trim();
  AI_RUNNING=true; AI_STOP=false; btn.textContent="중단";
  var groups=LAST.glResults, results=LAST.aiResults||{};
  LAST.aiResults=results;
  var info=el("aiinfo"), t0=Date.now(), ruleCnt=0, llmCnt=0, errCnt=0;
  for(var i=0;i<groups.length;i++){
    if(AI_STOP) break;
    var g=groups[i];
    if(results[g.subclass] && results[g.subclass].tag!=="오류"){ continue; } /* 재실행 시 기존 결과 유지 */
    var pre=aiRulePretag(g);
    if(pre){ results[g.subclass]=pre; ruleCnt++; }
    else{
      var svcCtx="";
      var sm=SVC_MASTER[g.svc];
      if(sm){ svcCtx="\n서비스 계층: "+(sm.layer>0
          ? ("공통 풀(계층"+sm.layer+"), 배부 대상: "+((SVC_ALLOC[g.svc]||[]).map(function(a){return a.name||a.code;}).join("·")||"미등록"))
          : ("개별 서비스, 통신회계 표준 "+sm.stdCode+" "+sm.stdName)); }
      /* RAG: R_GL이 이미 찾아둔 관련 가이드라인 조항 top-3의 제목·결론 주입 */
      var ragCtx="";
      if(g.matches&&g.matches.length){
        var refs=g.matches.slice(0,3).map(function(mm,ri){
          var e2=mm.entry, concl=(e2.conclusions&&e2.conclusions[0])?(" "+e2.conclusions[0].substring(0,90)):(e2.excerpt?(" "+e2.excerpt.substring(0,90)):"");
          return (ri+1)+") ["+e2.category.substring(0,10)+" "+e2.year+"] "+e2.title.substring(0,45)+concl;
        }).join("\n");
        ragCtx="\n관련 가이드라인 조항(참고):\n"+refs;
      }
      var funcLine=(g.funcName||"")?("\n기능명: "+g.funcName+((g.ccTop&&g.ccTop[0])?(" / 코스트센터: "+g.ccTop[0]):"")):"";
      var prompt="계정명: "+(g.acctName||g.acct)+"\n형태명: "+(g.formName||g.form)+funcLine+"\n역무: "+(g.svcName||"")+"("+g.svc+")"+svcCtx+"\n행수: "+g.cnt+", 금액합계: "+fmt(Math.round(g.acq))+"원\n적요(대표): "+((g.descTop||[]).join(" / ")||"(없음)")+"\n거래처(대표): "+((g.vendorTop||[]).join(" / ")||"(없음)")+ragCtx+"\n이 그룹의 실질을 태깅하고 형태 분류 적정성"+(svcCtx?"과 역무 적정성":"")+(funcLine?"과 기능 적정성":"")+"을 판단하라.";
      try{
        var resp=await fetch(OLLAMA_URL,{method:"POST",headers:{"Content-Type":"application/json"},
          body:JSON.stringify({model:model,prompt:prompt,system:AI_SYSTEM,stream:false,format:"json",think:false,
                               options:{temperature:0.1,num_predict:220}})});
        if(!resp.ok) throw new Error("HTTP "+resp.status);
        var data=await resp.json();
        var j=JSON.parse(data.response||"{}");
        results[g.subclass]={tag:j.tag||"판단불가",chk:j.form_check||"판단불가",func:(funcLine?(j.func_check||"정보없음"):"정보없음"),svc:(svcCtx?(j.svc_check||"정보없음"):"정보없음"),reason:(j.reason||"")+" [LLM]"};
        llmCnt++;
      }catch(ex){
        errCnt++;
        results[g.subclass]={tag:"오류",chk:"오류",reason:String(ex.message||ex)};
        if(String(ex).indexOf("fetch")>=0||String(ex).indexOf("Network")>=0){
          el("err").textContent="Ollama 연결 실패 — Ollama 실행 여부를 확인하세요. (트레이에 Ollama 아이콘이 없으면 시작 메뉴에서 Ollama 실행)";
          break;
        }
      }
    }
    /* 결정론 역무 정합 오버레이 — LLM svc_check 오판을 룰이 정정 */
    var _r=results[g.subclass];
    if(_r && _r.tag!=="오류"){
      var _sc=svcConsistencyCheck(g);
      if(_sc){ _r.svc="검토필요"; _r.reason=(_r.reason||"")+" / "+_sc; }
      var _fc=ccFuncCheck(g);
      if(_fc){ _r.func="검토필요"; _r.reason=(_r.reason||"")+" / "+_fc; }
    }
    info.textContent="AI 판정 "+(i+1)+"/"+groups.length+" — 룰 "+ruleCnt+" · LLM "+llmCnt+(errCnt?" · 오류 "+errCnt:"")+" ("+Math.round((Date.now()-t0)/1000)+"초)";
  }
  AI_RUNNING=false; btn.textContent="AI 판정 실행 (로컬)";
  renderAIResults();
}

/* 코스트센터↔기능 계열 정합 (결정론) — 비용 원장의 핵심 축 */
function ccFuncCheck(g){
  var fn=g.funcName||""; if(!fn) return null;
  var cc=(g.ccTop&&g.ccTop[0])||""; if(!cc) return null;
  if(/결산조정|본사공통|조정/.test(cc)) return null; /* 결산조정 CC는 실부서 아님 */
  var fam=null, famName="";
  if(/마케팅|영업|판매|유통|대리점/.test(cc)){ fam=/판매|영업|광고|판촉|마케팅/; famName="판매영업"; }
  else if(/회계|재무|인사|총무|법무|경영|기획|감사|IR/.test(cc)){ fam=/일반관리|지원/; famName="일반관리"; }
  else if(/Infra|인프라|네트워크|NW|기지국|전송|선로|교환|운용|장비|Access/i.test(cc)){ fam=/설비|운영|사용료|네트워크|NW|선로|전송|교환/i; famName="설비운영"; }
  else if(/고객센터|고객서비스|CS팀|콜센터|상담/.test(cc)){ fam=/고객/; famName="고객서비스"; }
  else if(/연구|개발|R&D/i.test(cc)){ fam=/연구|개발/; famName="연구개발"; }
  if(!fam) return null;
  if(!fam.test(fn))
    return "코스트센터("+cc+")의 주된 업무는 "+famName+" 계열이나 기능은 '"+fn+"' — 기능 분류 확인 필요 (고시 제17·18조) [룰]";
  return null;
}

/* ══════════════ AI 질의 (로컬 Ollama + 지식베이스 RAG) ══════════════ */
var QA_SYSTEM = "당신은 전기통신사업 회계분리기준(과기정통부 고시)·해설서·회계전문위원회 결정에 정통한 회계법인 외부검증인이다.\n"
  + "사용자의 질문에 한국어로 간결하고 정확하게 답하라.\n\n"
  + "## 확립된 핵심 지식 (최우선 근거)\n" + __QA_KNOWLEDGE__ + "\n"
  + "- 공통역무 풀: 원장 단계 계상은 허용되나 ① 개별 역무로 특정 가능한 수익을 공통에 두면 지적(FY2020 지적: 5G 멤버십 비용을 전체 공통 분류) ② 기말까지 미배부 잔존 시 역무별 손익 왜곡으로 지적 ③ 공통이 정당하면 매출액 비율 등 합리적 배부기준을 회계분리지침서에 명시하고 배부하여야 함(FY2013 자문단). 최종 영업보고서에는 공통(서비스공통미배부)이 남으면 안 됨.\n\n"
  + "## 답변 규칙\n"
  + "- 위 핵심 지식과 '관련 조항' 발췌를 근거로 답하고, 연도를 인용하라 (예: FY2020 지적사항).\n"
  + "- 관련 조항이 질문과 무관해 보이면 억지로 인용하지 말고 핵심 지식·일반 원칙으로만 답하라.\n"
  + "- 확실하지 않으면 단정하지 말고 확인이 필요하다고 답하라.\n"
  + "- 답변은 10문장 이내.";

function textToTags(text){
  var tags = {asset:{}, function:{}, service:{}, revenue:{}, cost:{}};
  ["asset","function","service","revenue","cost"].forEach(function(cat){
    var dict = STD_TERMS[cat] || {};
    Object.keys(dict).forEach(function(std){
      if(std.charAt(0) === "_") return;
      var entry = dict[std];
      var aliases = entry.aliases || [];
      for(var i=0;i<aliases.length;i++){
        if(aliases[i] && text.indexOf(aliases[i]) >= 0){ tags[cat][entry.code] = std; break; }
      }
    });
  });
  return tags;
}

function searchGuidelinesByText(text, K){
  K = K || 5;
  var tags = textToTags(text);
  /* 질문 토큰(2자 이상) — 제목 직접 매칭 보너스 */
  var tokens = text.split(/[\s,.?!·()\[\]"']+/).filter(function(t){return t.length >= 2;});
  /* 조문 번호 패턴 — 조사 무관 매칭 ("제9조는" → "제9조") */
  var _arts = text.match(/제\d+조(?:의\d+)?/g);
  if(_arts){ for(var _ai2=0;_ai2<_arts.length;_ai2++) tokens.push(_arts[_ai2]); }
  var out = [];
  for(var i=0;i<GL_INDEX.entries.length;i++){
    var e = GL_INDEX.entries[i];
    var s = scoreEntry(tags, e);
    var score = s.score;
    for(var ti=0;ti<tokens.length;ti++){
      if(e.title.indexOf(tokens[ti]) >= 0)
        score += (_arts && _arts.indexOf(tokens[ti]) >= 0) ? 15 : 4;
    }
    if(score > 0) out.push({entry:e, score:score});
  }
  out.sort(function(a,b){return b.score - a.score;});
  return out.slice(0, K);
}

async function askAI(){
  var q = el("aiq").value.trim();
  if(!q){ el("aiqout").textContent = "질문을 입력하세요."; return; }
  var btn = el("aiqbtn"); btn.disabled = true; btn.textContent = "답변 생성 중...";
  el("aiqout").innerHTML = "<span style='color:#889'>지식베이스 검색 중...</span>";
  try{
    /* 저신뢰 검색 결과 차단 — 무관 조항의 억지 인용 방지 (태그+제목 결합 점수 8 미만 제외) */
    var refs = searchGuidelinesByText(q, 5).filter(function(m){ return m.score >= 8; });
    var refTxt = refs.map(function(m,i){
      var e2 = m.entry;
      var concl = (e2.conclusions && e2.conclusions[0]) ? ("\n" + e2.conclusions[0].substring(0,150)) : (e2.excerpt?("\n"+e2.excerpt.substring(0,150)):"");
      return (i+1) + ") [" + e2.category + " " + e2.year + "] " + e2.title.substring(0,60) + concl;
    }).join("\n");
    var prompt = "질문: " + q + "\n\n관련 조항(지식베이스 검색 결과):\n" + (refTxt || "(신뢰도 있는 매칭 없음 — 핵심 지식과 일반 원칙으로만 답하고, 조항을 지어내지 말 것)") + "\n\n위 근거를 바탕으로 답하라.";
    el("aiqout").innerHTML = "<span style='color:#889'>로컬 AI 답변 생성 중... (수십 초)</span>";
    var model = (el("aimodel") ? el("aimodel").value : "qwen3:8b").trim() || "qwen3:8b";
    var resp = await fetch(OLLAMA_URL, {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({model:model, prompt:prompt, system:QA_SYSTEM, stream:false, think:false,
                            options:{temperature:0.2, num_predict:600}})});
    if(!resp.ok) throw new Error("HTTP " + resp.status);
    var data = await resp.json();
    var ansHtml = "<div style='padding:10px 12px;background:#F5F8FA;border-left:3px solid var(--navy);border-radius:0 4px 4px 0;white-space:pre-wrap;line-height:1.7'>" + esc(data.response || "(응답 없음)") + "</div>";
    if(refs.length){
      ansHtml += "<div style='margin-top:8px;font-size:11px;color:#667'><b>참고한 조항:</b><br>" + refs.map(function(m){
        var e2 = m.entry;
        return "· [" + esc(e2.category) + " " + esc(e2.year) + "] " + esc(e2.title.substring(0,60)) + " <span style='color:#99A'>(" + esc(e2.source_pdf || "") + ")</span>";
      }).join("<br>") + "</div>";
    }
    ansHtml += "<div style='margin-top:6px;font-size:10px;color:#A96A1E'>※ 로컬 8B 모델의 초안 답변입니다 — 중요한 판단은 원문 조항·검증인 확인을 거치세요.</div>";
    el("aiqout").innerHTML = ansHtml;
  }catch(ex){
    el("aiqout").innerHTML = "<span style='color:#C0504D'>오류: " + esc(ex.message||String(ex)) + " — Ollama 실행 여부를 확인하세요.</span>";
  }
  btn.disabled = false; btn.textContent = "질문하기";
}

/* ══════════════ 조서(지적사항 초안) 생성 — 검토필요 그룹만 ══════════════ */
var REG = {
  IFRS15: "전기통신사업 회계정리 및 보고에 관한 규정 제4조제1항제3호\n제4조(전기통신사업회계의 원칙) ① 전기통신사업의 회계정리는 다음 각 호의 원칙을 따라야 한다.\n3. 이 영에서 회계정리에 관하여 정하는 사항 외에는 일반적으로 공정·타당하다고 인정되는 회계기준에 따를 것\n\n▽ 참고\nFY2019_표준계정_사업자메뉴얼 4. IFRS15호조정전표(통신회계 제외)\nK-IFRS1115호 조정전표를 분리 표시해야 함",
  FORM: "전기통신사업 회계분리기준(과학기술정보통신부고시) 제9조(영업수익 및 영업비용의 형태별분류)\n영업수익 및 영업비용은 이용약관 등 거래의 성격에 따라 형태별로 분류하여야 함",
  FUNC: "전기통신사업 회계분리기준(과학기술정보통신부고시) 제17조(전기통신영업비용의 기능별 분류)·제18조(비용 및 자산의 기능별 분류기준)\n비용은 발생 원인이 되는 기능별로 분류하여야 함",
  SVC: "전기통신사업 회계분리기준(과학기술정보통신부고시) 제22조(비용 및 자산의 역무별 회계분리 기준)\n수익·비용은 발생 원인이 되는 역무별로 회계분리하여야 함",
  ALLOC: "전기통신사업 회계분리기준(과학기술정보통신부고시) 제19조(공통자산 및 공통운영비의 배부)·제22조(비용 및 자산의 역무별 회계분리 기준)\n공통으로 발생한 수익·비용은 합리적인 배부기준에 따라 역무별로 배부하여야 함",
};

/* 조서 대상(검토필요) 그룹 — 조서·RAW 시트가 같은 번호 체계 공유 */
function getJoseoTargets(){
  if(!LAST||!LAST.aiResults||!LAST.glResults) return [];
  return LAST.glResults.filter(function(g){
    var r=LAST.aiResults[g.subclass];
    return r && (r.chk==="검토필요"||r.svc==="검토필요"||r.func==="검토필요");
  }).sort(function(a,b){return Math.abs(b.acq)-Math.abs(a.acq);});
}

function buildJoseoRows(){
  var judged=getJoseoTargets();
  if(!judged.length) return [];
  var rows=[["No","최종 지적사항","위반내용 및 의견","위반규정","근거","비고(판정출처)"]];
  judged.forEach(function(g, gi){
    var r=LAST.aiResults[g.subclass];
    var loc=(g.acctName||g.acct)+" × "+(g.formName||g.form)+" × "+(g.svcName||g.svc)
            +" ("+fmt(g.cnt)+"행, "+fmtEok(g.acq)+")";
    var title="", viol="", opin="", reg="";
    if(r.tag==="조정전표"){
      title="(기타) 결산 조정전표의 통신회계 반영 적정성\n\n"+loc+"\n결산 조정전표가 영업보고서에 반영되어 있으나, K-IFRS1115호에 따른 수익 이연 등 발생주의 조정 전표는 통신회계에서 제외하여야 함";
      viol="결산 조정전표의 원거래 형태 준용 여부 및 K-IFRS1115호 조정(통신회계 제외 대상) 해당 여부가 확인되지 아니함";
      opin="조정전표의 성격을 확인하여, K-IFRS1115호에 따른 수익 이연 등 발생주의 조정 전표는 표준계정코드(P9010 등) 분류를 통해 통신회계에서 제외하고, 그 외 조정은 원거래의 형태를 준용하여 분류하여야 합니다.";
      reg=REG.IFRS15;
    } else if(r.tag==="배부확인"){
      title="(역무분류) 공통역무 풀 수익의 기말 배부 완결성\n\n"+loc+"\n공통역무 풀에 수익이 계상되어 있어 역무별 배부 완결 여부의 확인이 필요함";
      viol="공통역무 풀 계상 수익의 기말 역무별 배부·소거 여부가 확인되지 아니함"+((r.reason.indexOf("배부 대상")>=0)?(" ("+r.reason.split("—")[1].trim().split("[")[0].trim()+")"):"");
      opin="공통 풀 잔액은 등록된 배부관계에 따라 개별 역무로 배부·소거되어야 하며, 미배부 잔액은 역무별 손익을 왜곡하므로 배부 완결 증빙을 확인하여야 합니다.";
      reg=REG.ALLOC;
    } else {
      var isForm=(r.chk==="검토필요"), isSvc=(r.svc==="검토필요"), isFunc=(r.func==="검토필요");
      var axes=[]; if(isForm)axes.push("형태분류"); if(isFunc)axes.push("기능분류"); if(isSvc)axes.push("역무분류");
      title="("+(axes.join("·")||"분류")+") "+r.tag+" 관련 분류 적정성\n\n"+loc;
      viol=r.reason.replace(/\s*\[(룰|LLM)\]\s*/g,"");
      opin="상기 항목의 거래 실질을 확인하여 "+(axes.join(" 및 ")||"분류")+"의 적정성을 소명하거나 재분류하여야 합니다.";
      var regs=[]; if(isForm)regs.push(REG.FORM); if(isFunc)regs.push(REG.FUNC); if(isSvc)regs.push(REG.SVC);
      reg=regs.join("\n\n");
    }
    /* 근거: R_GL 매칭 선례 top-3 자동 인용 */
    var basis=(g.matches||[]).slice(0,3).map(function(m,i){
      var e2=m.entry;
      var concl=(e2.conclusions&&e2.conclusions[0])?("\n"+e2.conclusions[0].substring(0,120)):(e2.excerpt?("\n"+e2.excerpt.substring(0,120)):"");
      return (i+1)+". ["+e2.category+" "+e2.year+"] "+e2.title.substring(0,60)+concl+"\n(출처: "+(e2.source_pdf||"")+")";
    }).join("\n\n") || "(관련 선례 매칭 없음 — 규정 직접 근거)";
    rows.push([gi+1, title, "- [위반내용] "+viol+"\n\n- [검토의견] "+opin, reg, basis,
               (r.reason.indexOf("[룰]")>=0?"룰(결정론)":"LLM 초안")+" / 태그: "+r.tag]);
  });
  return rows;
}

/* 검토대상 RAW 추출 — 검토필요 그룹에 속한 원장 행 전부 (조서 No로 연결) */
function buildNeedRawRows(){
  var targets=getJoseoTargets();
  if(!targets.length||!DATA) return [];
  var get=function(r,k){ return MAP[k]? String(r[MAP[k]]==null?"":r[MAP[k]]).trim() : ""; };
  var idx={};
  targets.forEach(function(g,i){
    var r=LAST.aiResults[g.subclass];
    idx[g.subclass]={no:i+1, tag:r.tag, chk:r.chk, func:r.func||"-", svc:r.svc||"-"};
  });
  /* 생략 없음 — 검토필요 그룹의 원장 행 전부 추출 (엑셀 시트 한도 초과 시 쓰기 단계에서 분할) */
  var rows=[["조서No","태그","형태판정","기능판정","역무판정"].concat(DATA.headers)];
  DATA.rows.forEach(function(r){
    /* guidelineMatchBySubclass와 동일한 그룹키 재계산 */
    var key=(get(r,"acct")||"?")+"|"+(get(r,"form")||"?")+"|"+(get(r,"func")||"?")+"|"+(get(r,"svc")||"?");
    var t=idx[key]; if(!t) return;
    rows.push([t.no, t.tag, t.chk, t.func, t.svc].concat(DATA.headers.map(function(h){
      var v=r[h]; return /금액|가액|상각|개수|건수/.test(h)? num(v) : v;
    })));
  });
  return rows;
}

function renderAIResults(){
  if(!LAST||!LAST.aiResults) return;
  var groups=LAST.glResults, results=LAST.aiResults;
  var old=el("sec_R_AI"); if(old) old.remove();
  var judged=groups.filter(function(g){return results[g.subclass];});
  if(!judged.length) return;
  /* 검토필요·오류 먼저, 금액순 */
  judged.sort(function(a,b){
    var ra=results[a.subclass], rb=results[b.subclass];
    var pa=(ra.chk==="적정"&&ra.svc!=="검토필요"&&ra.func!=="검토필요")?1:0, pb=(rb.chk==="적정"&&rb.svc!=="검토필요"&&rb.func!=="검토필요")?1:0;
    if(pa!==pb) return pa-pb;
    return Math.abs(b.acq)-Math.abs(a.acq);
  });
  var nNeed=judged.filter(function(g){var r=results[g.subclass]; return r.chk!=="적정"||r.svc==="검토필요"||r.func==="검토필요";}).length;
  var sec=document.createElement("div"); sec.className="rulesec"; sec.id="sec_R_AI";
  var html="<h3><span class='pill "+(nNeed?"MED":"INFO")+"'>"+(nNeed?"MED":"INFO")+"</span>R_AI. 로컬 AI 판정 — "+fmt(judged.length)+"그룹 (검토필요 "+fmt(nNeed)+")</h3>";
  html+="<div class='basis'>결정론 룰([룰]: 공통역무·에누리·조정전표·낙전·임대·로밍 — 재현 가능) + 로컬 LLM([LLM]: qwen3 초안 판정 — 검증인 확인 필수). 서비스코드 참조표 제공 시 공통 풀 판정·배부대상·역무 적정성이 정밀해집니다. 데이터는 이 PC를 벗어나지 않습니다.</div>";
  var lim=Math.min(judged.length,300);
  html+="<div class='tblwrap'><table><thead><tr><th>형태판정</th><th>기능판정</th><th>역무판정</th><th>태그</th><th>계정·형태·역무</th><th>적요·거래처</th><th>건수</th><th>금액</th><th>근거</th></tr></thead><tbody>";
  for(var i=0;i<lim;i++){
    var g=judged[i], r=results[g.subclass];
    var color=r.chk==="적정"?"#4F6E54":(r.chk==="오류"?"#8E3B39":"#A96A1E");
    var svcTxt=r.svc&&r.svc!=="정보없음"?r.svc:"-";
    var svcColor=svcTxt==="적정"?"#4F6E54":(svcTxt==="검토필요"?"#A96A1E":"#99A");
    var fnTxt=r.func&&r.func!=="정보없음"?r.func:"-";
    var fnColor=fnTxt==="적정"?"#4F6E54":(fnTxt==="검토필요"?"#A96A1E":"#99A");
    var codeCell="<b>"+esc(g.acctName||g.acct)+"</b><br><span style='font-size:10px;color:#556'>"+esc((g.formName||g.form)+" · "+(g.svcName||g.svc))+"</span>";
    var descCell=esc((g.descTop||[]).slice(0,2).join(" / "))+(g.vendorTop&&g.vendorTop.length?"<br><span style='color:#889'>"+esc(g.vendorTop[0])+"</span>":"");
    html+="<tr><td style='color:"+color+";font-weight:bold'>"+esc(r.chk)+"</td>"+
      "<td style='color:"+fnColor+";font-weight:bold'>"+esc(fnTxt)+"</td>"+
      "<td style='color:"+svcColor+";font-weight:bold'>"+esc(svcTxt)+"</td><td>"+esc(r.tag)+"</td>"+
      "<td style='white-space:normal;max-width:170px'>"+codeCell+"</td>"+
      "<td style='font-size:11px;white-space:normal;max-width:220px'>"+descCell+"</td>"+
      "<td class='num'>"+fmt(g.cnt)+"</td><td class='num'>"+fmtEok(g.acq)+"</td>"+
      "<td style='font-size:11px;white-space:normal;max-width:320px'>"+esc(r.reason)+"</td></tr>";
  }
  html+="</tbody></table></div>";
  if(judged.length>lim) html+="<div class='stat'>※ 화면 300그룹 — 전체는 엑셀 다운로드</div>";
  sec.innerHTML=html;
  el("ruleout").insertBefore(sec, el("ruleout").firstChild);
  sec.scrollIntoView({behavior:"smooth"});
}
'''

BRIDGE_JS = BRIDGE_JS.replace('__SYSTEM_JS__', _system_js)

# QA용 핵심 지식: SYSTEM_KNOWLEDGE에서 '확립된 판정 선례' 섹션만 추출 (단일 소스)
_m2 = _re.search(r'## 확립된 판정 선례.*?\n(.*?)\n## 출력 형식', _system, _re.DOTALL)
_qa_knowledge = _m2.group(1).strip() if _m2 else ''
BRIDGE_JS = BRIDGE_JS.replace('__QA_KNOWLEDGE__', json.dumps(_qa_knowledge, ensure_ascii=False))

marker20a = '/* 입력 핸들러 */'
if marker20a in new_html:
    new_html = new_html.replace(marker20a, BRIDGE_JS + '\n' + marker20a, 1)
    print('(20a) 브릿지 JS 삽입 OK')
else:
    print('!! (20a) 입력 핸들러 마커 못 찾음')

# 버튼 UI: aipk 버튼 뒤에 추가
marker20b = '<button id="aipk" class="sec hide">AI 판정 패킷 생성</button>'
if marker20b in new_html:
    new_html = new_html.replace(marker20b,
        marker20b + '\n    <button id="aijudge" class="sec hide">AI 판정 실행 (로컬)</button>'
        '\n    <input id="aimodel" value="qwen3:8b" title="Ollama 모델명" '
        'style="border:1px solid #CBD5E1;border-radius:4px;padding:6px 8px;font-size:12px;width:100px">'
        '\n    <span id="aiinfo" class="stat"></span>', 1)
    print('(20b) AI 버튼 UI 추가 OK')
else:
    print('!! (20b) aipk 버튼 마커 못 찾음')

# execute 시 버튼 표시
marker20c = '  el("aipk").classList.remove("hide");'
if marker20c in new_html:
    new_html = new_html.replace(marker20c, marker20c + '\n  el("aijudge").classList.remove("hide");', 1)
    print('(20c) 버튼 표시 OK')
else:
    print('!! (20c) aipk 표시 마커 못 찾음')

# 버튼 와이어링 + 참조표 리스너 + AI 질의
marker20d = 'el("aipk").onclick=buildAIPacket;'
if marker20d in new_html:
    new_html = new_html.replace(marker20d,
        marker20d + '\nel("aijudge").onclick=aiJudgeAll;'
        '\nel("svcmaster").addEventListener("input", parseSvcRef);'
        '\nel("svcalloc").addEventListener("input", parseSvcRef);'
        '\nel("aiqbtn").onclick=askAI;'
        '\nel("aiq").addEventListener("keydown", function(e){ if(e.key==="Enter"&&(e.ctrlKey||e.metaKey)) askAI(); });', 1)
    print('(20d) 버튼 와이어링 OK')
else:
    print('!! (20d) aipk onclick 마커 못 찾음')

# ─────────── 23. AI 질의 카드 ───────────
QA_CARD = (
    '<div class="card" id="aiqcard">\n'
    '  <h2>AI 질의 (로컬 Ollama + 가이드라인 지식베이스)</h2>\n'
    '  <div class="stat">통신회계 관련 질문을 입력하면 내장 지식베이스(1,815개 조항·선례)에서 관련 조항을 검색해 근거와 함께 로컬 AI가 답합니다. '
    '원장 업로드와 무관하게 언제든 사용 가능하며, 질문 내용도 이 PC를 벗어나지 않습니다. (Ctrl+Enter로 실행)</div>\n'
    '  <textarea id="aiq" style="height:60px" placeholder="예) 수익에 역무공통이 남아 있으면 안 되나요? / 낙전수입의 형태 분류는? / MVNO 판매활성화 장려금은 어떻게 처리하나요?"></textarea>\n'
    '  <div style="margin-top:8px"><button id="aiqbtn" class="sec">질문하기</button></div>\n'
    '  <div id="aiqout" style="margin-top:10px;font-size:13px"></div>\n'
    '</div>\n\n'
)
marker23 = '<div class="card">\n  <h2>검토 룰 · 근거 설정</h2>'
if marker23 in new_html:
    new_html = new_html.replace(marker23, QA_CARD + marker23, 1)
    print('(23) AI 질의 카드 OK')
else:
    print('!! (23) 질의 카드 마커 못 찾음')

# ─────────── 21. 서비스코드 참조표 입력 카드 ───────────
SVC_CARD = (
    '<div class="card" id="svcrefcard">\n'
    '  <h2>1-2. 서비스코드 참조표 (선택)</h2>\n'
    '  <div class="stat">엑셀에서 범위 복사(Ctrl+C) 후 붙여넣기 — 제공 시 공통 풀 판정(계층구분 기반)·배부 대상 표시·역무 적정성(svc_check) 판단이 정밀해집니다. 없으면 서비스명 기반으로 동작합니다.</div>\n'
    '  <label style="display:block;margin-top:10px;font-size:12px;color:#556"><b>① 서비스 마스터</b> (서비스코드 · 서비스명 · 계층구분 · 통신회계보고서코드 · 통신회계서비스명)</label>\n'
    '  <textarea id="svcmaster" style="height:70px" placeholder="기준년도&#9;서비스코드&#9;서비스명&#9;계층구분&#9;통신회계보고서코드&#9;통신회계서비스명"></textarea>\n'
    '  <label style="display:block;margin-top:8px;font-size:12px;color:#556"><b>② 공통 배부관계</b> (서비스코드(FROM) → 서비스코드(TO))</label>\n'
    '  <textarea id="svcalloc" style="height:70px" placeholder="기준년도&#9;서비스코드(FROM)&#9;서비스명(FROM)&#9;서비스코드(TO)&#9;서비스명(TO)"></textarea>\n'
    '  <div id="svcinfo" class="stat" style="color:#4F6E54;font-weight:bold"></div>\n'
    '</div>\n\n'
)
marker21 = '<div class="card hide" id="mapcard">'
if marker21 in new_html:
    new_html = new_html.replace(marker21, SVC_CARD + marker21, 1)
    print('(21) 참조표 카드 OK')
else:
    print('!! (21) mapcard 마커 못 찾음')

# 엑셀에 AI 판정 시트 추가
AI_XLSX = (
    '\n'
    '  /* R_AI 로컬 AI 판정 시트 */\n'
    '  if (LAST.aiResults && LAST.glResults){\n'
    '    var aiRows = [["형태판정","기능판정","역무판정","태그","계정","계정명","형태","형태명","기능명","역무","서비스명","건수","금액","적요 상위","거래처 상위","근거"]];\n'
    '    LAST.glResults.forEach(function(g){\n'
    '      var r = LAST.aiResults[g.subclass]; if(!r) return;\n'
    '      aiRows.push([r.chk, r.func||"정보없음", r.svc||"정보없음", r.tag, g.acct, g.acctName||"", g.form, g.formName||"", g.funcName||"", g.svc, g.svcName||"",\n'
    '        g.cnt, g.acq, (g.descTop||[]).join(" / "), (g.vendorTop||[]).join(" / "), r.reason]);\n'
    '    });\n'
    '    if(aiRows.length>1) XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(aiRows), "R_AI_로컬AI판정");\n'
    '    /* 조서(지적사항 초안) 시트 — 검토필요만, No + 5컬럼 조서 형식 */\n'
    '    var joseo = buildJoseoRows();\n'
    '    if(joseo.length>1){\n'
    '      var wsJ = XLSX.utils.aoa_to_sheet(joseo);\n'
    '      wsJ["!cols"] = [{wch:5},{wch:45},{wch:55},{wch:55},{wch:60},{wch:18}];\n'
    '      XLSX.utils.book_append_sheet(wb, wsJ, "조서초안_검토필요");\n'
    '      /* 검토대상 RAW — 조서 No로 연결된 원장 행 전체 (생략 없음).\n'
    '         엑셀 시트 한도(1,048,576행) 초과 시 검토대상_RAW_2, _3 …으로 분할.\n'
    '         dense 모드로 대용량 메모리 절감. */\n'
    '      var rawRows = buildNeedRawRows();\n'
    '      if(rawRows.length>1){\n'
    '        var RMAX=1000000, rHead=rawRows[0], rBody=rawRows.slice(1);\n'
    '        for(var rci=0; rci*RMAX<rBody.length; rci++){\n'
    '          var rChunk=[rHead].concat(rBody.slice(rci*RMAX,(rci+1)*RMAX));\n'
    '          var rNm= rci===0? "검토대상_RAW" : ("검토대상_RAW_"+(rci+1));\n'
    '          XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rChunk,{dense:true}), rNm);\n'
    '        }\n'
    '      }\n'
    '    }\n'
    '  }\n'
)
marker20e = '  /* R_UM 미분류 계정 시트 */'
if marker20e in new_html:
    new_html = new_html.replace(marker20e, AI_XLSX + '\n' + marker20e, 1)
    print('(20e) 엑셀 AI 시트 OK')
else:
    print('!! (20e) 엑셀 마커 못 찾음')

# ─────────── 저장 ───────────
out_path = os.path.join(ROOT, '수익비용_자동검토_v1.html')
io.open(out_path, 'w', encoding='utf-8').write(new_html)
print('─' * 60)
print('산출: %s' % out_path)
print('크기: %.1f KB' % (os.path.getsize(out_path)/1024))
