import type { Child } from '@tauri-apps/plugin-shell'

/**
 * Gere plusieurs processus sidecar actifs et l'arret global.
 */
export class SidecarActiveChildren {
  private readonly children: Set<Child> = new Set()

  /**
   * @param {object} stopSignal - Flag d'arret partage.
   */
  public constructor(private readonly stopSignal: { requested: boolean }) {}

  /**
   * Reinitialise le flag d'arret avant un nouveau lancement.
   * @returns {void}
   */
  public resetStopSignal(): void {
    this.stopSignal.requested = false
  }

  /**
   * @returns {boolean} True si arret demande.
   */
  public isStopRequested(): boolean {
    return this.stopSignal.requested
  }

  /**
   * Enregistre un processus sidecar actif.
   * @param {Child} child - Processus Tauri.
   * @returns {void}
   */
  public register(child: Child): void {
    this.children.add(child)
  }

  /**
   * Retire un processus sidecar termine.
   * @param {Child} child - Processus Tauri.
   * @returns {void}
   */
  public unregister(child: Child): void {
    this.children.delete(child)
  }

  /**
   * Demande l'arret et tue tous les sidecars actifs.
   * @returns {Promise<boolean>} True si au moins un processus a ete tue.
   */
  public async stopAll(): Promise<boolean> {
    this.stopSignal.requested = true
    const snapshot: Child[] = [...this.children]

    if (snapshot.length === 0) {
      return false
    }

    await Promise.all(snapshot.map((child: Child) => child.kill()))

    return true
  }
}
