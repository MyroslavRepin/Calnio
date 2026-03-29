<script setup>
import {computed, onMounted, ref} from 'vue'
import axios from "axios";
import { API_BASE_URL } from '@/config/api.js'
import EntryModal from '../EntryModal/EntryModal.vue'

const entries = ref([])
const now = ref(new Date())
const selectedEntry = ref(null)
const isModalOpen = ref(false)

async function fetchAllEntries() {
  try {
    const response = await axios.get(`${API_BASE_URL}/time-entries`, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true,
    })
    console.log(response)
    entries.value = Array.isArray(response.data) ? response.data : []
  }
  catch (error) {
    console.error("Error fetching entries:", error);
    entries.value = []
  }
}
function calculateElapsedTime(startedAt, endedAt) {
  if (!endedAt) {
    return null;
  }
  const start = new Date(startedAt);
  const end = endedAt ? new Date(endedAt) : new Date();
  const elapsedMilliseconds = end - start;

  const totalSeconds = Math.floor(elapsedMilliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const data = { hours, minutes, seconds }
  return data
}

const entriesWithElapsedTime = computed(() => {
  return entries.value.map(entry => ({
    ...entry,
    elapsed: calculateElapsedTime(
      entry.started_at,
      entry.ended_at,
      now.value
    )
  }))
})

const totalEntries = computed(() => entries.value.length)

function openModal(entry) {
  selectedEntry.value = entry
  isModalOpen.value = true
}

function closeModal() {
  selectedEntry.value = null
  isModalOpen.value = false
}

onMounted(() => {
  fetchAllEntries()
  setInterval(() => {
    fetchAllEntries()
  }, 60000);
})
</script>
<template>
  <section class="entries-section">
    <header>
      <h2>Your sessions</h2>
      <p>Total {{ totalEntries }}</p>
    </header>
    <div class="entries-list">
      <p v-if="!entries">No existing entries are found</p>
      <div v-for="entry in entriesWithElapsedTime" :key="entry.id">
        <div v-if="entry.elapsed" class="entry" @click="openModal(entry)">
          <p>{{ entry["id"] }}</p>
          <p>{{ entry.elapsed.hours }}h {{ entry.elapsed.minutes }}m {{ entry.elapsed.seconds }}s</p>
        </div>
      </div>
    </div>

    <EntryModal 
      v-if="isModalOpen && selectedEntry" 
      :entry="selectedEntry" 
      @close="closeModal"
    />
  </section>
</template>
<style scoped>
.entries-section {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
header p{
  color: var(--color-text-secondary);
}
h2 {
  color: var(--color-text-primary);
}

.entries-list {
  display: flex;
  flex-direction: column;
  gap: 1em;
  width: 100%;
}

.entry {
  display: flex;
  justify-content: space-between;
  background-color: var(--color-secondary);
  padding: 15px;
  border-radius: 15px;
  color: #FFFFFF;
}

.entry:hover {
  //box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.7);
  cursor: pointer;
  transition: 0.25s ease-in;
}
</style>