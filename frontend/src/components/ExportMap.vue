<template>
  <div class="box export-map-container">
    <button class="button is-primary is-fullwidth" @click="openModal">
      <span class="icon">
        <i class="fas fa-download"></i>
      </span>
      <span>Export Map</span>
    </button>
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
  align-items: center;
  justify-content: center;
}
</style>
