/**
 * Fusionne des filtres de liste : les cles presentes a `undefined` dans `incoming` sont retirees.
 * @template T
 * @param {T} current - Filtres courants.
 * @param {Partial<T>} incoming - Mise a jour (ex. formulaire ou pagination).
 * @returns {T} Filtres fusionnes.
 */
export const mergeListQueryFilters: <T extends Record<string, unknown>>(current: T, incoming: Partial<T>) => T = <
  T extends Record<string, unknown>,
>(
  current: T,
  incoming: Partial<T>,
): T => {
  const next: T = { ...current, ...incoming }
  for (const key of Object.keys(incoming) as (keyof T)[]) {
    if (incoming[key] === undefined) {
      delete next[key]
    }
  }
  return next
}
