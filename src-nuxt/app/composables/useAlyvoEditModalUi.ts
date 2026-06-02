/**
 * Configuration UI d'une modale d'edition.
 */
type AlyvoModalUi = {
  overlay: string
  content: string
  close: string
}

/**
 * Configuration UI d'un champ de formulaire modale.
 */
type AlyvoModalFieldUi = {
  label: string
  container: string
}

/**
 * Configuration UI d'un input modale.
 */
type AlyvoModalInputUi = {
  base: string
}

/**
 * Configuration UI d'un select modale.
 */
type AlyvoModalSelectUi = {
  base: string
  trailingIcon: string
  content: string
  viewport: string
  item: string
  itemWrapper: string
  itemLabel: string
  itemTrailingIcon: string
}

/**
 * Configuration UI d'un champ date modale.
 */
type AlyvoModalDateFieldUi = {
  base: string
  segment: string
}

/**
 * Ensemble des styles partages des modales d'edition.
 */
type AlyvoEditModalUi = {
  modalUi: AlyvoModalUi
  fieldUi: AlyvoModalFieldUi
  inputUi: AlyvoModalInputUi
  selectUi: AlyvoModalSelectUi
  dateFieldUi: AlyvoModalDateFieldUi
  textareaClass: string
}

/**
 * Styles partages des modales d'edition (LinkedIn, business local).
 * @returns {AlyvoEditModalUi} Configurations UI communes.
 */
export const useAlyvoEditModalUi: () => AlyvoEditModalUi = (): AlyvoEditModalUi => {
  const modalUi: AlyvoModalUi = {
    overlay: 'bg-[#020617]/80 backdrop-blur-sm',
    content:
      'max-h-[calc(100vh-2rem)] w-[calc(100vw-2rem)] max-w-2xl overflow-y-auto rounded-lg border border-[#2f3d67] bg-[#071022] text-white shadow-[0_24px_80px_rgba(0,0,0,0.45)] ring-0 divide-y-0',
    close: 'text-[#9ba3bd] hover:text-white hover:bg-[#111c3f]',
  } as const

  const fieldUi: AlyvoModalFieldUi = {
    label: 'text-[#c7d0ea] font-medium',
    container: 'mt-1.5',
  } as const

  const inputUi: AlyvoModalInputUi = {
    base: 'h-11 rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] placeholder:text-[#626d90] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
  } as const

  const selectUi: AlyvoModalSelectUi = {
    base: 'h-11 w-full cursor-pointer rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5]',
    trailingIcon: 'text-[#9ba3bd]',
    content:
      'max-h-60 w-(--reka-select-trigger-width) rounded-md border border-[#2f3d67] bg-[#071022] shadow-[0_18px_48px_rgba(0,0,0,0.35)] ring-0 origin-(--reka-select-content-transform-origin)',
    viewport: 'relative divide-y divide-[#152247] scroll-py-1 overflow-y-auto flex-1',
    item: 'group relative flex w-full items-start gap-1.5 rounded-md p-1.5 text-sm !text-[#c7d0ea] outline-none transition-colors hover:bg-[#111c3f] hover:!text-white data-[highlighted]:bg-[#111c3f] data-[highlighted]:!text-white data-[state=checked]:bg-[#16234f] data-[state=checked]:!text-white',
    itemWrapper: 'min-w-0 flex-1 !text-current',
    itemLabel: '!text-current group-data-[highlighted]:!text-white group-data-[state=checked]:!text-white',
    itemTrailingIcon:
      'text-[#9a65d5] group-data-[highlighted]:text-[#c7a8f2] group-data-[state=checked]:text-[#c7a8f2]',
  } as const

  const dateFieldUi: AlyvoModalDateFieldUi = {
    base: 'h-11 w-full rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 shadow-[0_10px_24px_rgba(0,0,0,0.18)] transition hover:border-[#485780]',
    segment: 'text-[#f7f8ff] data-placeholder:text-[#626d90] focus:bg-[#1a2747] rounded px-0.5',
  } as const

  const textareaClass: string =
    'min-h-20 w-full resize-y rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 py-2 text-sm text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]'

  return { modalUi, fieldUi, inputUi, selectUi, dateFieldUi, textareaClass }
}
