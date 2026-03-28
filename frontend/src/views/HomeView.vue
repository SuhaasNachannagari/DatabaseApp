<script setup>
import { ref, onMounted } from 'vue'
import TextBox from '../components/TextBox.vue'

const message = ref('Loading...')

onMounted(async () => {
  try {
    const response = await fetch('http://127.0.0.1:5000/greetings')
    const data = await response.text()
    message.value = data
  } catch (error) {
    console.error('Error fetching data:', error)
    message.value = 'Error connecting to backend!'
  }
})
</script>

<template>
  <main class="container">
    <TextBox :text="message" />
  </main>
</template>

<style scoped>
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
</style>
