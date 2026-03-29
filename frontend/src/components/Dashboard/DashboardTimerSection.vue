<script setup>
import {ref, onMounted, computed, onUnmounted, watch} from "vue";
import axios from "axios";
import { API_BASE_URL } from "@/config/api.js";

let isError = ref(false)
let errorMessage = ref("")
let isTimerRunning = ref(false)

const startedAtTimerSeconds = ref(0)
const dateNow = ref(new Date())
const elapsedSeconds = ref(0)
let intervalId = null

const formData = ref({
  title: '',
  description: '',
});

function startTick() {
  if (intervalId) return

  intervalId = setInterval(() => {
    elapsedSeconds.value += 1
  }, 1000)
}
function stopTick() {
  clearInterval(intervalId)
  intervalId = null
}

const hours = computed(() => Math.floor(elapsedSeconds.value / 3600))
const minutes = computed(() => Math.floor(elapsedSeconds.value / 60) % 60)
const seconds = computed(() => elapsedSeconds.value % 60)

async function initTimerFromApi() {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/time-entries/current-running`,
      { withCredentials: true }
    )

    if (!response.data) {
      isTimerRunning.value = false
      elapsedSeconds.value = 0
      return
    }

    const startedAt = Math.floor(
      new Date(response.data.started_at).getTime() / 1000
    )

    const now = Math.floor(Date.now() / 1000)

    elapsedSeconds.value = now - startedAt
    isTimerRunning.value = true

  } catch (e) {
    console.error('Timer init failed', e)
    isTimerRunning.value = false
    elapsedSeconds.value = 0
  }
}

const startTimerRequest = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/time-entries/start`, {
      title: formData.value.title,
      description: formData.value.description,
    }, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true,
    })
    elapsedSeconds.value = 0
    isTimerRunning.value = true
  }
  catch (error) {
    isError.value = true
    errorMessage.value = error.message
    console.error("Error starting timer:", error);
  }
}
const stopTimerRequest = async () => {
  try {
    const response = await axios.patch(`${API_BASE_URL}/time-entries/stop`, {}, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true,
    })
    isTimerRunning.value = false
    elapsedSeconds.value = 0
  }
  catch (error) {
    isError.value = true
    errorMessage.value = error.message
    console.error("Error stopping timer:", error);
    isTimerRunning.value = false
    elapsedSeconds.value = 0
  }
}
const pauseTimerRequest = async () => {
}

onMounted( () => {
  initTimerFromApi()
})

watch(isTimerRunning, (running) => {
  if (running) startTick()
  else stopTick()
})
const timerDisplay = computed(() => {
  return `${hours.value}h ${minutes.value}m ${seconds.value}s`
})
</script>

<template>
  <div class="tracking-card">
    <div class="card-glow"></div>
    
    <div class="tracking-header">
      <div class="left-side-card">
        <div class="status-badge" :class="{ active: isTimerRunning }">
          <span class="status-dot"></span>
          {{ isTimerRunning ? 'Active' : 'Idle' }}
        </div>
        <div class="session-time">
          <span class="time-digit">{{ hours.toString().padStart(2, '0') }}</span>
          <span class="time-separator">:</span>
          <span class="time-digit">{{ minutes.toString().padStart(2, '0') }}</span>
          <span class="time-separator">:</span>
          <span class="time-digit">{{ seconds.toString().padStart(2, '0') }}</span>
        </div>
        <div class="session-label">{{ isTimerRunning ? 'Time Tracked' : 'Ready to Start' }}</div>
      </div>
      
      <div class="tracking-controls">
        <button class="btn btn-start" v-if="!isTimerRunning" @click="startTimerRequest">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          Start
        </button>
<!--        <button class="btn btn-pause" v-if="isTimerRunning" @click="pauseTimerRequest">-->
<!--          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">-->
<!--            <rect x="6" y="4" width="4" height="16"></rect>-->
<!--            <rect x="14" y="4" width="4" height="16"></rect>-->
<!--          </svg>-->
<!--          Pause-->
<!--        </button>-->
        <button class="btn btn-stop" v-if="isTimerRunning" @click="stopTimerRequest">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <rect x="5" y="5" width="14" height="14"></rect>
          </svg>
          Stop
        </button>
      </div>
    </div>
    <div class="bottom-section" v-if="!isTimerRunning">
      <form class="timer-form">
        <div class="form-field">
          <input 
            id="titleFrom" 
            type="text" 
            placeholder="What are you working on?" 
            class="form-input title-input" 
            v-model="formData.title"
          />
        </div>
        <div class="form-field">
          <textarea 
            id="descriptionForm" 
            placeholder="Add description (optional)" 
            class="form-input description-input" 
            v-model="formData.description"
          ></textarea>
        </div>
      </form>
    </div>
    
    <div class="running-task" v-if="isTimerRunning && formData.title">
      <div class="task-info">
        <div class="task-title">{{ formData.title }}</div>
        <div class="task-description" v-if="formData.description">{{ formData.description }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tracking-card {
  position: relative;
  background: linear-gradient(145deg, #0d0d0d 0%, #1a1a1a 100%);
  border-radius: 24px;
  padding: 48px;
  color: #fff;
  width: 100%;
  max-width: 100%;
  min-height: 200px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.tracking-card:hover {
  border-color: rgba(255, 255, 255, 0.1);
}

.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

.tracking-card:hover .card-glow {
  opacity: 1;
}

.tracking-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.left-side-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #999;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.status-badge.active {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.2);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #666;
  transition: all 0.3s ease;
}

.status-badge.active .status-dot {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.session-time {
  font-size: 64px;
  font-weight: 700;
  letter-spacing: -3px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-variant-numeric: tabular-nums;
  background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.time-digit {
  min-width: 80px;
  text-align: center;
}

.time-separator {
  opacity: 0.5;
  animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.1; }
}

.session-label {
  font-size: 15px;
  color: #999;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.tracking-controls {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-icon {
  width: 18px;
  height: 18px;
  stroke-width: 2.5;
}

.btn-start {
  background: linear-gradient(135deg, #ffffff 0%, #e5e5e5 100%);
  color: #000000;
}

.btn-start:hover {
  //transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 255, 255, 0.3);
}

.btn-start:active {
  //transform: translateY(0);
}

.btn-pause {
  background: rgba(255, 255, 255, 0.05);
  color: #FFFFFF;
  border: 1.5px solid rgba(255, 255, 255, 0.1);
}

.btn-pause:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  //transform: translateY(-2px);
}

.btn-stop {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: #FFFFFF;
}

.btn-stop:hover {
  background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%);
  //transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
}

.bottom-section {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.timer-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  width: 100%;
}

.form-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  color: #FFFFFF;
  font-size: 15px;
  padding: 14px 18px;
  transition: all 0.3s ease;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-input::placeholder {
  color: #666;
}

.title-input {
  font-weight: 500;
}

.description-input {
  min-height: 100px;
  max-height: 200px;
  resize: vertical;
  font-size: 14px;
  line-height: 1.6;
}

.running-task {
  margin-top: 32px;
  padding: 20px 24px;
  background: rgba(99, 102, 241, 0.05);
  //border-left: 3px solid #6366f1;
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.task-description {
  font-size: 14px;
  color: #999;
  line-height: 1.6;
}
</style>