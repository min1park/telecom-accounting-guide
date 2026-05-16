# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page, dependency-free static web app: **영업보고서 참고자료 검색 시스템** — a
browser-side search/browse tool over Korean telecommunications accounting-separation
reference material (전기통신사업 회계분리기준). All UI text, data, and commit messages
are in Korean. There is no backend, build step, package manager, test suite, or linter —
the entire application is `index.html` plus static `data/` assets, deployed via GitHub Pages.

## Running / developing

There is no build or test tooling. To preview locally, serve the directory over HTTP
(needed so the dynamically-injected `data/*.js` `<script>` tags resolve):

```bash
python3 -m http.server 8000   # then open http://localhost:8000
```

Deployment is GitHub Pages from the default branch — pushing is the deploy. An empty
"trigger GitHub Pages build" commit is the established way to force a rebuild.

## Architecture

`index.html` is fully self-contained: all CSS lives in one inline `<style>` block and
all logic in one inline `<script>` block (no framework, only Google Fonts via CDN).

Data is **not** bundled or fetched as JSON. The flow is:

1. `dataRegistry` (object near the top of the script) is the single source of truth. It
   maps each **category display name** → `{ key, years: [...], icon, color }`.
2. The script builds script URLs as `data/${key}_${year}.js` (or `data/${key}_data.js`
   when the year is `null`) for every year in every registry entry, and injects them as
   `<script>` tags.
3. Each `data/*.js` file is just a call to the global `window.registerData([ ...records ])`,
   which pushes its records into `fullTableData`.
4. Once all files load, `initialize()` reduces `fullTableData` into `groupedData`
   (`category → year → records[]`) and renders the sidebar. Browsing reads `groupedData`;
   search filters `fullTableData` directly.

Consequence: a `data/*.js` file is only loaded if its year is listed in `dataRegistry`,
**and** the renderer only shows a category if records carry a matching `category` string.
Both sides must agree.

## Data record schema

Each element of the array passed to `registerData` looks like:

```js
{
  "id": "GOSI-2023-001",          // convention: {KEY-UPPER}-{YEAR}-{NNN}
  "category": "영업보고서 검증결과 지적사항",  // MUST exactly equal a dataRegistry display-name key
  "year": "2023",                 // string; null for the year-less "참고자료" set
  "title": "...",
  "content": "...",               // see below
  "source_company": null,
  "source_category": null,
  "related_tags": ["#tag", ...]   // array OR comma-joined string; both accepted
}
```

`content` is polymorphic and rendered accordingly:
- A **string** → single paragraph; `\n` becomes `<br>`.
- An **object** → each key becomes an uppercased bold section heading with its value as
  the body (e.g. `qna_*` files use `{ question, answer }`; `acmt_*` use keys like
  `current_situation`). Key names are free-form per file but rendered verbatim (uppercased).

`icon` values in `dataRegistry` are HTML numeric entities (e.g. `&#128269;`).

## Current categories (key → files)

`gosi` (지적사항), `qna` (질의회신), `acmt` (회의결과), `acc` (일원화방안),
`guide` (작성주의사항, 2019 only), `ref` (참고자료 → `ref_data.js`, year `null`).
Year coverage differs per key and `acc` has gaps — trust `dataRegistry`, not assumptions.

## Common change recipes

- **Add a year to an existing category:** create `data/{key}_{year}.js` wrapping records
  in `window.registerData([...])`, then add the year to that category's `years` array in
  `dataRegistry`. Skipping the registry edit means the file is silently never loaded.
- **Add a new category:** add a `dataRegistry` entry (`key`, `years`, `icon`, `color`),
  create the matching `data/*.js` file(s), and ensure every record's `category` string is
  byte-for-byte identical to the new registry display-name key.
- **Editing data:** keep one record array per file, valid JS object literals, `\n` for
  line breaks inside `content`. The PDFs in `data/` and the repo root are the source
  documents these `.js` files are transcribed from.

The client-side search requires ≥2 characters, is debounced 200 ms, matches
case-insensitively across `title`, flattened `content`, and `related_tags`, and
regex-escapes the query before highlighting.
