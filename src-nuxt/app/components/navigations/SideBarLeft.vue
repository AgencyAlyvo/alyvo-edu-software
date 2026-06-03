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
        <!-- Sections principales de navigation (shell Edu — liens a ajouter plus tard). -->
        <div v-for="section in sections" :key="section.title" class="grid w-full gap-5">
          <div class="grid w-full gap-1">
            <h3 class="px-3 pb-1 text-[10px] font-bold tracking-wider text-[#6b7591] uppercase">
              {{ section.title }}
            </h3>
            <RouterLink
              v-for="link in section.links"
              :key="link.name"
              :to="link.to"
              class="flex h-[40px] items-center gap-x-3 rounded-md px-3 text-sm text-[#9ba3bd] transition-colors duration-150 hover:bg-[rgba(154,101,213,0.12)] hover:text-white"
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
            class="flex h-[44px] items-center gap-x-3 rounded-md px-3 text-sm text-[#9ba3bd] transition-colors duration-150 hover:bg-[rgba(154,101,213,0.12)] hover:text-white"
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

// Sections de navigation — a definir lors de l'ajout des modules Edu.
const sections: NavSection[] = []

// Liens de bas de sidebar — aucun pour l'instant.
const bottomLinks: NavLink[] = []
</script>
