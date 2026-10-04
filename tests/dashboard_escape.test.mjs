// Régression XSS du dashboard : les fonctions de rendu réelles de index.html sont extraites
// et exécutées sur une charge utile hostile (webhook / calendrier). Lancer : node --test tests/dashboard_escape.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "..", "index.html"), "utf8");

// Extrait une fonction `function NAME(` par équilibrage des accolades.
function extractFunction(name) {
  const start = html.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `fonction introuvable : ${name}`);
  let depth = 0;
  let i = html.indexOf("{", start);
  for (; i < html.length; i++) {
    if (html[i] === "{") depth++;
    else if (html[i] === "}" && --depth === 0) break;
  }
  return html.slice(start, i + 1);
}

// Extrait une constante tenant sur une ligne (`const NAME = ...;`).
function extractConst(name) {
  const start = html.indexOf(`const ${name} = `);
  assert.ok(start >= 0, `constante introuvable : ${name}`);
  const end = html.indexOf("\n", start);
  return html.slice(start, end).replace(/\r$/, "");
}

const names = ["parseNum", "formatDisplay", "setupIctLabel", "statusCellHtml", "qualityClass",
  "sessionCellHtml", "dateCellHtml", "unavailableReason", "formatEur", "resultCellHtml",
  "exitPriceCellHtml", "tradeRowHtml"];

const code = [
  extractConst("escHtml"),
  extractConst("utcDate"),
  extractConst("EXIT_LABELS_FR"),
  ...names.map(extractFunction),
  "({ escHtml, tradeRowHtml, setupIctLabel, statusCellHtml })",
].join("\n");

const ctx = createContext({ document: { getElementById: () => ({ value: "0" }) } });
const { escHtml, tradeRowHtml, setupIctLabel, statusCellHtml } = runInContext(code, ctx);

const HOSTILE = "<img src=x onerror=alert(1)>";

test("escHtml neutralise les 5 caractères spéciaux", () => {
  assert.equal(escHtml(`<a href="x">'&'</a>`), "&lt;a href=&quot;x&quot;&gt;&#39;&amp;&#39;&lt;/a&gt;");
  assert.equal(escHtml(undefined), "");
  assert.equal(escHtml(null), "");
});

test("setupIctLabel : libellé connu inchangé, valeur inconnue rendue brute (à échapper par l'appelant)", () => {
  assert.equal(setupIctLabel("SSL SWEEP"), "🐢 Turtle Soup (SSL)");
  assert.equal(escHtml(setupIctLabel(HOSTILE)), "&lt;img src=x onerror=alert(1)&gt;");
});

test("statusCellHtml : un statut hostile ne crée aucun balisage actif", () => {
  const out = statusCellHtml('SL_HIT"><img src=x onerror=alert(1)>');
  assert.ok(!out.includes("<img"), out);
  assert.ok(out.includes("&lt;img"), out);
  assert.match(statusCellHtml("TP_HIT"), /TP atteint/);
});

test("tradeRowHtml : symbole, direction, statut, qualité hostiles restent du texte", () => {
  const out = tradeRowHtml({
    entry: {
      time: "2026-01-01T10:00:00", symbol: HOSTILE, direction: "BUY",
      status: 'SSL SWEEP" onmouseover="alert(1)', quality: 'A+"><script>x</script>',
      session: "🇬🇧 Londres", entry_price: "1.10000", sl_price: "1.09000", tp_price: "1.12000",
    },
    exit: null,
    isOpen: true,
  });
  assert.ok(!out.includes("<img"), "balise <img> active");
  assert.ok(!out.includes("<script"), "balise <script> active");
  assert.ok(!out.includes(' onmouseover="'), "attribut d'événement injecté");
});

test("tradeRowHtml : données propres rendues à l'identique (pas de régression d'affichage)", () => {
  const out = tradeRowHtml({
    entry: { time: "2026-01-01T10:00:00", symbol: "GOLD", direction: "SELL", status: "RETEST",
      quality: "A+", session: "🇺🇸 NY AM", entry_price: "2350.5", sl_price: "2355", tp_price: "2340" },
    exit: null,
    isOpen: true,
  });
  assert.ok(out.includes(">GOLD<"));
  assert.ok(out.includes("🔄 Retest FVG/OB"));
  assert.ok(out.includes("quality-A_PLUS"));
});
