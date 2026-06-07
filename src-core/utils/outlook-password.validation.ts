/**
 * Regles de mot de passe imposees par Microsoft lors de la creation Outlook.
 */
export const OUTLOOK_PASSWORD_REQUIREMENTS_MESSAGE: string =
  'Les mots de passe doivent contenir au moins 8 caractères et inclure une combinaison de majuscules, de minuscules, de chiffres et de symboles.'

/**
 * Verifie qu'un mot de passe respecte les exigences Outlook.
 * @param {string} password - Mot de passe a valider.
 * @returns {boolean} True si le mot de passe est accepte par les regles Outlook.
 */
export function isValidOutlookPassword(password: string): boolean {
  if (password.length < 8) {
    return false
  }

  if (!/[A-Z]/.test(password)) {
    return false
  }

  if (!/[a-z]/.test(password)) {
    return false
  }

  if (!/[0-9]/.test(password)) {
    return false
  }

  if (!/[^A-Za-z0-9]/.test(password)) {
    return false
  }

  return true
}
