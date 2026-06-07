/**
 * Maintenance : regenere data/us_*_names.txt (usage ponctuel, pas dans npm run sidecar:build).
 *   node sidecar/outlook-creator/scripts/generate-name-lists.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const outlookCreatorRoot = path.resolve(__dirname, '..')
const dataDir = path.join(outlookCreatorRoot, 'data')
const cacheDir = path.join(dataDir, '.sources')

const BABY_NAMES_URL = 'https://raw.githubusercontent.com/hadley/data-baby-names/master/baby-names.csv'
const SURNAMES_URL = 'https://raw.githubusercontent.com/fivethirtyeight/data/master/most-common-name/surnames.csv'
const SUPPLEMENTAL_FIRST_NAMES_URL = 'https://raw.githubusercontent.com/dominictarr/random-name/master/first-names.txt'

const TARGET_COUNT = 5000
const VALID_NAME = /^[A-Za-z][A-Za-z'-]*$/

/**
 * Telecharge un fichier source dans le cache local si absent.
 * @param {string} filename - Nom du fichier dans .sources.
 * @param {string} url - URL HTTP du dataset.
 * @returns {Promise<string>} Chemin absolu du fichier en cache.
 */
async function ensureSource(filename, url) {
  fs.mkdirSync(cacheDir, { recursive: true })
  const dest = path.join(cacheDir, filename)
  if (!fs.existsSync(dest)) {
    console.log(`Downloading ${url} ...`)
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`)
    fs.writeFileSync(dest, await res.text(), 'utf8')
  }
  return dest
}

/**
 * Met en forme un nom de famille en Title Case.
 * @param {string} upper - Nom en majuscules.
 * @returns {string} Nom formate.
 */
function titleCaseSurname(upper) {
  const lower = upper.toLowerCase()
  return lower.charAt(0).toUpperCase() + lower.slice(1)
}

/**
 * Normalise un prenom pour la liste Outlook.
 * @param {string} name - Prenom brut.
 * @returns {string | null} Prenom valide ou null si rejete.
 */
function normalizeFirstName(name) {
  const trimmed = name.trim()
  if (!VALID_NAME.test(trimmed)) return null
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1).toLowerCase()
}

/**
 * Fusionne deux listes jusqu'a atteindre le nombre cible.
 * @param {string[]} primary - Liste principale (prioritaire).
 * @param {string[]} secondary - Liste de complement.
 * @param {number} target - Nombre de prenoms uniques attendu.
 * @returns {string[]} Prenoms uniques.
 */
function mergeToTarget(primary, secondary, target) {
  const seen = new Set()
  const result = []

  for (const source of [primary, secondary]) {
    for (const raw of source) {
      const name = normalizeFirstName(raw)
      if (!name || seen.has(name)) continue
      seen.add(name)
      result.push(name)
      if (result.length >= target) return result
    }
  }

  throw new Error(`Only ${result.length} unique first names (need ${target})`)
}

/**
 * Parse le CSV hadley/data-baby-names et trie par popularite.
 * @param {string} csvPath - Chemin du fichier CSV.
 * @returns {string[]} Prenoms tries par score decroissant.
 */
function parseBabyNames(csvPath) {
  const lines = fs.readFileSync(csvPath, 'utf8').trim().split(/\r?\n/)
  const scores = new Map()

  for (let i = 1; i < lines.length; i++) {
    const m = lines[i].match(/^(\d+),"([^"]+)",([0-9.]+),"(boy|girl)"$/)
    if (!m) continue
    const name = m[2]
    const percent = Number(m[3])
    scores.set(name, (scores.get(name) ?? 0) + percent)
  }

  return [...scores.entries()].sort((a, b) => b[1] - a[1]).map(([name]) => name)
}

/**
 * Lit une liste de prenoms supplementaires (une ligne par nom).
 * @param {string} txtPath - Chemin du fichier texte.
 * @returns {string[]} Prenoms bruts.
 */
function parseSupplementalFirstNames(txtPath) {
  return fs
    .readFileSync(txtPath, 'utf8')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
}

/**
 * Extrait les N noms de famille les plus frequents du CSV FiveThirtyEight.
 * @param {string} csvPath - Chemin du fichier CSV.
 * @returns {string[]} Noms de famille formates.
 */
function parseSurnames(csvPath) {
  const lines = fs.readFileSync(csvPath, 'utf8').trim().split(/\r?\n/)
  const names = []
  for (let i = 1; i < lines.length && names.length < TARGET_COUNT; i++) {
    const raw = lines[i].split(',')[0]?.trim()
    if (!raw) continue
    names.push(titleCaseSurname(raw))
  }
  return names
}

/**
 * Ecrit une liste de noms dans data/ apres verification du quota.
 * @param {string} filename - Nom du fichier de sortie.
 * @param {string[]} names - Noms a ecrire.
 * @returns {void}
 */
function writeList(filename, names) {
  const unique = [...new Set(names)]
  if (unique.length < TARGET_COUNT) {
    throw new Error(`${filename}: only ${unique.length} names (need ${TARGET_COUNT})`)
  }
  const outPath = path.join(dataDir, filename)
  fs.writeFileSync(outPath, `${unique.join('\n')}\n`, 'utf8')
  console.log(`Wrote ${unique.length} names → ${outPath}`)
}

/**
 * Point d'entree : telecharge les sources et regenere us_first_names / us_last_names.
 * @returns {Promise<void>}
 */
async function main() {
  const babyPath = await ensureSource('baby-names.csv', BABY_NAMES_URL)
  const surnamesPath = await ensureSource('surnames.csv', SURNAMES_URL)
  const supplementalPath = await ensureSource('first-names-supplemental.txt', SUPPLEMENTAL_FIRST_NAMES_URL)

  const firstNames = mergeToTarget(
    parseBabyNames(babyPath),
    parseSupplementalFirstNames(supplementalPath),
    TARGET_COUNT,
  )

  writeList('us_first_names.txt', firstNames)
  writeList('us_last_names.txt', parseSurnames(surnamesPath))
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
