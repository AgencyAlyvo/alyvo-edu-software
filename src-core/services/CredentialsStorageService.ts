import { BaseDirectory, exists, mkdir, readTextFile, remove, writeTextFile } from '@tauri-apps/plugin-fs'

/**
 * Données persistées sur le disque pour la feature "Rester connecté".
 */
type StoredCredentials = {
  email: string
  password: string
  autoLogin: boolean
}

/**
 * Service de persistance des identifiants sur le système de fichiers OS.
 * Les données sont encodées en base64 avant écriture pour éviter le stockage en clair.
 *
 * L'identifiant de l'application doit être injecté via configure() au démarrage
 * (plugin Nuxt credentials-storage.client.ts) pour que le chemin du fichier
 * soit résolu selon l'environnement courant.
 *
 * Chemin résolu :
 * Windows : %APPDATA%\{identifier}\saved_credentials.dat
 * macOS   : ~/Library/Application Support/{identifier}/saved_credentials.dat
 * Linux   : ~/.local/share/{identifier}/saved_credentials.dat
 */
export class CredentialsStorageService {
  /**
   * Identifiant de l'application injecté par le plugin au démarrage.
   * Détermine le sous-dossier de stockage dans BaseDirectory.Data.
   */
  private static _identifier: string = 'fr.alyvo.prospectresearch'

  /**
   * Configure l'identifiant de l'application.
   * Doit être appelé une seule fois au démarrage via le plugin Nuxt.
   * @param {string} identifier - Identifiant bundle de l'application.
   * @returns {void}
   */
  public static configure(identifier: string): void {
    if (identifier.trim().length > 0) {
      this._identifier = identifier.trim()
    }
  }

  /**
   * Retourne le chemin du fichier de credentials relatif à BaseDirectory.Data.
   * @returns {string} Chemin relatif du fichier.
   */
  private static get credentialsFile(): string {
    return `${this._identifier}/saved_credentials.dat`
  }

  /**
   * Crée le dossier de l'application dans Data s'il n'existe pas encore.
   * Nécessaire au premier lancement avant toute lecture ou écriture.
   * @returns {Promise<void>}
   */
  private static async ensureDirectory(): Promise<void> {
    await mkdir(this._identifier, { baseDir: BaseDirectory.Data, recursive: true })
  }

  /**
   * Encode et écrit les identifiants dans le fichier Data avec autoLogin activé.
   * @param {string} email - Email de l'utilisateur.
   * @param {string} password - Mot de passe de l'utilisateur.
   * @returns {Promise<void>}
   */
  public static async save(email: string, password: string): Promise<void> {
    // Garantit que le dossier de l'application existe avant l'écriture.
    await this.ensureDirectory()

    const data: StoredCredentials = { email, password, autoLogin: true }
    const encoded: string = btoa(JSON.stringify(data))

    await writeTextFile(this.credentialsFile, encoded, { baseDir: BaseDirectory.Data })
  }

  /**
   * Lit et décode les identifiants depuis le fichier Data.
   * @returns {Promise<StoredCredentials | null>} Les identifiants ou null si le fichier n'existe pas.
   */
  public static async load(): Promise<StoredCredentials | null> {
    try {
      const fileExists: boolean = await exists(this.credentialsFile, { baseDir: BaseDirectory.Data })

      if (!fileExists) {
        return null
      }

      const encoded: string = await readTextFile(this.credentialsFile, { baseDir: BaseDirectory.Data })
      return JSON.parse(atob(encoded)) as StoredCredentials
    } catch {
      // Dossier ou fichier absent (premier lancement) — comportement normal.
      return null
    }
  }

  /**
   * Désactive l'auto-connexion sans supprimer les identifiants.
   * Appelé après une déconnexion manuelle pour pré-remplir le formulaire sans se connecter auto.
   * @returns {Promise<void>}
   */
  public static async disableAutoLogin(): Promise<void> {
    const stored: StoredCredentials | null = await this.load()

    if (!stored) {
      return
    }

    const updated: StoredCredentials = { ...stored, autoLogin: false }
    const encoded: string = btoa(JSON.stringify(updated))

    await writeTextFile(this.credentialsFile, encoded, { baseDir: BaseDirectory.Data })
  }

  /**
   * Supprime le fichier de credentials (décocher "Rester connecté").
   * @returns {Promise<void>}
   */
  public static async clear(): Promise<void> {
    try {
      const fileExists: boolean = await exists(this.credentialsFile, { baseDir: BaseDirectory.Data })

      if (fileExists) {
        await remove(this.credentialsFile, { baseDir: BaseDirectory.Data })
      }
    } catch {
      // Dossier absent — rien à supprimer.
    }
  }
}
