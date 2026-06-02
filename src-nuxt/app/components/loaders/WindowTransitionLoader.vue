<template>
  <span class="transition-loader" aria-label="Loading"></span>
</template>

<style scoped>
.transition-loader {
  width: 42px;
  height: 42px;
  border: 3px solid rgb(255 255 255 / 18%);
  border-top-color: #2fb7ff;
  border-radius: 9999px;
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
