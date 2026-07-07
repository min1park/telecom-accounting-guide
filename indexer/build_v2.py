# -*- coding: utf-8 -*-
"""자산원장_자동검토_v2.html 빌드

v1.html에 다음을 추가:
1. 인라인 인덱스 (guideline_index.json + standard_terms.json)
2. 자산 row → 태그 변환 함수 rowToTags()
3. 매칭 스코어링 matchGuidelines() + guidelineMatchBySubclass()
4. 새 룰 R_GL "가이드라인 조항 매칭" 카드·섹션
5. 결과 엑셀에 "가이드라인_매칭" 시트 추가
"""
import io, os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

v1 = io.open(os.path.join(ROOT, '자산원장_자동검토_v1.html'), encoding='utf-8').read()
gi = io.open(os.path.join(ROOT, 'indexer', 'guideline_index.json'), encoding='utf-8').read()
st = io.open(os.path.join(ROOT, 'indexer', 'standard_terms.json'), encoding='utf-8').read()

# ─────────── 1. 인라인 인덱스 + 매칭 엔진 ───────────
INDEX_BLOCK = (
    '\n\n/* ══════════════ Phase 2: 가이드라인 지식베이스 인라인 ══════════════ */\n'
    'var STD_TERMS = ' + st + ';\n'
    'var GL_INDEX = ' + gi + ';\n'
    '\n'
    '/* row 텍스트 필드에서 표준 용어 alias 검색 → 태그 코드 리스트 */\n'
    'function rowToTags(r, map) {\n'
    '  var textParts = [];\n'
    '  ["subclass","formName","funcName","svcName","acctName"].forEach(function(k){\n'
    '    if (map[k] && r[map[k]] != null) textParts.push(String(r[map[k]]));\n'
    '  });\n'
    '  var text = textParts.join(" ");\n'
    '  var tags = {asset:{}, function:{}, service:{}, revenue:{}, cost:{}};\n'
    '  ["asset","function","service","revenue","cost"].forEach(function(cat){\n'
    '    var dict = STD_TERMS[cat] || {};\n'
    '    Object.keys(dict).forEach(function(std){\n'
    '      if (std.charAt(0) === "_") return;\n'
    '      var entry = dict[std];\n'
    '      var aliases = entry.aliases || [];\n'
    '      for (var i=0;i<aliases.length;i++){\n'
    '        if (aliases[i] && text.indexOf(aliases[i]) >= 0){\n'
    '          tags[cat][entry.code] = std; break;\n'
    '        }\n'
    '      }\n'
    '    });\n'
    '  });\n'
    '  return tags;\n'
    '}\n'
    '\n'
    '/* 태그 집합 vs 인덱스 entry 매칭도 계산 */\n'
    'var GL_WEIGHTS = {asset:2, function:1, service:3, revenue:1, cost:1};\n'
    'function scoreEntry(rowTags, entry){\n'
    '  var score = 0, matched = [];\n'
    '  Object.keys(GL_WEIGHTS).forEach(function(cat){\n'
    '    var eCodes = {};\n'
    '    (entry.tags[cat]||[]).forEach(function(t){ eCodes[t.code]=t.term; });\n'
    '    Object.keys(rowTags[cat]).forEach(function(code){\n'
    '      if (eCodes[code]){\n'
    '        score += GL_WEIGHTS[cat];\n'
    '        matched.push(cat+":"+rowTags[cat][code]);\n'
    '      }\n'
    '    });\n'
    '  });\n'
    '  return {score:score, matched:matched};\n'
    '}\n'
    '\n'
    'function matchGuidelines(rowTags, K){\n'
    '  K = K || 5;\n'
    '  var out = [];\n'
    '  for (var i=0;i<GL_INDEX.entries.length;i++){\n'
    '    var e = GL_INDEX.entries[i];\n'
    '    var s = scoreEntry(rowTags, e);\n'
    '    if (s.score > 0){\n'
    '      out.push({entry:e, score:s.score, matched:s.matched});\n'
    '    }\n'
    '  }\n'
    '  out.sort(function(a,b){ return b.score - a.score; });\n'
    '  return out.slice(0, K);\n'
    '}\n'
    '\n'
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
    '  });\n'
    '  var out = [];\n'
    '  Object.keys(groups).forEach(function(sc){\n'
    '    var g = groups[sc];\n'
    '    var tags = rowToTags(g.sample, map);\n'
    '    var top = matchGuidelines(tags, K);\n'
    '    if (top.length > 0){\n'
    '      var mostForm = Object.keys(g.forms).sort(function(a,b){return g.forms[b]-g.forms[a];})[0]||"";\n'
    '      var mostFunc = Object.keys(g.funcs).sort(function(a,b){return g.funcs[b]-g.funcs[a];})[0]||"";\n'
    '      var mostSvc  = Object.keys(g.svcs ).sort(function(a,b){return g.svcs[b] -g.svcs[a] ;})[0]||"";\n'
    '      out.push({subclass:sc, cnt:g.cnt, acq:g.acq, form:mostForm, func:mostFunc, svc:mostSvc, tags:tags, matches:top});\n'
    '    }\n'
    '  });\n'
    '  out.sort(function(a,b){ return b.acq - a.acq; });\n'
    '  return out;\n'
    '}\n'
)

# ─────────── 2. RULE_META에 R_GL 추가 (v1의 RULE_META 배열 뒤에) ───────────
RULE_ADD = (
    '\n'
    '/* R_GL은 정합성 지적이 아니라 참조성 매칭이므로 요약 카드에는 안 넣고 별도 섹션 */\n'
    'var GL_META = {id:"R_GL", sev:"INFO", name:"가이드라인 조항 매칭 (세분류 단위)", \n'
    '  basis:"각 자산 세분류(subclass)의 대표 자산을 표준 용어 사전으로 태깅 후, guideline_index (1,857 entry)와 대조하여 관련도 top-5 조항을 매칭. 지적이 아니라 참고: 회사 원장 검토·조서 작성 시 근거 조항 인용용."};\n'
)

# ─────────── 3. execute() 안에서 R_GL 결과 렌더링 (기존 execute의 out.appendChild(sec) 뒤에 append) ───────────
GL_RENDER = (
    '\n'
    '  /* ─── R_GL 가이드라인 조항 매칭 (세분류별) ─── */\n'
    '  if (glResults.length){\n'
    '    var glSec = document.createElement("div"); glSec.className="rulesec"; glSec.id="sec_R_GL";\n'
    '    var glHtml = "<h3><span class=\'pill INFO\'>INFO</span>"+GL_META.id+". "+esc(GL_META.name)+" — 세분류 "+fmt(glResults.length)+"개 매칭</h3>";\n'
    '    glHtml += "<div class=\'basis\'>"+esc(GL_META.basis)+"</div>";\n'
    '    var lim = Math.min(glResults.length, 100);\n'
    '    glHtml += "<div class=\'tblwrap\'><table><thead><tr><th>세분류</th><th>대세 형태·기능·역무</th><th>건수</th><th>취득금액</th><th>매칭된 태그</th><th>관련 조항 (top-5)</th></tr></thead><tbody>";\n'
    '    for (var gi=0; gi<lim; gi++){\n'
    '      var g = glResults[gi];\n'
    '      var tagList = [];\n'
    '      ["asset","function","service","revenue","cost"].forEach(function(cat){\n'
    '        Object.values(g.tags[cat]).forEach(function(t){ tagList.push(cat.charAt(0).toUpperCase()+":"+t); });\n'
    '      });\n'
    '      var matchHtml = g.matches.map(function(m,i){\n'
    '        var ttl = esc((m.entry.title||"").substring(0,60));\n'
    '        var src = m.entry.category+"("+m.entry.year+")";\n'
    '        var concl = (m.entry.conclusions[0]||"").substring(0,80);\n'
    '        return "<div style=\'margin:3px 0;padding:3px 6px;background:#F5F8FA;border-left:2px solid #4A7C9B;font-size:11px\'>"+\n'
    '          "<b>"+(i+1)+".</b> ["+esc(src)+"] "+ttl+" <span style=\'color:#889\'>(점수 "+m.score+")</span><br>"+\n'
    '          "<span style=\'color:#556\'>매칭: "+m.matched.slice(0,5).join(", ")+"</span>"+\n'
    '          (concl?"<br><span style=\'color:#456\'>결론: "+esc(concl)+"</span>":"")+\n'
    '          "</div>";\n'
    '      }).join("");\n'
    '      glHtml += "<tr><td><b>"+esc(g.subclass)+"</b></td><td>"+esc(g.form+" · "+g.func+" · "+g.svc)+"</td>"+\n'
    '        "<td class=\'num\'>"+fmt(g.cnt)+"</td><td class=\'num\'>"+fmtEok(g.acq)+"</td>"+\n'
    '        "<td style=\'font-size:10px;color:#667;white-space:normal;max-width:180px\'>"+esc(tagList.slice(0,6).join(", "))+(tagList.length>6?" …":"")+"</td>"+\n'
    '        "<td style=\'white-space:normal;max-width:520px\'>"+matchHtml+"</td></tr>";\n'
    '    }\n'
    '    glHtml += "</tbody></table></div>";\n'
    '    if (glResults.length>lim) glHtml += "<div class=\'stat\'>※ 화면에는 100개 세분류 — 전체 "+fmt(glResults.length)+"개는 엑셀 다운로드로 확인</div>";\n'
    '    glSec.innerHTML = glHtml;\n'
    '    out.appendChild(glSec);\n'
    '  }\n'
)

# ─────────── 4. 요약 카드에도 R_GL 카드 추가 (INFO 뱃지, 클릭 시 스크롤) ───────────
GL_CARD = (
    '\n'
    '  /* R_GL 매칭 실행 (카드·섹션 공용) */\n'
    '  var glResults = guidelineMatchBySubclass(DATA.rows, MAP, 5);\n'
    '  LAST.glResults = glResults;\n'
    '  if (glResults && glResults.length){\n'
    '    var glCard = document.createElement("div");\n'
    '    glCard.className = "rc INFO";\n'
    '    glCard.innerHTML = "<span class=\'sev\'>INFO</span><h3>R_GL. 가이드라인 매칭</h3><div class=\'n\'>"+fmt(glResults.length)+"<span style=\'font-size:12px\'> 세분류</span></div><div class=\'m\'>관련 조항 top-5씩</div>";\n'
    '    glCard.onclick = function(){ var t=el("sec_R_GL"); if(t) t.scrollIntoView({behavior:"smooth"}); };\n'
    '    cards.appendChild(glCard);\n'
    '  }\n'
)

# ─────────── 5. 엑셀 다운로드에 가이드라인 매칭 시트 추가 ───────────
XLSX_ADD = (
    '\n'
    '  /* R_GL 시트 */\n'
    '  if (LAST.glResults && LAST.glResults.length){\n'
    '    var glHead = ["세분류","대세 형태","대세 기능","대세 역무","건수","취득금액",\n'
    '                  "매칭된 태그","순위","관련 조항 ID","카테고리","연도","제목","점수","매칭 태그","결정 유형","결론","출처 PDF"];\n'
    '    var glRows = [glHead];\n'
    '    LAST.glResults.forEach(function(g){\n'
    '      var tagList = [];\n'
    '      ["asset","function","service","revenue","cost"].forEach(function(cat){\n'
    '        Object.values(g.tags[cat]).forEach(function(t){ tagList.push(cat.charAt(0).toUpperCase()+":"+t); });\n'
    '      });\n'
    '      var tagStr = tagList.join(", ");\n'
    '      g.matches.forEach(function(m, i){\n'
    '        glRows.push([g.subclass, g.form, g.func, g.svc, g.cnt, g.acq, tagStr, i+1,\n'
    '          m.entry.id, m.entry.category, m.entry.year, m.entry.title, m.score,\n'
    '          m.matched.join("; "), (m.entry.decision_types||[]).join(","),\n'
    '          (m.entry.conclusions[0]||""), m.entry.source_pdf]);\n'
    '      });\n'
    '    });\n'
    '    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(glRows), "R_GL_가이드라인매칭");\n'
    '  }\n'
)

# ─────────── 삽입 ───────────
new_html = v1

# (a) execute() 안의 RULE_META.forEach 뒤, execute 함수 끝 앞에 GL_RENDER 삽입
# 주의: GL_RENDER는 forEach 콜백 밖에 있어야 함 (안이면 R1~R7 각각마다 반복 렌더)
marker_a = '  });\n}\n\nfunction download('
if marker_a in new_html:
    new_html = new_html.replace(marker_a, '  });\n' + GL_RENDER + '\n}\n\nfunction download(', 1)
    print('(a) execute() GL_RENDER 삽입 OK (forEach 밖)')
else:
    print('!! (a) 마커 못 찾음')

# (b) 요약 카드 삽입: 기존 RULE_META.forEach 카드 렌더 뒤에 GL_CARD 추가
marker_b = '    cards.appendChild(d);\n  });\n\n  var out = el("ruleout");'
if marker_b in new_html:
    new_html = new_html.replace(marker_b, '    cards.appendChild(d);\n  });' + GL_CARD + '\n\n  var out = el("ruleout");', 1)
    print('(b) 카드 R_GL 삽입 OK')
else:
    print('!! (b) 카드 마커 못 찾음')

# (c) RULE_META 배열 뒤에 GL_META 추가
marker_c = '];\n\n/* ══════════════ 유틸 ══════════════ */'
if marker_c in new_html:
    new_html = new_html.replace(marker_c, ']' + RULE_ADD + '\n/* ══════════════ 유틸 ══════════════ */', 1)
    print('(c) GL_META 삽입 OK')
else:
    print('!! (c) GL_META 마커 못 찾음')

# (d) 매칭 엔진 삽입: /* ══════════════ 룰 엔진 ══════════════ */ 앞에
marker_d = '/* ══════════════ 룰 엔진 ══════════════ */'
if marker_d in new_html:
    new_html = new_html.replace(marker_d, INDEX_BLOCK + '\n' + marker_d, 1)
    print('(d) 매칭 엔진 + 인덱스 인라인 삽입 OK')
else:
    print('!! (d) 룰 엔진 마커 못 찾음')

# (e) 엑셀 다운로드: 마지막 XLSX.writeFile 앞에 GL 시트 추가
marker_e = '  var d=new Date(), ds=d.getFullYear()+("0"+(d.getMonth()+1)).slice(-2)+("0"+d.getDate()).slice(-2);\n  XLSX.writeFile(wb, "자산원장_자동검토결과_"+ds+".xlsx");'
if marker_e in new_html:
    new_html = new_html.replace(marker_e, XLSX_ADD + '\n' + marker_e, 1)
    print('(e) 엑셀 GL 시트 추가 OK')
else:
    print('!! (e) 엑셀 마커 못 찾음')

# (f) 헤더 부제·버전 업데이트
new_html = new_html.replace(
    '<h1>통신회계 자산원장 자동검토<span class="badge">v1.0</span></h1>',
    '<h1>통신회계 자산원장 자동검토<span class="badge">v2.0 · GL 매칭</span></h1>',
    1)
new_html = new_html.replace(
    '자산원장 자동검토 v1.0',
    '자산원장 자동검토 v2.0 · 가이드라인 매칭(GL) 층 추가 (1,857 entry 인덱스)',
    1)

# ─────────── 저장 ───────────
out_path = os.path.join(ROOT, '자산원장_자동검토_v2.html')
io.open(out_path, 'w', encoding='utf-8').write(new_html)
print('─' * 60)
print('산출: %s' % out_path)
print('크기: %.1f KB (v1: %.1fKB, +%.1fKB)' % (os.path.getsize(out_path)/1024, len(v1)/1024, (len(new_html)-len(v1))/1024))
