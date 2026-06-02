import {
  linkedinSelectableStatusLabels,
  linkedinStatusBadgeStyles,
  type LinkedinStatusBadgeColor,
} from '#src-core/constants/linkedinSelectableStatuses'
import { localBusinessStatusBadgeStyles } from '#src-core/constants/localBusinessSelectableStatuses'
import { LinkedinProspectStatus } from '#src-core/types/enums/linkedin.enums'
import { LocalBusinessStatus, LocalBusinessStatusLabels } from '#src-core/types/enums/local-business.enums'

/**
 * Configuration visuelle d'un badge de statut.
 */
export type StatusBadgeConfig = {
  label: string
  className: string
  color: LinkedinStatusBadgeColor
}

const defaultBadge: StatusBadgeConfig = {
  label: linkedinSelectableStatusLabels[LinkedinProspectStatus.A_INVITER],
  color: 'primary',
  className: 'bg-purple-700',
}

/**
 * Retourne la couleur Nuxt UI pour un statut business local.
 * @param {LocalBusinessStatus} status - Statut business local.
 * @returns {LinkedinStatusBadgeColor} Couleur du badge.
 */
const getLocalBusinessBadgeColor: (status: LocalBusinessStatus) => LinkedinStatusBadgeColor = (
  status: LocalBusinessStatus,
): LinkedinStatusBadgeColor => {
  switch (status) {
    case LocalBusinessStatus.EMAIL_ENVOYE:
    case LocalBusinessStatus.APPEL_PASSE:
    case LocalBusinessStatus.RELANCE_1_ENVOYEE:
    case LocalBusinessStatus.RELANCE_2_ENVOYEE:
    case LocalBusinessStatus.RELANCE_3_ENVOYEE:
      return 'info'
    case LocalBusinessStatus.REPONDU_INTERESSE:
    case LocalBusinessStatus.APPEL_DECOUVERTE_FAIT:
    case LocalBusinessStatus.APPEL_DE_VENTE_FAIT:
    case LocalBusinessStatus.PROPOSITION_ACCEPTEE:
      return 'success'
    case LocalBusinessStatus.REPONDU_NON_INTERESSE:
    case LocalBusinessStatus.PROPOSITION_REFUSEE:
      return 'error'
    case LocalBusinessStatus.NON_REPONDU:
    case LocalBusinessStatus.ARCHIVE:
      return 'neutral'
    default:
      return 'primary'
  }
}

/**
 * Libelles et couleurs des statuts LinkedIn.
 * @returns {{ getStatusBadge: (status?: LinkedinProspectStatus | string | null) => StatusBadgeConfig }} Helpers de badge.
 */
export const useStatusBadge: () => {
  getStatusBadge: (status?: LinkedinProspectStatus | string | null) => StatusBadgeConfig
} = (): { getStatusBadge: (status?: LinkedinProspectStatus | string | null) => StatusBadgeConfig } => {
  /**
   * Retourne la configuration d'un statut.
   * @param {LinkedinProspectStatus | string | null | undefined} status - Statut brut.
   * @returns {StatusBadgeConfig} Configuration visuelle.
   */
  const getStatusBadge: (status?: LinkedinProspectStatus | string | null) => StatusBadgeConfig = (
    status?: LinkedinProspectStatus | string | null,
  ): StatusBadgeConfig => {
    const key: string = String(status ?? '')
    const styles: { color: LinkedinStatusBadgeColor; className: string } | undefined =
      linkedinStatusBadgeStyles[key as LinkedinProspectStatus]
    const label: string | undefined = linkedinSelectableStatusLabels[key as LinkedinProspectStatus]

    if (!styles || !label) {
      const localLabel: string | undefined = LocalBusinessStatusLabels[key as LocalBusinessStatus]
      const localClassName: string | undefined = localBusinessStatusBadgeStyles[key as LocalBusinessStatus]

      if (localLabel && localClassName) {
        return {
          label: localLabel,
          color: getLocalBusinessBadgeColor(key as LocalBusinessStatus),
          className: localClassName,
        }
      }

      return defaultBadge
    }

    return { label, ...styles }
  }

  return { getStatusBadge }
}
