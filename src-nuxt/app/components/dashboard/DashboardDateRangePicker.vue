<template>
  <div ref="pickerRef" class="relative">
    <UButton
      icon="i-heroicons-calendar-days"
      :label="modelValue.label"
      color="neutral"
      variant="outline"
      :loading="loading"
      class="h-11 rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-4 font-medium text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] transition hover:border-[#485780] hover:bg-[#111c3f]"
      @click="isOpen = !isOpen"
    />

    <div
      v-if="isOpen"
      class="absolute right-0 z-30 mt-2 w-[320px] rounded-lg border border-[#2f3d67] bg-[#071022] p-3 shadow-[0_18px_48px_rgba(0,0,0,0.35)]"
    >
      <p class="px-1 text-xs font-semibold tracking-[0.16em] text-[#9a65d5] uppercase">Periode</p>

      <div class="mt-3 grid gap-1">
        <button
          v-for="preset in presets"
          :key="preset.id"
          type="button"
          class="rounded-md px-3 py-2 text-left text-sm transition"
          :class="
            modelValue.presetId === preset.id
              ? 'bg-[#16234f] font-semibold text-white'
              : 'text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white'
          "
          @click="applyPreset(preset)"
        >
          {{ preset.label }}
        </button>
      </div>

      <div class="mt-4 grid gap-3 border-t border-[#2f3d67] pt-4">
        <p class="px-1 text-xs font-medium text-[#9fb0d0]">Plage personnalisee</p>
        <UFormField label="Du" :ui="fieldUi">
          <UInputDate v-model="customFrom" granularity="day" variant="none" class="w-full" :ui="dateFieldUi" />
        </UFormField>
        <UFormField label="Au" :ui="fieldUi">
          <UInputDate v-model="customTo" granularity="day" variant="none" class="w-full" :ui="dateFieldUi" />
        </UFormField>
        <p v-if="customError" class="text-xs text-red-400">{{ customError }}</p>
        <UButton
          label="Appliquer la plage"
          class="rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-4 py-2 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)]"
          @click="applyCustomRange"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import type { CalendarDate } from '@internationalized/date'
import type { DashboardDateRange, DashboardDateRangePreset } from '#src-core/types/payload/stats.types'
import {
  calendarDateToIsoDate,
  createDashboardDateRange,
  isoDateToCalendarDate,
  listDashboardDateRangePresets,
} from '#src-nuxt/app/utils/dashboardDateRange'

/**
 * Props du selecteur de periode dashboard.
 */
type DashboardDateRangePickerProps = {
  modelValue: DashboardDateRange
  loading?: boolean
}

/**
 * Evenements du selecteur de periode dashboard.
 */
type DashboardDateRangePickerEmits = {
  'update:modelValue': [value: DashboardDateRange]
}

/**
 * Signature de l'emetteur.
 */
type DashboardDateRangePickerEmit = (event: 'update:modelValue', value: DashboardDateRange) => void

/**
 * Configuration UI des champs de formulaire.
 */
type FieldUiConfig = {
  label: string
}

/**
 * Configuration UI des champs date.
 */
type DateFieldUiConfig = {
  base: string
  segment: string
}

const fieldUi: FieldUiConfig = {
  label: 'text-xs font-medium text-[#9fb0d0]',
}

const dateFieldUi: DateFieldUiConfig = {
  base: 'h-11 w-full rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 shadow-[0_10px_24px_rgba(0,0,0,0.18)] transition hover:border-[#485780]',
  segment: 'text-[#f7f8ff] data-placeholder:text-[#626d90] focus:bg-[#1a2747] rounded px-0.5',
}

const props: DashboardDateRangePickerProps = defineProps<DashboardDateRangePickerProps>()
const emit: DashboardDateRangePickerEmit = defineEmits<DashboardDateRangePickerEmits>()

const pickerRef: Ref<HTMLElement | null> = ref(null)
const isOpen: Ref<boolean> = ref(false)

/**
 * Ferme le panneau de selection lorsqu'on clique en dehors du composant.
 * @returns {void}
 */
onClickOutside(pickerRef, (): void => {
  isOpen.value = false
})
const customFrom: Ref<CalendarDate | null> = ref(
  isoDateToCalendarDate(props.modelValue.from),
) as unknown as Ref<CalendarDate | null>
const customTo: Ref<CalendarDate | null> = ref(
  isoDateToCalendarDate(props.modelValue.to),
) as unknown as Ref<CalendarDate | null>
const customError: Ref<string | null> = ref(null)
const presets: DashboardDateRangePreset[] = listDashboardDateRangePresets()

/**
 * Applique un preset de periode.
 * @param {DashboardDateRangePreset} preset - Preset selectionne.
 * @returns {void}
 */
const applyPreset: (preset: DashboardDateRangePreset) => void = (preset: DashboardDateRangePreset): void => {
  customError.value = null
  customFrom.value = isoDateToCalendarDate(preset.from)
  customTo.value = isoDateToCalendarDate(preset.to)
  emit(
    'update:modelValue',
    createDashboardDateRange({
      from: preset.from,
      to: preset.to,
      presetId: preset.id,
    }),
  )
  isOpen.value = false
}

/**
 * Applique une plage personnalisee saisie par l'utilisateur.
 * @returns {void}
 */
const applyCustomRange: () => void = (): void => {
  customError.value = null

  const from: string | null = calendarDateToIsoDate(customFrom.value)
  const to: string | null = calendarDateToIsoDate(customTo.value)

  if (!from && !to) {
    customError.value = 'Selectionnez au moins une date de debut ou de fin.'
    return
  }

  if (from && to && from > to) {
    customError.value = 'La date de debut doit etre anterieure ou egale a la date de fin.'
    return
  }

  emit(
    'update:modelValue',
    createDashboardDateRange({
      from,
      to,
      presetId: 'custom',
    }),
  )
  isOpen.value = false
}

watch(
  (): DashboardDateRange => props.modelValue,
  (range: DashboardDateRange): void => {
    customFrom.value = isoDateToCalendarDate(range.from)
    customTo.value = isoDateToCalendarDate(range.to)
  },
)
</script>
