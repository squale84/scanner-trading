// Filtre par actif du journal : exécute les vraies fonctions de index.html avec un DOM factice.
// Lancer : node --test tests/journal_filter.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "..", "index.html"), "utf8");

function extractFunction(name) {
  const start = html.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `fonction introuvable : ${name}`);
  let depth = 0, i = html.indexOf("{", start);
  for (; i < html.length; i++) {
    if (html[i] === "{") depth++;
    else if (html[i] === "}" && --depth === 0) break;
  }
  return html.slice(start, i + 1);
}
function extractConst(name) {
  const start = html.indexOf(`const ${name} = `);
  assert.ok(start >= 0, `constante introuvable : ${name}`);
  const end = html.indexOf("\n", start);
  return html.slice(start, end).replace(/\r$/, "");
}

// DOM factice : un élément par id, avec innerHTML, style, textContent et écouteurs.
function makeDom() {
  const els = {};
  const el = id => (els[id] ||= { id, innerHTML: "", textContent: "", style: {}, listeners: {},
    dataset: {}, addEventListener(t, f) { this.listeners[t] = f; } });
  return { els, getElementById: el };
}

const names = ["parseNum", "formatDisplay", "setupIctLabel", "statusCellHtml", "qualityClass",
  "sessionCellHtml", "dateCellHtml", "unavailableReason", "formatEur", "resultCellHtml",
  "exitPriceCellHtml", "tradeRowHtml", "buildJournalTrades", "renderJournalAssetTabs",
  "renderJournalTable", "updateJournalStats"];

const code = [
  extractConst("escHtml"), extractConst("utcDate"), extractConst("EXIT_LABELS_FR"),
  "let journalClosed = 0, journalWins = 0, journalLosses = 0, journalR = 0, journalOrphanCount = 0, hasLogRows = false;",
  "let journalAssetFilter = 'ALL'; const journalRows = [];",
  ...names.map(extractFunction),
  "({ renderJournalTable, journalRows, setFilter: v => { journalAssetFilter = v; }, getFilter: () => journalAssetFilter, getOrphanCount: () => journalOrphanCount });",
].join("\n");

function setup(rows) {
  const dom = makeDom();
  const ctx = createContext({ document: dom, Date, Math, Intl, console });
  const api = runInContext(code, ctx);
  api.journalRows.push(...rows);
  return { api, dom };
}

const entry = (sym, time, dir = "BUY", id = 1) => ({ kind: "entry", time, symbol: sym, direction: dir, status: "SSL SWEEP", quality: "A", session: "🇬🇧 Londres", entry_price: "100", sl_price: "99", tp_price: "102", trade_id: `${sym}-${id}` });
const exit = (sym, time, status = "TP_HIT") => ({ kind: "exit", time, symbol: sym, status, direction: "BUY", entry_price: "100", sl_price: "99", tp_price: "102", exit_price: "102", r_multiple: 2, targets: [], targets_reached: 1 });

const ROWS = [
  entry("GOLD", "2026-09-20T08:00", "BUY", 1), exit("GOLD", "2026-09-20T09:00"),
  entry("EURUSD", "2026-09-21T08:00", "SELL", 2), exit("EURUSD", "2026-09-21T09:00", "SL_HIT"),
  entry("FR40", "2026-09-22T08:00", "BUY", 3), exit("FR40", "2026-09-22T09:00"),
];

test("Tous les actifs : toutes les lignes sont affichées", () => {
  const { dom } = setup(ROWS);
  const { renderJournalTable } = (() => { const r = setup(ROWS); return r.api; })();
  // rendu avec filtre ALL (défaut)
  const s = setup(ROWS); s.api.renderJournalTable();
  const body = s.dom.els["log-body"].innerHTML;
  assert.ok(body.includes("GOLD") && body.includes("EURUSD") && body.includes("FR40"));
});

test("Filtre GOLD : seules les lignes GOLD restent dans le tableau", () => {
  const s = setup(ROWS); s.api.setFilter("GOLD"); s.api.renderJournalTable();
  const body = s.dom.els["log-body"].innerHTML;
  assert.ok(body.includes(">GOLD<"), "GOLD absent");
  assert.ok(!body.includes("EURUSD") && !body.includes("FR40"), "autres actifs encore affichés");
});

test("Les boutons affichent les compteurs par actif", () => {
  const s = setup(ROWS); s.api.renderJournalTable();
  const tabs = s.dom.els["journal-assets"].innerHTML;
  // un trade = une entrée + sa sortie : 3 trades au total, 1 par actif
  assert.match(tabs, /Tous \(3\)/);
  assert.match(tabs, /GOLD \(1\)/);
  assert.match(tabs, /EURUSD \(1\)/);
});

test("Les compteurs globaux ne dépendent pas du filtre", () => {
  const s = setup(ROWS); s.api.renderJournalTable();
  const all = s.dom.els["log-count"].textContent;
  s.api.setFilter("EURUSD"); s.api.renderJournalTable();
  assert.equal(s.dom.els["log-count"].textContent, all);
});

test("Un symbole hostile reste du texte dans les boutons (pas de balisage actif)", () => {
  const hostile = [entry(`X'"><img src=x onerror=alert(1)>`, "2026-09-23T08:00"), exit(`X'"><img src=x onerror=alert(1)>`, "2026-09-23T09:00")];
  const s = setup(hostile); s.api.renderJournalTable();
  const tabs = s.dom.els["journal-assets"].innerHTML;
  assert.ok(!tabs.includes("<img"), tabs);
  assert.ok(tabs.includes("&lt;img"), tabs);
});

test("Un filtre devenu invalide (actif disparu) revient à Tous", () => {
  const s = setup(ROWS); s.api.setFilter("NATGAS"); s.api.renderJournalTable();
  assert.equal(s.api.getFilter(), "ALL");
});
