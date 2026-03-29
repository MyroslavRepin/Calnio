<script setup>
import {defineProps, defineEmits, ref, computed, watch, onMounted} from "vue";
import axios from "axios";
import {API_BASE_URL} from "@/config/api.js";

const props = defineProps({ entry: Object })
const emit = defineEmits(['close', 'updated'])

function handleClose() {
  emit('close')
}

const formData = ref({
  title: undefined,
  description: undefined,
  started_at: undefined,
  ended_at: undefined,
})

const isSaving = ref(false)
const saveError = ref(null)

// Convert ISO string to datetime-local format (YYYY-MM-DDThh:mm)
const isoToLocal = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Convert datetime-local format to ISO string
const localToISO = (localString) => {
  if (!localString) return null;
  return new Date(localString).toISOString();
}

// Calculate duration in human-readable format
const duration = computed(() => {
  if (!formData.value.started_at) return 'N/A';
  
  const start = new Date(formData.value.started_at);
  const end = formData.value.ended_at ? new Date(formData.value.ended_at) : new Date();
  
  const diffMs = end - start;
  if (diffMs < 0) return 'Invalid';
  
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);
  
  return `${hours}h ${minutes}m ${seconds}s`;
})

// Initialize form data from entry prop
onMounted(() => {
  if (props.entry) {
    formData.value.title = props.entry.title;
    formData.value.description = props.entry.description;
    formData.value.started_at = isoToLocal(props.entry.started_at);
    formData.value.ended_at = isoToLocal(props.entry.ended_at);
  }
})

const saveChanges = async () => {
  if (isSaving.value) return;
  
  isSaving.value = true;
  saveError.value = null;
  
  try {
    const response = await axios.patch(
      `${API_BASE_URL}/time-entries/${props.entry.id}?session_id=${props.entry.id}`,
      {
        title: formData.value.title,
        description: formData.value.description,
        started_at: localToISO(formData.value.started_at),
        ended_at: localToISO(formData.value.ended_at),
      },
      {
        headers: {
          'Content-Type': 'application/json'
        },
        withCredentials: true,
      }
    );
    
    emit('updated', response.data);
    emit('close');
  } catch (error) {
    console.error("Error saving changes:", error);
    saveError.value = error.response?.data?.detail || "Failed to save changes. Please try again.";
  } finally {
    isSaving.value = false;
  }
}

</script>

<template>
  <div class="modal-body">
    <form @submit.prevent="saveChanges">
      <!--- Title field --->
      <div class="modal-field">
        <label>Title:</label>
        <input
          v-bind:placeholder="entry.title"
          v-model="formData.title"
        />
      </div>

      <!--- Description field --->
      <div class="modal-field description-field">
        <label>Description:</label>
        <textarea
          v-bind:placeholder="entry.description"
          v-model="formData.description"
          rows="4"
        ></textarea>
      </div>
      <!--- Start time field --->
      <div class="modal-field">
        <label>Started at:</label>
        <input 
          type="datetime-local" 
          class="datetime-input"
          v-model="formData.started_at"
        >
      </div>

      <!--- End time field --->
      <div class="modal-field">
        <label>Ended at:</label>
        <input 
          type="datetime-local" 
          class="datetime-input"
          v-model="formData.ended_at"
        >
      </div>

      <!--- Elapsed time field --->
      <div class="modal-field">
        <label>Duration total:</label>
        <span>{{ duration }}</span>
      </div>

      <!--- Error message --->
      <div v-if="saveError" class="error-message">
        {{ saveError }}
      </div>
    </form>
  </div>

  <div class="modal-footer">
    <button type="button" class="btn-primary" @click="saveChanges" :disabled="isSaving">
      {{ isSaving ? 'Saving...' : 'Save' }}
    </button>
  </div>
</template>

<style scoped>
.modal-body {
  padding: 30px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.modal-footer {
  padding: 20px 40px 30px;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}
.modal-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  gap: 15px;
}

.modal-field.description-field {
  align-items: flex-start;
}

.modal-field label {
  font-size: 15px;
  color: #999;
  font-weight: 500;
  min-width: 100px;
}

.modal-field input,
.modal-field textarea {
  flex: 1;
  padding: 10px 12px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.modal-field input:focus,
.modal-field textarea:focus {
  outline: none;
  border-color: #4a90e2;
}

.modal-field textarea {
  resize: vertical;
  min-height: 80px;
  line-height: 1.5;
}

.datetime-input {
  font-family: monospace;
}

.modal-field span {
  font-size: 14px;
  font-weight: bold;
}

.error-message {
  padding: 10px 12px;
  background-color: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn-save {
  padding: 10px 24px;
  background-color: #4a90e2;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-save:hover:not(:disabled) {
  background-color: #357abd;
}

.btn-save:disabled {
  background-color: #ccc;
  cursor: not-allowed;
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

.btn-primary:disabled {
  background: #666;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: #999;
  border: 1px solid #333;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
}

.btn-secondary:hover:not(:disabled) {
  border-color: #fff;
  color: #fff;
}

.btn-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>

