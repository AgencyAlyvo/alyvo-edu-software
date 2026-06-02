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
        <!-- Sections principales (LinkedIn puis Business Locaux). -->
        <div class="grid w-full gap-5">
          <div v-for="section in sections" :key="section.title" class="grid w-full gap-1">
            <h3 class="px-3 pb-1 text-[10px] font-bold tracking-wider text-[#6b7591] uppercase">
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

        <!-- Liens de bas de sidebar. -->
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
 * Lien de navigation avec son icone Nuxt UI.
 */
type NavLink = {
  name: string
  icon: string
  to: string
}

/**
 * Groupe de liens (section dans la sidebar) avec un en-tete.
 */
type NavSection = {
  title: string
  links: NavLink[]
}

// Deux sections distinctes : LinkedIn (existant) puis Business Locaux (nouveau module OSM).
const sections: NavSection[] = [
  {
    title: 'LinkedIn',
    links: [
      { name: 'Tableau de bord LinkedIn', icon: 'i-heroicons-squares-2x2', to: '/home' },
      { name: 'Objectif LinkedIn semaine', icon: 'i-heroicons-calendar', to: '/home/linkedin/weekly' },
      { name: 'Tous les prospects LinkedIn', icon: 'i-heroicons-users', to: '/home/linkedin/all' },
      { name: 'Rendez-vous appels LinkedIn', icon: 'i-heroicons-phone', to: '/home/linkedin/calls' },
      { name: 'Relances LinkedIn', icon: 'i-heroicons-bell', to: '/home/tasks' },
      { name: 'Parametres LinkedIn', icon: 'i-heroicons-cog-6-tooth', to: '/home/settings' },
    ],
  },
  {
    title: 'Business Locaux',
    links: [
      {
        name: 'Tableau de bord Business',
        icon: 'i-heroicons-squares-2x2',
        to: '/home/local-business',
      },
      {
        name: 'Tous les business locaux',
        icon: 'i-heroicons-building-storefront',
        to: '/home/local-business/all',
      },
      {
        name: 'Rendez-vous appels Business',
        icon: 'i-heroicons-phone',
        to: '/home/local-business/calls',
      },
      {
        name: 'Import depuis OSM',
        icon: 'i-heroicons-map-pin',
        to: '/home/local-business/import',
      },
      {
        name: 'Relances Business Locaux',
        icon: 'i-heroicons-bell',
        to: '/home/local-business/tasks',
      },
    ],
  },
]

// Aucun lien de bas pour l'instant.
const bottomLinks: NavLink[] = []

/**
 * Verifie si la route courante correspond exactement au lien.
 * @param {string} to - Chemin de la route a comparer avec la route active.
 * @returns {boolean} Vrai si la route courante correspond au chemin donne.
 */
const isActive: (to: string) => boolean = (to: string): boolean => {
  const path: string = useRoute().path

  if (to === '/home' || to === '/home/local-business') {
    return path === to
  }

  return path.startsWith(to)
}
</script>
