import { invoke } from '@tauri-apps/api/core'

import type { DesktopCliRunResult } from '#src-core/types/response/desktop-cli.types'

/**
 * Reponse brute renvoyee par les commandes Tauri desktop-automation.
 */
type RawCliRunResult = {
  exit_code: number
  stdout: string
  stderr: string
}

/**
 * Execute des commandes systeme via le backend Tauri (chemins configurables).
 */
export class DesktopCliService {
  /**
   * Lance un executable avec des arguments.
   * @param {string} program - Chemin absolu de l'executable.
   * @param {string[]} args - Arguments de ligne de commande.
   * @returns {Promise<DesktopCliRunResult>} Code de sortie et flux stdout/stderr.
   */
  public static async runProgram(program: string, args: string[]): Promise<DesktopCliRunResult> {
    const raw: RawCliRunResult = await invoke<RawCliRunResult>('run_cli_program', {
      program: program.trim(),
      args,
    })

    return {
      exitCode: raw.exit_code,
      stdout: raw.stdout,
      stderr: raw.stderr,
    }
  }

  /**
   * Ferme Chrome et Chromium sur Windows.
   * @returns {Promise<DesktopCliRunResult>} Resultat de la commande taskkill.
   */
  public static async closeChromeProcesses(): Promise<DesktopCliRunResult> {
    const raw: RawCliRunResult = await invoke<RawCliRunResult>('close_chrome_processes')

    return {
      exitCode: raw.exit_code,
      stdout: raw.stdout,
      stderr: raw.stderr,
    }
  }

  /**
   * Vide le cache DNS Windows.
   * @returns {Promise<DesktopCliRunResult>} Resultat de ipconfig /flushdns.
   */
  public static async flushDnsWindows(): Promise<DesktopCliRunResult> {
    const raw: RawCliRunResult = await invoke<RawCliRunResult>('flush_dns_windows')

    return {
      exitCode: raw.exit_code,
      stdout: raw.stdout,
      stderr: raw.stderr,
    }
  }
}
