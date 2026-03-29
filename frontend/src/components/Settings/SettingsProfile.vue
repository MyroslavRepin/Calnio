<script setup>
import axios from "axios";
import { API_BASE_URL } from "@/config/api.js";
import {computed, onMounted, ref} from "vue";
import Notification from "@/components/Notification.vue";

const email = ref('');
const username = ref('');
const formData = ref({
  email: undefined,
  username: undefined,
  password: undefined,
})
const loading = ref(false);
const hasError = ref(false);
const success = ref(false);
const message = ref('');

async function fetchUserData() {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/me`, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true,
    });
    email.value = response.data["email"]
    username.value = response.data["username"]
  } catch (error) {
      console.error("Error fetching user data:", error);
  }
}

async function saveChanges() {
  loading.value = true;
  success.value = false;
  hasError.value = false;
  
  try {
    const response = await axios.patch(`${API_BASE_URL}/users/me`, formData.value, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true,
    });
    
    if (response.status === 200) {
      success.value = true;
      message.value = "Changes saved successfully";
      setTimeout(() => {
        success.value = false;
      }, 3000);
    }
  } catch (err) {
    hasError.value = true;
    
    if (err.response) {
      const status = err.response.status;
      
      if (status === 401) {
        message.value = "Unauthorized. Please log in again.";
      } else if (status === 422) {
        message.value = "Validation error. Please check your input and try again.";
      } else if (status === 500) {
        message.value = "Server error. Please try again later.";
      } else {
        message.value = `An error occurred (${status})`;
      }
    } else if (err.request) {
      message.value = "Server error. No response received.";
    } else {
      message.value = "Network error. Please check your connection.";
    }
    
    setTimeout(() => {
      hasError.value = false;
    }, 3000);
  } finally {
    loading.value = false;
  }
}

const isFormEmpty = computed(() => {
  const isEmpty = !formData.value.email && !formData.value.username && !formData.value.password;
  return isEmpty;
})

onMounted( async () => {
  await fetchUserData();
})

</script>

<template>
  <main class="main-content">
    <Notification v-if="success" :message="message" type="success" />
    <Notification v-if="hasError" :message="message" type="error" />
    <h1>Settings</h1>
    <section>
      <section class="section-type">
        <div class="headings">
          <h2>Account</h2>
          <p>Manage your account settings and preferences.</p>
        </div>
        <div class="form-section">
          <form @submit.prevent="saveChanges()">
            <div class="form-group">
              <h4>Change your email</h4>
              <input type="email" v-bind:placeholder="email" v-model="formData.email">
            </div>
            <div class="form-group">
              <h4>Change your username</h4>
              <input type="text" v-bind:placeholder="username" v-model="formData.username">
            </div>
            <div class="form-group">
              <h4>Change your password</h4>
              <input type="password" placeholder="Your new password" v-model="formData.password">
            </div>
            <button
                type="submit"
                class="btn-submit-changes"
                :disabled="isFormEmpty || loading">{{ loading ? 'Saving Changes...' : 'Save Changes' }}
            </button>
          </form>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
h1, h2, h3, * {
  margin: 0;
  padding: 0;
  color: #000000;
}
h4 {
  margin-bottom: 8px;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: calc(100% - 96px);
  background-color: var(--color-white);
  padding: var(--spacing-lg);
  border-radius: 15px;
}
.section-type {
  background: var(--color-off-white);
  border: 1px solid #cdcdcd;
  border-radius: 15px;
  padding: var(--spacing-md);
  position: relative;
}
.headings {
  margin-bottom: var(--spacing-lg);
}
.form-section {
  margin-top: var(--spacing-md);
}
.form-group {
  margin-bottom: var(--spacing-md);
}
input {
  width: 100%;
  max-width: 100%;
  padding: var(--spacing-sm);
  border: 1px solid #cdcdcd;
  border-radius: 8px;
  box-sizing: border-box;
  background-color: #FFFFFF;
}
form {
  position: relative;
  width: 100%;
  max-width: 100%;
}
.btn-submit-changes {
  width: 100%;
  height: 48px;
  transition: opacity 0.25s;
  margin-top: var(--spacing-md);
  color: #ffffff;
}
.btn-submit-changes:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
.btn-submit-changes:hover:not(:disabled) {
  opacity: var(--opacity-hover);
  transition: opacity 0.25s;
}
</style>
