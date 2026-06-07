<script lang="ts" setup>
/**
 * Redirige /home vers la liste des comptes (page d'accueil apres connexion).
 */
definePageMeta({ layout: 'home' })

await navigateTo('/home/accounts', { replace: true })
</script>
