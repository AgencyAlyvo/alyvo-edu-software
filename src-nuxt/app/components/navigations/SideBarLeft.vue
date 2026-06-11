<template>
  <div
    id="sidebar-left"
    class="fixed z-10 flex w-[260px] flex-col items-center justify-start overflow-y-auto p-4 text-white"
    style="
      height: calc(100vh - 36px);
      background: linear-gradient(180deg, #0b1433 0%, #050917 100%);
      border-right: 1px solid #2f3d67;
    "
  >
    <nav class="flex h-full w-full flex-col">
      <div class="flex h-full w-full flex-col items-center justify-between gap-6">
        <div class="grid w-full gap-5">
          <div v-for="section in sections" :key="section.title" class="grid w-full gap-1">
            <h3 v-if="section.title" class="px-3 pb-1 text-[10px] font-bold tracking-wider text-[#6b7591] uppercase">
              {{ section.title }}
            </h3>
            <RouterLink
              v-for="link in section.links"
              :key="link.name"
              :to="link.to"
              class="flex h-[40px] items-center gap-x-3 rounded-md px-3 text-sm transition-colors duration-150"
              :class="
                isActive(link.to)
                  ? 'bg-[#9a65d5] text-white'
                  : 'text-[#9ba3bd] hover:bg-[rgba(154,101,213,0.12)] hover:text-white'
              "
            >
              <UIcon :name="link.icon" class="h-[18px] w-[18px] shrink-0" />
              <span class="truncate font-medium">{{ link.name }}</span>
            </RouterLink>
          </div>
        </div>

        <div class="grid w-full gap-2">
          <RouterLink
            v-for="link in bottomLinks"
            :key="link.name"
            :to="link.to"
            class="flex h-[44px] items-center gap-x-3 rounded-md px-3 text-sm transition-colors duration-150"
            :class="
              isActive(link.to)
                ? 'bg-[#9a65d5] text-white'
                : 'text-[#9ba3bd] hover:bg-[rgba(154,101,213,0.12)] hover:text-white'
            "
          >
            <UIcon :name="link.icon" class="h-[18px] w-[18px] shrink-0" />
            <span class="truncate font-medium">{{ link.name }}</span>
          </RouterLink>
        </div>
      </div>
    </nav>
  </div>
</template>

<script lang="ts" setup>
/**
 *
 */
type NavLink = {
  name: string
  icon: string
  to: string
}

/**
 *
 */
type NavSection = {
  title?: string
  links: NavLink[]
}

const sections: NavSection[] = [
  {
    links: [
      { name: 'Liste des comptes', icon: 'i-heroicons-users', to: '/home/accounts' },
      {
        name: 'Créer des comptes Outlook',
        icon: 'i-heroicons-envelope',
        to: '/home/accounts/create-outlook',
      },
      {
        name: 'Inscription Broward',
        icon: 'i-heroicons-academic-cap',
        to: '/home/accounts/create-broward',
      },
      {
        name: 'Activation email Broward',
        icon: 'i-heroicons-identification',
        to: '/home/accounts/activate-broward',
      },
      {
        name: 'Support SheerID',
        icon: 'i-heroicons-clipboard-document-list',
        to: '/home/sheerid-support',
      },
    ],
  },
]

const bottomLinks: NavLink[] = [{ name: 'Paramètres', icon: 'i-heroicons-cog-6-tooth', to: '/home/settings' }]

/**
 * Verifie si la route courante correspond au lien.
 * @param {string} to - Chemin de navigation du lien.
 * @returns {boolean} True si le lien doit apparaitre actif.
 */
const isActive: (to: string) => boolean = (to: string): boolean => {
  const path: string = useRoute().path

  if (to === '/home/accounts') {
    return path === '/home/accounts'
  }

  if (to === '/home/accounts/create-outlook') {
    return path === '/home/accounts/create-outlook'
  }

  if (to === '/home/accounts/create-broward') {
    return path === '/home/accounts/create-broward'
  }

  if (to === '/home/accounts/activate-broward') {
    return path === '/home/accounts/activate-broward'
  }

  if (to === '/home/sheerid-support') {
    return path === '/home/sheerid-support'
  }

  return path.startsWith(to)
}
</script>
