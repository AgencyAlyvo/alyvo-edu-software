/** Chemin Windscribe CLI par defaut sur Windows. */
export const DEFAULT_WINDSCRIBE_CLI_PATH: string = 'C:\\Program Files\\Windscribe\\windscribe-cli.exe'

/** Localisation Windscribe par defaut pour la rotation VPN. */
export const DEFAULT_WINDSCRIBE_LOCATION: string = 'US'

/** Nombre de comptes Outlook par lot IP (rotation VPN + flush DNS avant Chrome). */
export const OUTLOOK_ACCOUNTS_PER_VPN_ROTATION: number = 2

/** Cle API CapSolver par defaut (vide : a renseigner dans Parametres). */
export const DEFAULT_CAPSOLVER_API_KEY: string = ''

export const DESKTOP_SETTINGS_STORAGE_KEYS: {
  readonly windscribeCliPath: string
  readonly windscribeLocation: string
  readonly capsolverApiKey: string
} = {
  windscribeCliPath: 'alyvo.desktop.windscribeCliPath',
  windscribeLocation: 'alyvo.desktop.windscribeLocation',
  capsolverApiKey: 'alyvo.desktop.capsolverApiKey',
} as const
