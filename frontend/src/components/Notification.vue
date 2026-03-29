<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: value => ['success', 'error', 'info'].includes(value)
  },
  message: {
    type: String,
    required: true,
    message: String
  }
})

</script>
<template>
  <aside role="alert" :class="props.type">
    <p>
      {{ props.message }}
    </p>
  </aside>
</template>

<style scoped>
* {
  box-sizing: border-box;
}
aside {
  width: 100%;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  color: #ffffff;
  font-weight: bold;
}
aside.success {
  background-color: #57cc99;
}
aside.error {
  background-color: #ef476f;
}
aside.info {
  background-color: #4895ef;
}
aside[role="alert"]:has(+ *) {
  margin-bottom: var(--spacing-md);
}
</style>