<script setup>
const userName = "Hoo Lee Sheet";
</script>

<template>
<div class="user-greeting">
  <h1>Hello, {{userName}}</h1>
</div>
</template>

<style scoped>
.user-greeting {
  border: 1px solid #4d4d4d;
  margin-top: 15px;
  background: rgba(10, 10, 10, 0.22);
  border-radius: 24px;
  margin-bottom: 30px;
  color: #000000;
  max-width: 700px;
  width: 100%;
  height: 200px;
}
</style>