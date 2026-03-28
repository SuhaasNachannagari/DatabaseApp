<script setup>
defineProps({
  text: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <div class="text-box">
    <h1 class="neon-text">{{ text }}</h1>
  </div>
</template>

<style scoped>
.text-box {
  background-color: #333; /* Dark background container */
  padding: 40px; /* Increased padding */
  display: inline-block;
  border-radius: 16px; /* Slightly more rounded */
}

.neon-text {
  font-family: 'Bangers', cursive;
  letter-spacing: 2px;
  font-size: 5rem; /* Even bigger for cartoon impact */
  color: #ccff00; /* Neon Yellow */
  text-shadow:
    0 0 10px #ccff00,
    0 0 20px #ccff00; /* Stronger glow */
  margin: 0;
}
</style>
