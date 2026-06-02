<template>
  <div class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
    <div v-if="loading" class="p-6 text-sm text-[#9ba3bd]">Chargement...</div>

    <EmptyState
      v-else-if="safeRelances.length === 0"
      title="Aucune relance LinkedIn"
      description="Aucune relance due pour le moment. Les echeances sont calculees depuis la date du message 1 et vos delais dans les parametres LinkedIn."
    />

    <div v-else class="overflow-x-auto">
      <table class="w-full min-w-[900px] text-left text-sm">
        <thead class="border-b border-[#2f3d67] text-xs text-[#9ba3bd] uppercase">
          <tr>
            <th class="px-4 py-3">Prospect</th>
            <th class="px-4 py-3">Relance</th>
            <th class="px-4 py-3">Message 1 envoye</th>
            <th class="px-4 py-3">Echeance</th>
            <th class="px-4 py-3">Retard</th>
            <th class="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in safeRelances"
            :key="`${item.prospect.id}-${item.relanceNumber}`"
            class="cursor-pointer border-b border-[#1a2747] text-[#dfe6ff] last:border-0 hover:bg-[#111c35]"
            @click="navigateToProspect(item.prospect.id)"
          >
            <td class="px-4 py-3">
              <p class="font-medium text-white">{{ item.prospect.firstName }} {{ item.prospect.lastName }}</p>
              <p class="mt-1 text-xs text-[#9ba3bd]">{{ item.prospect.company ?? 'Entreprise non renseignee' }}</p>
            </td>
            <td class="px-4 py-3 font-medium text-[#c7a8f2]">Relance {{ item.relanceNumber }}</td>
            <td class="px-4 py-3 text-[#c7d0ea]">{{ formatDate(item.message1SentAt) }}</td>
            <td class="px-4 py-3 text-[#c7d0ea]">{{ formatDate(item.dueAt) }}</td>
            <td class="px-4 py-3">
              <span
                class="rounded-md px-2 py-1 text-xs font-semibold"
                :class="item.daysOverdue > 0 ? 'bg-red-500/15 text-red-300' : 'bg-[#16234f] text-[#cbb6ff]'"
              >
                {{ item.daysOverdue > 0 ? `${item.daysOverdue} j` : 'Aujourd hui' }}
              </span>
            </td>
            <td class="px-4 py-3" @click.stop>
              <div class="flex flex-wrap gap-2">
                <UButton
                  size="xs"
                  label="Marquer envoyee"
                  :loading="isMarking(item.prospect.id)"
                  class="rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-3 py-1.5 font-semibold text-white"
                  @click="markRelanceSent(item)"
                />
                <NuxtLink
                  :to="`/home/linkedin/${item.prospect.id}`"
                  class="inline-flex items-center gap-1 rounded-md border border-[#2f3d67] px-3 py-1.5 text-xs text-[#c7a8f2] transition-colors hover:border-[#9a65d5] hover:text-white"
                >
                  <UIcon name="i-heroicons-arrow-top-right-on-square" class="h-4 w-4 shrink-0" />
                  <span>Fiche</span>
                </NuxtLink>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ProspectActionType } from '#src-core/types/enums/linkedin.enums'
import type { DueRelance } from '#src-core/types/response/relances.types'
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'
import { useTasksStore } from '#src-nuxt/app/stores/tasks.store'
import { formatParisDate } from '#src-nuxt/app/utils/parisTime'

/**
 * Props de la table de relances LinkedIn.
 */
type TasksTableProps = {
  relances?: DueRelance[]
  loading?: boolean
}

const props: TasksTableProps = withDefaults(defineProps<TasksTableProps>(), {
  /**
   * Retourne la liste vide par defaut.
   * @returns {DueRelance[]} Liste vide.
   */
  relances: (): DueRelance[] => [],
  loading: false,
})

const router: ReturnType<typeof useRouter> = useRouter()
const toast: ReturnType<typeof useToast> = useToast()
const prospectsStore: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()
const tasksStore: ReturnType<typeof useTasksStore> = useTasksStore()
const markingIds: Ref<Set<number>> = ref(new Set<number>())

const safeRelances: ComputedRef<DueRelance[]> = computed((): DueRelance[] => props.relances ?? [])

const relanceActionTypes: Record<1 | 2 | 3, ProspectActionType> = {
  1: ProspectActionType.RELANCE_1,
  2: ProspectActionType.RELANCE_2,
  3: ProspectActionType.RELANCE_3,
}

/**
 * Navigue vers la fiche d'un prospect.
 * @param {number} id - Identifiant du prospect.
 * @returns {Promise<void>}
 */
const navigateToProspect: (id: number) => Promise<void> = async (id: number): Promise<void> => {
  await router.push(`/home/linkedin/${id}`)
}

/**
 * Indique si un prospect est en cours de marquage.
 * @param {number} id - Identifiant du prospect.
 * @returns {boolean} True si une action est en cours.
 */
const isMarking: (id: number) => boolean = (id: number): boolean => markingIds.value.has(id)

/**
 * Marque ou retire un prospect de l'etat de chargement local.
 * @param {number} id - Identifiant du prospect.
 * @param {boolean} value - Etat de chargement.
 * @returns {void}
 */
const setMarking: (id: number, value: boolean) => void = (id: number, value: boolean): void => {
  const next: Set<number> = new Set(markingIds.value)
  if (value) {
    next.add(id)
  } else {
    next.delete(id)
  }
  markingIds.value = next
}

/**
 * Marque une relance comme envoyee puis recharge la liste.
 * @param {DueRelance} item - Relance a marquer.
 * @returns {Promise<void>}
 */
const markRelanceSent: (item: DueRelance) => Promise<void> = async (item: DueRelance): Promise<void> => {
  const actionType: ProspectActionType = relanceActionTypes[item.relanceNumber]
  setMarking(item.prospect.id, true)
  try {
    await prospectsStore.markAction(item.prospect.id, { actionType })
    await tasksStore.fetchDue()
    toast.add({
      title: 'Relance enregistree',
      description: `Relance ${item.relanceNumber} marquee comme envoyee.`,
      color: 'success',
      duration: 3000,
    })
  } finally {
    setMarking(item.prospect.id, false)
  }
}

/**
 * Formate une date en fuseau Paris.
 * @param {string} value - Date ISO.
 * @returns {string} Date lisible.
 */
const formatDate: (value: string) => string = (value: string): string =>
  formatParisDate(value, { dateStyle: 'medium' }) ?? '-'
</script>
