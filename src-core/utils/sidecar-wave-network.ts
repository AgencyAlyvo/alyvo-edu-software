import { OUTLOOK_ACCOUNTS_PER_VPN_ROTATION } from '#src-core/constants/desktop-settings.constants'
import { OutlookBatchVpnService } from '#src-core/services/OutlookBatchVpnService'
import { waitForNoActiveSidecarSlots } from '#src-core/utils/sidecar-wave-coordinator'

/**
 * Prepare le reseau (VPN + flush DNS) avant une vague de sidecars.
 * @param {object} options - Contexte vague et VPN.
 * @returns {Promise<void>}
 */
export async function prepareSidecarWaveNetwork(options: {
  index: number
  maxConcurrent: number
  isVpnConfigured: boolean
  windscribeCliPath: string
  windscribeLocation: string
  onStepLog: (line: string) => void
  onSubLog: (line: string) => void
}): Promise<void> {
  const {
    index,
    maxConcurrent,
    isVpnConfigured,
    windscribeCliPath,
    windscribeLocation,
    onStepLog,
    onSubLog,
  } = options

  if (maxConcurrent > 1) {
    const isWaveStart: boolean = index % maxConcurrent === 0
    const waveNumber: number = Math.floor(index / maxConcurrent) + 1

    if (!isWaveStart) {
      return
    }

    if (index > 0) {
      onSubLog('Attente : fin des instance(s) Chrome de la vague precedente...')
      await waitForNoActiveSidecarSlots()
    }

    if (isVpnConfigured) {
      onStepLog(
        `Reseau : Windscribe (${windscribeLocation}), flush DNS, puis jusqu'a ${maxConcurrent} Chrome(s) (vague ${waveNumber}).`,
      )
      await OutlookBatchVpnService.prepareBeforeChrome({
        windscribeCliPath,
        location: windscribeLocation,
        closeChromeFirst: false,
        batchNumber: waveNumber,
        onLog: onSubLog,
      })
    } else if (index === 0) {
      onStepLog('Reseau : Windscribe non configure (voir Parametres).')
    }

    return
  }

  const isStartOfVpnBatch: boolean = index % OUTLOOK_ACCOUNTS_PER_VPN_ROTATION === 0
  const batchNumber: number = Math.floor(index / OUTLOOK_ACCOUNTS_PER_VPN_ROTATION) + 1
  const accountInBatch: number = (index % OUTLOOK_ACCOUNTS_PER_VPN_ROTATION) + 1

  if (isStartOfVpnBatch) {
    if (isVpnConfigured) {
      onStepLog(
        `Reseau : Windscribe (${windscribeLocation}), flush DNS, puis Chrome (lot ${batchNumber}).`,
      )
      await OutlookBatchVpnService.prepareBeforeChrome({
        windscribeCliPath,
        location: windscribeLocation,
        closeChromeFirst: index > 0,
        batchNumber,
        onLog: onSubLog,
      })
    } else if (index === 0) {
      onStepLog('Reseau : Windscribe non configure (voir Parametres).')
    } else {
      onStepLog(`Reseau : lot ${batchNumber} sans changement d'IP (configurez windscribe-cli.exe).`)
    }
  } else if (index > 0) {
    onStepLog(
      `Meme lot VPN (${accountInBatch}/${OUTLOOK_ACCOUNTS_PER_VPN_ROTATION}) : fermeture de Chrome avant relance.`,
    )
    await OutlookBatchVpnService.ensureChromeClosedBeforeSidecar(onSubLog)
  }
}
