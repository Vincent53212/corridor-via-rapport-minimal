// Étape 30 — livrables/rapport_corridor.html -> livrables/rapport_corridor.pdf.
//
// Chrome piloté par puppeteer-core, et non `chrome --print-to-pdf` : c'est la
// seule voie pour un pied de page paginé (displayHeaderFooter + footerTemplate).
// `preferCSSPageSize` fait de @page la référence, ce qui donne la couverture à
// fond perdu (@page couverture, marges nulles) sans traitement particulier.
//
// DEUX PASSES, parce que le sommaire annonce des folios réels :
//   passe 1 -> PDF de travail ; mutool en extrait le texte page par page et on
//              relève la page où chaque titre apparaît pour la première fois
//              APRÈS le sommaire (qui contient les mêmes libellés) ;
//   passe 2 -> les numéros sont injectés dans le DOM, puis le PDF final est
//              imprimé. Le sommaire occupe la même place aux deux passes : les
//              folios relevés restent valides.
//
// La couverture est imprimée SÉPARÉMENT et sans pied : displayHeaderFooter ne se
// conditionne pas page par page, et le pied se poserait sur son fond d'encre. On
// recolle ensuite avec mutool ; `pageNumber` reste le folio du document complet.
//
// Tout passe par un dossier de travail ASCII hors OneDrive : mutool refuse les
// chemins accentués, et ce dépôt vit sous « Contrat François Rebello ».
//
//     node scripts/30_rapport_pdf.mjs

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, copyFileSync, readFileSync, rmSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const RACINE = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = join(RACINE, "livrables", "rapport_corridor.html");
// Sortie normalement fixe. `RAPPORT_PDF_OUT` permet d'écrire ailleurs quand la
// cible est tenue ouverte par un lecteur PDF, plutôt que de perdre la composition.
const CIBLE = process.env.RAPPORT_PDF_OUT
  || join(RACINE, "livrables", "rapport_corridor.pdf");

const TRAVAIL = join(tmpdir(), "tgv_rapport");
const tHtml = join(TRAVAIL, "rapport.html");
const tHtml2 = join(TRAVAIL, "rapport_final.html");
const tP1 = join(TRAVAIL, "passe1.pdf");
const tTxt = join(TRAVAIL, "passe1.txt");
const tCouv = join(TRAVAIL, "couverture.pdf");
const tCorps = join(TRAVAIL, "corps.pdf");
const tFinal = join(TRAVAIL, "final.pdf");

const CHROMES = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
];
const chrome = CHROMES.find(existsSync);
if (!chrome) { console.error("Chrome introuvable."); process.exit(1); }
if (!existsSync(SRC)) { console.error("HTML introuvable : lancer 29_rapport_html.py."); process.exit(1); }

// Résolution de puppeteer-core par le NOM du paquet et non par un chemin de
// fichier : la disposition interne change d'une version à l'autre (lib/cjs/... en
// 24.x, lib/... en 25.x). Un chemin en dur trouvait donc le puppeteer 24.43 que
// mermaid-cli embarque et ignorait le 25.4 installé globalement, si bien que
// désinstaller mermaid aurait cassé la fabrication du rapport.
const RACINES = [
  join(process.env.APPDATA || "", "npm", "node_modules"),
  join(process.env.APPDATA || "", "npm", "node_modules", "@mermaid-js",
       "mermaid-cli", "node_modules"),
];
function charger() {
  for (const racine of RACINES) {
    try {
      const m = require(require.resolve("puppeteer-core", { paths: [racine] }));
      return m.default || m;
    } catch { /* racine suivante */ }
  }
  return null;
}

// Pied de page. Les couleurs sont écrites ici en clair parce que le
// footerTemplate de Chrome est un document ISOLÉ, sans accès au CSS de la page
// ni à ses variables : ce sont celles de identite.json, à garder synchronisées.
//
// Le gabarit fait DEUX choses. Il pose le pied, filet clair, identité à gauche
// et folio à droite. Et il peint les deux bandes de marge en crème : sans elles,
// le haut et le bas de chaque page sortaient blancs (voir la note en tête de
// identite/rapport.css). C'est possible parce qu'un élément `position:fixed`
// d'un gabarit de pied se positionne sur la PAGE ENTIÈRE, et non sur la seule
// boîte du pied. Les deux bandes doivent donc couvrir exactement les marges
// hautes et basses de @page, un cheveu de plus pour ne pas laisser de liseré.
const CREME = "#F5F1E8";
const bande = (cote, hauteur) =>
  `<div style="position:fixed;${cote}:0;left:0;right:0;height:${hauteur};` +
  `background:${CREME};-webkit-print-color-adjust:exact;"></div>`;

const PIED = bande("top", "0.79in") + bande("bottom", "0.86in") + `
<div style="position:fixed;bottom:0.42in;left:0.85in;right:0.85in;
            font-family:'IBM Plex Mono','Consolas',monospace;font-size:7pt;color:#646B79;
            border-top:.5pt solid #D2CAB6;padding-top:2.4mm;
            display:flex;justify-content:space-between;align-items:baseline;">
  <span>Corridor Qu&#233;bec-Toronto &nbsp;&#183;&nbsp; Ce que la voie existante permet
        &nbsp;&#183;&nbsp; Vincent Duguay / Vision Transport</span>
  <span class="pageNumber"></span>
</div>`;

// `preferCSSPageSize` fait de @page la référence, y compris de la page nommée
// `couverture` (marges nulles, fond perdu). Passer des marges par l'option
// `margin` de puppeteer serait sans effet : dès que @page en déclare, Chrome
// ignore celles du tirage.
const OPTS = {
  printBackground: true,
  preferCSSPageSize: true,
  displayHeaderFooter: true,
  headerTemplate: "<div></div>",
  footerTemplate: PIED,
  timeout: 180000,
};
// La couverture s'imprime à part et SANS gabarit de pied : ses bandes crème se
// poseraient sur l'encre à fond perdu. Elle occupe exactement une page dans les
// deux régimes grâce à sa hauteur en `vh`, donc la pagination relevée à la
// passe 1 reste valide.
const OPTS_COUVERTURE = { ...OPTS, displayHeaderFooter: false };

const norm = (s) => s.toLowerCase().replace(/[’‘]/g, "'").replace(/\s+/g, "");

function pagesDuPdf(pdf) {
  try {
    execFileSync("mutool", ["draw", "-F", "txt", "-o", tTxt, pdf],
                 { stdio: "ignore", timeout: 120000 });
    return readFileSync(tTxt, "utf8").split("\f");
  } catch {
    console.warn("  mutool indisponible : sommaire sans folios.");
    return null;
  }
}

function releverFolios(pages, cibles) {
  const res = {};
  if (!pages) return res;
  const n = pages.map(norm);
  // La page du sommaire porte tous les titres : on la neutralise.
  const iSom = n.findIndex((p) => p.includes(norm("Table des matières")));
  if (iSom >= 0) n[iSom] = "";
  for (const c of cibles) {
    const aiguille = norm(c);
    for (let i = 1; i < n.length; i++) {
      if (n[i].includes(aiguille)) { res[c] = i + 1; break; }
    }
  }
  return res;
}

mkdirSync(TRAVAIL, { recursive: true });
copyFileSync(SRC, tHtml);

const puppeteer = charger();
if (!puppeteer) { console.error("puppeteer-core introuvable."); process.exit(1); }

const navigateur = await puppeteer.launch({
  executablePath: chrome,
  headless: "new",
  args: ["--allow-file-access-from-files", "--font-render-hinting=none"],
});
try {
  const page = await navigateur.newPage();
  await page.goto("file:///" + tHtml.replace(/\\/g, "/"),
                  { waitUntil: "networkidle0", timeout: 120000 });
  // Les images sont inlinées en base64 par l'étape 29, mais Chrome ne décode pas
  // forcément avant l'impression : on l'attend explicitement.
  await page.evaluate(async () => {
    for (const img of document.images) img.loading = "eager";
    await Promise.all([...document.images].filter((i) => !i.complete)
      .map((i) => new Promise((r) => { i.onload = i.onerror = r; })));
    await document.fonts.ready;
  });
  await page.emulateMediaType("print");

  const cibles = await page.$$eval(".toc-folio[data-find]",
    (els) => els.map((e) => e.getAttribute("data-find")));

  console.log("  passe 1 : pagination…");
  await page.pdf({ ...OPTS, path: tP1 });
  const folios = releverFolios(pagesDuPdf(tP1), cibles);
  const trouves = Object.keys(folios).length;
  console.log(`  ${trouves}/${cibles.length} entrées de sommaire localisées.`);
  if (trouves < cibles.length)
    console.warn("  non localisées :", cibles.filter((c) => !folios[c]).join(" | "));

  console.log("  passe 2 : rapport final…");
  await page.$$eval(".toc-folio[data-find]", (els, map) => {
    for (const el of els) {
      const n = map[el.getAttribute("data-find")];
      el.textContent = n == null ? "—" : String(n);
    }
  }, folios);

  await page.pdf({ ...OPTS_COUVERTURE, pageRanges: "1", path: tCouv });
  await page.pdf({ ...OPTS, pageRanges: "2-", path: tCorps });
  execFileSync("mutool", ["merge", "-o", tFinal, tCouv, tCorps],
               { stdio: "ignore", timeout: 120000 });

  // Contrôle : chaque folio annoncé porte bien son titre sur le PDF final.
  const pages2 = pagesDuPdf(tFinal);
  if (pages2) {
    for (const [c, n] of Object.entries(folios))
      if (!norm(pages2[n - 1] || "").includes(norm(c)))
        console.warn(`  AVERTISSEMENT : « ${c} » annoncé p.${n}, introuvable sur cette page`);
  }

  // La cible est verrouillée tant qu'un lecteur PDF la tient ouverte (EBUSY),
  // et OneDrive peut la retenir un instant de plus après une synchronisation.
  // On patiente, puis on le dit clairement plutôt que de jeter une trace Node.
  for (let essai = 0; ; essai++) {
    try { copyFileSync(tFinal, CIBLE); break; }
    catch (e) {
      if (essai >= 5) {
        console.error(`\nÉCHEC : impossible d'écrire ${CIBLE}`);
        console.error("Le fichier est ouvert dans un lecteur PDF. Fermez-le et relancez ;");
        console.error(`le rapport composé est prêt ici : ${tFinal}`);
        process.exit(1);
      }
      console.log("  cible verrouillée (lecteur PDF ouvert), nouvel essai…");
      await new Promise((r) => setTimeout(r, 2500));
    }
  }
  const nPages = (pages2 || []).filter((p) => p.trim()).length;
  console.log(`Écrit rapport_corridor.pdf (${(statSync(CIBLE).size / 1e6).toFixed(2)} Mo, ${nPages} pages)`);
} finally {
  await navigateur.close();
  for (const f of [tP1, tTxt, tCouv, tCorps, tFinal, tHtml, tHtml2])
    { try { rmSync(f, { force: true }); } catch { /* rien */ } }
}
