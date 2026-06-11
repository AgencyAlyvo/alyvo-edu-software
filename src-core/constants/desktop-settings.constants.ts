/** Chemin Windscribe CLI par defaut sur Windows. */
export const DEFAULT_WINDSCRIBE_CLI_PATH: string = 'C:\\Program Files\\Windscribe\\windscribe-cli.exe'

/** Localisation Windscribe par defaut pour la rotation VPN. */
export const DEFAULT_WINDSCRIBE_LOCATION: string = 'US'

/** Nombre de comptes Outlook par lot IP (rotation VPN + flush DNS avant Chrome). */
export const OUTLOOK_ACCOUNTS_PER_VPN_ROTATION: number = 2

/** Cle API CapSolver par defaut (vide : a renseigner dans Parametres). */
export const DEFAULT_CAPSOLVER_API_KEY: string = ''

/** Nombre minimum d'instances Chrome/nodriver simultanees par workflow. */
export const MIN_SIDECAR_CONCURRENT_INSTANCES: number = 1

/** Nombre maximum d'instances Chrome/nodriver simultanees par workflow. */
export const MAX_SIDECAR_CONCURRENT_INSTANCES: number = 10

/** Instances Chrome simultanees par defaut — creation Outlook. */
export const DEFAULT_OUTLOOK_MAX_CONCURRENT_INSTANCES: number = 1

/** Instances Chrome simultanees par defaut — inscription Broward. */
export const DEFAULT_BROWARD_ENROLLMENT_MAX_CONCURRENT_INSTANCES: number = 1

/** Instances Chrome simultanees par defaut — activation Student ID Broward. */
export const DEFAULT_BROWARD_ACTIVATION_MAX_CONCURRENT_INSTANCES: number = 1

export const DESKTOP_SETTINGS_STORAGE_KEYS: {
  readonly windscribeCliPath: string
  readonly windscribeLocation: string
  readonly capsolverApiKey: string
  readonly outlookMaxConcurrentInstances: string
  readonly browardEnrollmentMaxConcurrentInstances: string
  readonly browardActivationMaxConcurrentInstances: string
} = {
  windscribeCliPath: 'alyvo.desktop.windscribeCliPath',
  windscribeLocation: 'alyvo.desktop.windscribeLocation',
  capsolverApiKey: 'alyvo.desktop.capsolverApiKey',
  outlookMaxConcurrentInstances: 'alyvo.desktop.outlookMaxConcurrentInstances',
  browardEnrollmentMaxConcurrentInstances: 'alyvo.desktop.browardEnrollmentMaxConcurrentInstances',
  browardActivationMaxConcurrentInstances: 'alyvo.desktop.browardActivationMaxConcurrentInstances',
} as const
