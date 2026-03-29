<script setup>
import {defineProps, defineEmits, ref, onMounted} from 'vue'
import axios from "axios";
import {API_BASE_URL} from "@/config/api.js";
import EntryModalPreview from "@/components/EntryModal/EntryModalPreview.vue";
import EntryModalEdit from "@/components/EntryModal/EntryModalEdit.vue";

const props = defineProps({ 
  entry: Object,
  entryId: Number
})
const emit = defineEmits(['close', 'updated'])

const isEditing = ref(false)
const entryData = ref(null)
const isLoading = ref(false)
const loadError = ref(null)

// Load entry data from API
const loadEntry = async () => {
  if (props.entry) {
    entryData.value = props.entry
    return
  }
  
  if (!props.entryId) {
    loadError.value = 'No entry ID provided'
    return
  }
  
  isLoading.value = true
  loadError.value = null
  
  try {
    const response = await axios.get(`${API_BASE_URL}/time-entries/${props.entryId}`, {
      withCredentials: true,
    })
    entryData.value = response.data
  } catch (err) {
    console.error('Error loading entry:', err)
    loadError.value = err.response?.data?.detail || 'Failed to load entry'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadEntry()
})

function closeModal() {
  emit('close')
}
</script>
<template>
  <div class="modal-backdrop" @click="closeModal">
    <div class="modal" @click.stop>
      <div class="modal-header">
        <h3 v-if="!isEditing">Entry Details</h3>
        <h3 v-if="isEditing">Edit Entry Details</h3>
        <div class="modal-actions">
          <button class="edit-btn" @click="isEditing=true" v-if="!isEditing">Edit</button>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
      </div>

      <EntryModalPreview v-if="!isEditing" :entry="entryData" @close="closeModal" />
      <EntryModalEdit v-if="isEditing" :entry="entryData" @close="closeModal" />
    </div>
  </div>
</template>
<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: #111111;
  border-radius: 24px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  color: #fff;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30px 40px 20px;
  border-bottom: 1px solid #222;
}

.modal-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}
.modal-actions {
  display: flex;
  gap: 16px;
}
.edit-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  padding: 0;
}
.edit-btn:focus {
  outline: none;
}
.close-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 32px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  line-height: 32px;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #fff;
}
</style>