/**
 * Niveau d'indentation d'une ligne du journal de creation Outlook.
 */
export type JournalLineLevel = 'account' | 'step' | 'sub' | 'sidecar' | 'sidecarDetail' | 'sidecarDeep'

/**
 * Entree du journal affiche pendant la creation de comptes Outlook.
 */
export type JournalLine = {
  text: string
  level: JournalLineLevel
}

export const JOURNAL_LINE_INDENT: Record<JournalLineLevel, string> = {
  account: '',
  step: '  ',
  sub: '    ',
  sidecar: '      ',
  sidecarDetail: '        ',
  sidecarDeep: '          ',
}
