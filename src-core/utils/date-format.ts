/**
 * Formate une date ISO (YYYY-MM-DD ou datetime) pour affichage jour/mois/annee.
 * @param {string | null | undefined} value - Date ISO ou vide.
 * @returns {string} Date formatee en locale fr-FR ou tiret cadratin.
 */
export function formatIsoDate(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }

  const datePart: string = value.includes('T') ? value.split('T')[0]! : value.slice(0, 10)
  const date: Date = new Date(`${datePart}T12:00:00`)

  if (Number.isNaN(date.getTime())) {
    return '—'
  }

  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/**
 * Formate une date ISO pour affichage date et heure dans l'interface.
 * @param {string | null | undefined} value - Date ISO ou vide.
 * @returns {string} Date/heure formatee en locale fr-FR ou tiret cadratin.
 */
export function formatIsoDateTime(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }

  const date: Date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '—'
  }

  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
