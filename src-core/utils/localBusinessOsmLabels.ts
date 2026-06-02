/**
 * Formate une valeur de tag OSM (shop=stationery, etc.) pour l'affichage.
 * @param {string} value - Valeur brute du tag.
 * @returns {string} Libelle lisible.
 */
export const formatLocalBusinessOsmTagValue: (value: string) => string = (value: string): string =>
  value
    .replace(/_/g, ' ')
    .split(' ')
    .map((word: string): string => (word.length > 0 ? `${word.charAt(0).toUpperCase()}${word.slice(1)}` : word))
    .join(' ')
