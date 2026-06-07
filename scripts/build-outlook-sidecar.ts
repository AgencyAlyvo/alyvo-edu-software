/**
 * Script de build du sidecar Outlook (Python + nodriver embarques via PyInstaller).
 *
 * Contexte :
 * - Le sidecar est un executable autonome bundle dans l'app Tauri (`externalBin`).
 * - Tauri attend un fichier par plateforme : `outlook-creator-{TARGET_TRIPLE}` (+ `.exe` sur Windows).
 *
 * Etapes :
 * 1. Detecte le triple hote via `rustc --print host-tuple` (ex. `x86_64-pc-windows-msvc`).
 * 2. Trouve un interpreteur Python (`python`, `python3` ou `py`).
 * 3. Installe les dependances depuis `sidecar/outlook-creator/requirements.txt`.
 * 4. Lance PyInstaller avec `outlook-creator.spec` (--onefile).
 * 5. Copie le binaire produit vers `src-tauri/binaries/outlook-creator-{triple}`.
 *
 * Usage : `npm run sidecar:build` (a lancer sur chaque OS/arch cible, y compris en dev local).
 * Prerequis : Python 3.14.5, Chrome/Chromium sur la machine cible au runtime (pas au build).
 */
import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'

const rootDir: string = path.resolve(import.meta.dirname, '..')
const sidecarDir: string = path.join(rootDir, 'sidecar', 'outlook-creator')
const binariesDir: string = path.join(rootDir, 'src-tauri', 'binaries')
const distDir: string = path.join(sidecarDir, 'dist')

const extension: string = process.platform === 'win32' ? '.exe' : ''
const targetTriple: string = execSync('rustc --print host-tuple', { encoding: 'utf8' }).trim()

if (!targetTriple) {
  console.error('Failed to determine platform target triple')
  process.exit(1)
}

console.log(`Building outlook-creator sidecar for ${targetTriple}...`)

const pythonCommands: string[] = ['python', 'python3', 'py']

let pythonBin: string | null = null

for (const candidate of pythonCommands) {
  try {
    execSync(`${candidate} --version`, { stdio: 'ignore' })
    pythonBin = candidate
    break
  } catch {
    // essaie le candidat suivant
  }
}

if (!pythonBin) {
  console.error('Python not found. Install Python 3.14.5 then run: npm run sidecar:build')
  process.exit(1)
}

const pythonVersion: string = execSync(`${pythonBin} --version`, { encoding: 'utf8' }).trim()

if (!pythonVersion.includes('3.14.5')) {
  console.error(`Python 3.14.5 required for the outlook sidecar. Found: ${pythonVersion}`)
  process.exit(1)
}

console.log(`Using ${pythonVersion}`)

execSync(`${pythonBin} -m pip install -r requirements.txt`, {
  cwd: sidecarDir,
  stdio: 'inherit',
})

console.log('Patching nodriver network.py encoding for Python 3.14...')
execSync(`${pythonBin} patch_nodriver_encoding.py`, {
  cwd: sidecarDir,
  stdio: 'inherit',
})

execSync(`${pythonBin} -m PyInstaller --noconfirm outlook-creator.spec`, {
  cwd: sidecarDir,
  stdio: 'inherit',
})

const builtPath: string = path.join(distDir, `outlook-creator${extension}`)
const destPath: string = path.join(binariesDir, `outlook-creator-${targetTriple}${extension}`)

if (!fs.existsSync(builtPath)) {
  console.error(`Built binary not found: ${builtPath}`)
  process.exit(1)
}

fs.mkdirSync(binariesDir, { recursive: true })
fs.copyFileSync(builtPath, destPath)
console.log(`Sidecar installed: ${destPath}`)
