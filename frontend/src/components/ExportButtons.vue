<template>
  <div class="box export-map-container">
    <button class="button is-primary is-fullwidth" @click="openModal">
      <span class="icon">
        <i class="fas fa-download"></i>
      </span>
      <span>Export Map</span>
    </button>
    <a
      href="https://arcg.is/1ziaPD1"
      target="_blank"
      rel="noopener noreferrer"
      class="button is-info is-fullwidth mt-2"
    >
      <span class="icon">
        <i class="fas fa-external-link-alt"></i>
      </span>
      <span>About</span>
    </a>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  openModal: []
}>()

const openModal = () => {
  emit('openModal')
}
</script>

<style scoped>
.export-map-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
}
</style>
