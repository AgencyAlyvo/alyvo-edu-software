/**
 * Configuration UI d'un champ texte sombre.
 */
type AlyvoInputUi = {
  base: string
  leadingIcon: string
}

/**
 * Configuration UI d'un select sombre.
 */
type AlyvoSelectUi = {
  base: string
  placeholder: string
  trailingIcon: string
  content: string
  viewport: string
  item: string
  itemWrapper: string
  itemLabel: string
  itemTrailingIcon: string
}

/**
 * Configuration UI d'une zone de texte sombre.
 */
type AlyvoTextareaUi = {
  base: string
}

/**
 * Ensemble des classes partagees par les ecrans Alyvo sombres.
 */
type AlyvoDarkUi = {
  inputUi: AlyvoInputUi
  selectUi: AlyvoSelectUi
  textareaUi: AlyvoTextareaUi
  primaryButtonClass: string
  secondaryButtonClass: string
  ghostButtonClass: string
  iconGhostButtonClass: string
  infoGhostButtonClass: string
  dangerGhostButtonClass: string
  checkboxClass: string
  pageButtonClass: string
  activePageButtonClass: string
}

/**
 * Styles partages pour garder les ecrans secondaires alignes sur les pages LinkedIn.
 * @returns {AlyvoDarkUi} Classes et configurations UI communes.
 */
export const useAlyvoDarkUi: () => AlyvoDarkUi = (): AlyvoDarkUi => {
  const inputUi: AlyvoInputUi = {
    base: 'h-11 w-full rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] placeholder:text-[#626d90] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
    leadingIcon: 'text-[#9ba3bd]',
  } as const

  const selectUi: AlyvoSelectUi = {
    base: 'h-11 w-full cursor-pointer rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
    placeholder: 'truncate text-[#626d90]',
    trailingIcon: 'text-[#9ba3bd]',
    content:
      'max-h-60 w-(--reka-select-trigger-width) rounded-md border border-[#2f3d67] bg-[#071022] shadow-[0_18px_48px_rgba(0,0,0,0.35)] ring-0 origin-(--reka-select-content-transform-origin)',
    viewport: 'relative divide-y divide-[#152247] scroll-py-1 overflow-y-auto flex-1',
    item: 'group relative flex w-full items-start gap-1.5 rounded-md p-1.5 text-sm !text-[#c7d0ea] outline-none transition-colors hover:bg-[#111c3f] hover:!text-white data-[highlighted]:bg-[#111c3f] data-[highlighted]:!text-white data-[state=checked]:bg-[#16234f] data-[state=checked]:!text-white',
    itemWrapper: 'min-w-0 flex-1 !text-current',
    itemLabel: 'truncate !text-current group-data-[highlighted]:!text-white group-data-[state=checked]:!text-white',
    itemTrailingIcon:
      'text-[#9a65d5] group-data-[highlighted]:text-[#c7a8f2] group-data-[state=checked]:text-[#c7a8f2]',
  } as const

  const textareaUi: AlyvoTextareaUi = {
    base: 'min-h-24 w-full resize-y rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 py-2 text-sm text-[#f7f8ff] placeholder:text-[#626d90] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
  } as const

  const primaryButtonClass: string =
    'rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-4 py-2 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)] disabled:brightness-[0.72]'
  const secondaryButtonClass: string =
    'rounded-md border border-[#3f4f7d] bg-[#111c3f] px-4 py-2 font-semibold text-[#dfe5ff] transition hover:bg-[#182755] disabled:brightness-[0.72]'
  const ghostButtonClass: string =
    'rounded-md px-4 py-2 font-semibold text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white'
  const iconGhostButtonClass: string = 'text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white'
  const infoGhostButtonClass: string = 'text-[#8fd3ff] hover:bg-[#111c3f] hover:text-white'
  const dangerGhostButtonClass: string = 'text-red-300 hover:bg-red-500/10 hover:text-red-200'
  const checkboxClass: string = 'h-4 w-4 rounded border-[#2f3d67] bg-[#071022] accent-[#9a65d5]'
  const pageButtonClass: string =
    'inline-flex h-9 min-w-9 items-center justify-center rounded-md border border-[#2f3d67] bg-[#071022] px-3 text-sm font-semibold text-[#c7d0ea] transition hover:border-[#9a65d5] hover:bg-[#111c3f] hover:text-white disabled:cursor-not-allowed disabled:opacity-40'
  const activePageButtonClass: string =
    'inline-flex h-9 min-w-9 items-center justify-center rounded-md border border-[#9a65d5] bg-[#16234f] px-3 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(0,0,0,0.18)]'

  return {
    inputUi,
    selectUi,
    textareaUi,
    primaryButtonClass,
    secondaryButtonClass,
    ghostButtonClass,
    iconGhostButtonClass,
    infoGhostButtonClass,
    dangerGhostButtonClass,
    checkboxClass,
    pageButtonClass,
    activePageButtonClass,
  }
}
