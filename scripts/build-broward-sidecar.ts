/**
 * Build PyInstaller du sidecar broward-enrollment pour Tauri externalBin.
 */
import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'

const rootDir: string = path.resolve(import.meta.dirname, '..')
const sidecarDir: string = path.join(rootDir, 'sidecar', 'broward-enrollment')
const outlookSidecarDir: string = path.join(rootDir, 'sidecar', 'outlook-creator')
const binariesDir: string = path.join(rootDir, 'src-tauri', 'binaries')
const distDir: string = path.join(sidecarDir, 'dist')

const extension: string = process.platform === 'win32' ? '.exe' : ''
const targetTriple: string = execSync('rustc --print host-tuple', { encoding: 'utf8' }).trim()

if (!targetTriple) {
  console.error('Failed to determine platform target triple')
  process.exit(1)
}

console.log(`Building broward-enrollment sidecar for ${targetTriple}...`)

const pythonCommands: string[] = ['python', 'python3', 'py']

let pythonBin: string | null = null

for (const candidate of pythonCommands) {
  try {
    execSync(`${candidate} --version`, { stdio: 'ignore' })
    pythonBin = candidate
    break
  } catch {
    // next
  }
}

if (!pythonBin) {
  console.error('Python not found. Install Python 3.14.5 then run: npm run sidecar:build:broward')
  process.exit(1)
}

const pythonVersion: string = execSync(`${pythonBin} --version`, { encoding: 'utf8' }).trim()

if (!pythonVersion.includes('3.14.5')) {
  console.error(`Python 3.14.5 required for the broward sidecar. Found: ${pythonVersion}`)
  process.exit(1)
}

console.log(`Using ${pythonVersion}`)

execSync(`${pythonBin} -m pip install -r requirements.txt`, {
  cwd: sidecarDir,
  stdio: 'inherit',
})

console.log('Patching nodriver network.py encoding for Python 3.14...')
execSync(`${pythonBin} patch_nodriver_encoding.py`, {
  cwd: outlookSidecarDir,
  stdio: 'inherit',
})

console.log('Verifying nodriver import...')
execSync(`${pythonBin} -c "import nodriver; print('nodriver import ok')"`, {
  cwd: sidecarDir,
  stdio: 'inherit',
})

execSync(`${pythonBin} -m PyInstaller --noconfirm broward-enrollment.spec`, {
  cwd: sidecarDir,
  stdio: 'inherit',
})

const builtPath: string = path.join(distDir, `broward-enrollment${extension}`)
const destPath: string = path.join(binariesDir, `broward-enrollment-${targetTriple}${extension}`)

if (!fs.existsSync(builtPath)) {
  console.error(`Built binary not found: ${builtPath}`)
  process.exit(1)
}

fs.mkdirSync(binariesDir, { recursive: true })
fs.copyFileSync(builtPath, destPath)
console.log(`Sidecar installed: ${destPath}`)
