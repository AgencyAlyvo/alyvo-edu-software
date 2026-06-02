/**
 * Indique si le filtre « favoris uniquement » est actif (select ou query API).
 * @param {unknown} value - Valeur du select ou du query param.
 * @returns {boolean} True si seuls les favoris sont demandes.
 */
export const isFavoriteOnlyFilter: (value: unknown) => boolean = (value: unknown): boolean =>
  value === true || value === 'true' || value === 1 || value === '1'
