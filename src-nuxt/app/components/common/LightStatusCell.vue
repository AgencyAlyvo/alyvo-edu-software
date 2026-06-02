<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      :title="currentLabel"
      :aria-haspopup="'listbox'"
      :aria-expanded="open"
      class="flex h-10 w-full cursor-pointer items-center justify-between gap-2 rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-left text-sm text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] transition outline-none hover:border-[#485780] focus:border-[#9a65d5]"
      @click.stop="toggle"
    >
      <span class="block min-w-0 truncate">{{ currentLabel }}</span>
      <UIcon name="i-heroicons-chevron-down" class="h-4 w-4 shrink-0 text-[#9ba3bd]" />
    </button>
    <Teleport v-if="open" to="body">
      <div
        :style="floatStyle"
        class="fixed z-[2000] max-h-60 min-w-[200px] overflow-y-auto rounded-md border border-[#2f3d67] bg-[#071022] py-1 shadow-[0_18px_48px_rgba(0,0,0,0.35)]"
        role="listbox"
        @click.stop
      >
        <button
          v-for="item in items"
          :key="String(item.value)"
          type="button"
          role="option"
          :aria-selected="item.value === modelValue"
          :class="[
            'flex w-full cursor-pointer items-center px-3 py-2 text-left text-sm transition-colors',
            item.value === modelValue
              ? 'bg-[#16234f] text-white'
              : 'text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white',
          ]"
          @click="select(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script lang="ts" setup generic="T extends string">
import type { Ref } from 'vue'

/**
 * Item de selection.
 */
type StatusItem = {
  label: string
  value: T
}

/**
 * Props du selecteur de statut leger.
 */
type LightStatusCellProps = {
  modelValue: T
  items: readonly StatusItem[]
}

/**
 * Evenements emis.
 */
type LightStatusCellEmits = {
  'update:modelValue': [value: T]
}

const props: LightStatusCellProps = defineProps<LightStatusCellProps>()
const emit: (event: 'update:modelValue', value: T) => void = defineEmits<LightStatusCellEmits>()

const rootRef: Ref<HTMLDivElement | null> = ref(null)
const open: Ref<boolean> = ref(false)
const floatStyle: Ref<Record<string, string>> = ref({})

const currentLabel: ComputedRef<string> = computed((): string => {
  const found: StatusItem | undefined = props.items.find((item: StatusItem): boolean => item.value === props.modelValue)
  return found ? found.label : String(props.modelValue)
})

/**
 * Recalcule la position du popover sous le bouton.
 * @returns {void}
 */
const updatePosition: () => void = (): void => {
  const root: HTMLDivElement | null = rootRef.value
  if (!root) return
  const rect: DOMRect = root.getBoundingClientRect()
  const desiredTop: number = rect.bottom + 4
  const viewportHeight: number = window.innerHeight
  const popoverEstimatedHeight: number = 240
  const flipUp: boolean = desiredTop + popoverEstimatedHeight > viewportHeight && rect.top > popoverEstimatedHeight
  const top: number = flipUp ? rect.top - popoverEstimatedHeight - 4 : desiredTop
  floatStyle.value = {
    top: `${top}px`,
    left: `${rect.left}px`,
    minWidth: `${rect.width}px`,
  }
}

/**
 * Ferme le popover.
 * @returns {void}
 */
const close: () => void = (): void => {
  open.value = false
}

/**
 * Gestionnaire de clic en dehors.
 * @param {Event} event - Evenement de clic.
 * @returns {void}
 */
const onDocumentClick: (event: Event) => void = (event: Event): void => {
  const root: HTMLDivElement | null = rootRef.value
  if (!root) return
  const target: Node | null = event.target as Node | null
  if (target && root.contains(target)) return
  close()
}

/**
 * Gestionnaire d'echappement.
 * @param {KeyboardEvent} event - Evenement clavier.
 * @returns {void}
 */
const onKeydown: (event: KeyboardEvent) => void = (event: KeyboardEvent): void => {
  if (event.key === 'Escape') close()
}

watch(open, async (value: boolean): Promise<void> => {
  if (!value) {
    if (typeof window !== 'undefined') {
      document.removeEventListener('mousedown', onDocumentClick, true)
      document.removeEventListener('keydown', onKeydown)
      window.removeEventListener('scroll', updatePosition, true)
      window.removeEventListener('resize', updatePosition)
    }
    return
  }
  updatePosition()
  await nextTick()
  if (typeof window !== 'undefined') {
    document.addEventListener('mousedown', onDocumentClick, true)
    document.addEventListener('keydown', onKeydown)
    window.addEventListener('scroll', updatePosition, true)
    window.addEventListener('resize', updatePosition)
  }
})

onBeforeUnmount((): void => {
  if (typeof window !== 'undefined') {
    document.removeEventListener('mousedown', onDocumentClick, true)
    document.removeEventListener('keydown', onKeydown)
    window.removeEventListener('scroll', updatePosition, true)
    window.removeEventListener('resize', updatePosition)
  }
})

/**
 * Bascule l'ouverture du popover.
 * @returns {void}
 */
const toggle: () => void = (): void => {
  open.value = !open.value
}

/**
 * Selectionne une valeur.
 * @param {T} value - Valeur selectionnee.
 * @returns {void}
 */
const select: (value: T) => void = (value: T): void => {
  emit('update:modelValue', value)
  close()
}
</script>
