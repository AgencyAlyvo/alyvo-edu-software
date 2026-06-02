import { LogicalSize } from '@tauri-apps/api/dpi'
import { getCurrentWindow } from '@tauri-apps/api/window'
import type { Window as TauriWindow } from '@tauri-apps/api/window'

/**
 * Configuration de comportement d'une fenetre Tauri.
 */
export type TauriWindowConfiguration = {
  minWidth?: number
  minHeight?: number
  width?: number
  height?: number
  center?: boolean
  resizable: boolean
  decorations: boolean
  maximized: boolean
}

/**
 * Service dedie aux transitions et dimensions de la fenetre Tauri.
 */
export class TauriWindowService {
  /**
   * Configure la fenetre principale de l'application.
   * @param {TauriWindowConfiguration} configuration - Configuration cible de la fenetre.
   * @returns {Promise<void>}
   */
  public static async configureCurrentWindow(configuration: TauriWindowConfiguration): Promise<void> {
    const appWindow: TauriWindow = getCurrentWindow()

    await appWindow.setDecorations(configuration.decorations)
    await appWindow.setResizable(configuration.resizable)

    const minSize: LogicalSize | null =
      configuration.minWidth && configuration.minHeight
        ? new LogicalSize(configuration.minWidth, configuration.minHeight)
        : null
    await appWindow.setMinSize(minSize)

    if (configuration.width && configuration.height) {
      await appWindow.setSize(new LogicalSize(configuration.width, configuration.height))

      // Centre la fenêtre uniquement si explicitement demandé (pas lors d'une navigation interne auth).
      if (configuration.center !== false) {
        await appWindow.center()
      }
    }

    if (configuration.maximized) {
      await appWindow.maximize()
    } else if (await appWindow.isMaximized()) {
      await appWindow.unmaximize()
    }
  }

  /**
   * Configure la fenetre pour la page de connexion.
   * @param {boolean} center - Centre la fenetre si true, conserve sa position sinon.
   * @returns {Promise<void>}
   */
  public static async configureLoginWindow(center: boolean = true): Promise<void> {
    await this.configureCurrentWindow({
      width: 400,
      height: 595,
      center,
      resizable: false,
      decorations: false,
      maximized: false,
    })
  }

  /**
   * Configure la fenetre principale apres connexion.
   * @returns {Promise<void>}
   */
  public static async configureMainWindow(): Promise<void> {
    await this.configureCurrentWindow({
      minWidth: 1280,
      minHeight: 720,
      width: 1280,
      height: 720,
      resizable: true,
      decorations: false,
      maximized: true,
    })
  }
}
