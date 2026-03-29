<script setup>
import {defineProps, defineEmits, computed} from "vue";

const props = defineProps({ entry: Object })
const emit = defineEmits(['close'])

function handleClose() {
  emit('close')
}

// Format date to readable string
const formatDate = (isoString) => {
  if (!isoString) return 'N/A';
  return new Date(isoString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Calculate duration between started_at and ended_at
const duration = computed(() => {
  if (!props.entry?.started_at) return 'N/A';
  
  const start = new Date(props.entry.started_at);
  const end = props.entry.ended_at ? new Date(props.entry.ended_at) : new Date();
  
  const diffMs = end - start;
  if (diffMs < 0) return 'Invalid';
  
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);
  
  return `${hours}h ${minutes}m ${seconds}s`;
})

</script>

<template>
  <div class="modal-body">
    <div class="modal-field">
      <label>Title:</label>
      <span class="field-value">{{ entry?.title || 'No title' }}</span>
    </div>

    <div class="modal-field description-field">
      <label>Description:</label>
      <span class="field-value description-text">{{ entry?.description || 'No description' }}</span>
    </div>

    <div class="modal-field">
      <label>Started:</label>
      <span class="field-value">{{ formatDate(entry?.started_at) }}</span>
    </div>
    
    <div class="modal-field">
      <label>Ended:</label>
      <span class="field-value">{{ entry?.ended_at ? formatDate(entry.ended_at) : 'Still running' }}</span>
    </div>
    
    <div class="modal-field">
      <label>Duration:</label>
      <span class="field-value">{{ duration }}</span>
    </div>
  </div>

  <div class="modal-footer">
    <button class="btn-primary" @click="handleClose">Close</button>
  </div>
</template>

<style scoped>
.modal-body {
  padding: 30px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-field {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
}

.modal-field.description-field {
  flex-direction: column;
  align-items: flex-start;
}

.modal-field label {
  font-size: 15px;
  color: #999;
  font-weight: 500;
  min-width: 100px;
}

.field-value {
  font-size: 14px;
  font-weight: 400;
  margin-left: auto;
}

.description-text {
  margin-left: 0;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  width: 100%;
}

.modal-footer {
  padding: 20px 40px 30px;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}

.btn-primary {
  background: #ffffff;
  color: #000000;
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
}

.btn-primary:hover {
  box-shadow: #9e9e9d 0px 0px 7px;
}
</style>