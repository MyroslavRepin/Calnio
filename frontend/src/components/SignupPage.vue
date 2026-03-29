<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { API_BASE_URL } from '@/config/api';

const router = useRouter();

const formData = ref({
  email: '',
  username: '',
  password: '',
});
const isLoading = ref(false);

const tagline = ref("Ready to track your coding progress?")
const isError = ref(false);

const disabled = computed(() => {
  if (isLoading.value) {
    return true;
  }
  return !formData.value.email || !formData.value.username || !formData.value.password;
});

let year = ref( new Date().getFullYear() );

const sendSignupRequest = async () => {
  isError.value = false;
  isLoading.value = true;
  
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/signup`, {
      email: formData.value.email,
      username: formData.value.username,
      password: formData.value.password,
    }, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true,
    });
    
    if (response.data?.ok) {
      return router.push('/dashboard');
    }
  } catch (error) {
    isError.value = true;
    
    if (!error.response) {
      tagline.value = "Network error. Please check your connection.";
      return;
    }
    
    const status = error.response.status;
    const detail = error.response.data?.detail;
    
    if (status === 409) {
      tagline.value = detail || 'User with this email/username already exists.';
    } else if (status === 500) {
      tagline.value = "Server error. Please try again later.";
    } else {
      tagline.value = detail || "An error occurred. Please try again.";
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <main>
    <div class="container">
      <div class="login-container">
        <div class="decorative-plus plus-1">+</div>
        <div class="decorative-plus plus-2">+</div>
        <div class="decorative-plus plus-3">+</div>
        <div class="decorative-plus plus-4">+</div>

        <div class="login-content">
      <div class="logo">reflectly<span class="registered">®</span></div>
      <p class="subtitle">Time Tracker</p>
      <p class="tagline" :class="{ error: isError }">{{tagline}}</p>

      <form @submit.prevent="sendSignupRequest">
        <!--- Email field --->
        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="formData.email"
            type="email"
            autocomplete="username email"
            class="form-input"
            placeholder="you@example.com"
            required
          >
        </div>
        <!--- Username field --->
        <div class="form-group">
          <label class="form-label">Username</label>
          <input
            v-model="formData.username"
            type="text"
            id="username"
            name="username"
            class="form-input"
            placeholder="Enter your new username"
            required
            autocomplete="current-username"
          >
        </div>
        <!--- Password field --->
        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input
            v-model="formData.password"
            type="password"
            id="password"
            name="password"
            class="form-input"
            placeholder="Enter your new password"
            required
            autocomplete="current-password"
          >
        </div>

        <button
          type="submit"
          class="login-button"
          :disabled="disabled"
        >
          {{ isLoading ? 'Creating account...' : 'Start being productive' }}
        </button>
      </form>

      <div class="signup-link">
        Already productive? <a href="/login">Log In</a>
      </div>

      <div class="footer-text">© {{year}} Reflectly Tracker</div>
    </div>
  </div>
    </div>
  </main>
</template>

<style scoped>
main {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-container {
  background: var(--color-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-5xl);
  max-width: var(--card-max-width);
  width: 100%;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.decorative-plus {
  position: absolute;
  color: var(--color-secondary);
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-light);
}

.plus-1 {
  top: 40px;
  left: 40px;
}

.plus-2 {
  top: 40px;
  right: 40px;
}

.plus-3 {
  bottom: 40px;
  left: 40px;
}

.plus-4 {
  bottom: 40px;
  right: 40px;
}

.login-content {
  position: relative;
  z-index: var(--z-base);
}

.logo {
  font-size: var(--font-size-8xl);
  color: var(--color-text-light);
  font-weight: var(--font-weight-bold);
  letter-spacing: -2px;
  margin-bottom: var(--spacing-sm);
}

.registered {
  font-size: var(--font-size-6xl);
}

.subtitle {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-light);
  margin-bottom: var(--spacing-4xl);
  letter-spacing: var(--letter-spacing-medium);
}

.tagline {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-lg);
  margin-bottom: var(--spacing-4xl);
  transition: color var(--transition-base);
}

.tagline.error {
  color: #f5576c;
}

.form-group {
  margin-bottom: var(--spacing-xl);
}

.form-label {
  display: block;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-light);
}

.form-input {
  width: 100%;
  padding: var(--spacing-md) var(--spacing-lg);
  border: 1px solid var(--color-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-lg);
  background: var(--color-secondary);
  color: var(--color-text-light);
  transition: all var(--transition-base);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-white);
  background: #222;
}

.form-input::placeholder {
  color: var(--color-text-secondary);
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: var(--spacing-2xl);
}

.checkbox-group input[type="checkbox"] {
  width: var(--icon-sm);
  height: var(--icon-sm);
  cursor: pointer;
  accent-color: var(--color-white);
}

.checkbox-group label {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-md);
  cursor: pointer;
}

.forgot-password {
  text-align: right;
  margin-bottom: var(--spacing-2xl);
}

.forgot-password a {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-base);
  transition: color var(--transition-base);
}

.forgot-password a:hover {
  color: var(--color-text-light);
}

.login-button {
  width: 100%;
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  background: var(--color-white);
  color: var(--color-text-primary);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
}

.login-button:hover:not(:disabled) {
  background: var(--color-off-white);
  transform: translateY(-1px);
}

.login-button:disabled {
  opacity: var(--opacity-disabled);
  cursor: not-allowed;
}

.signup-link {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-md);
}

.signup-link a {
  color: var(--color-text-light);
  font-weight: var(--font-weight-semibold);
  transition: opacity var(--transition-base);
}

.signup-link a:hover {
  opacity: var(--opacity-active);
}

.footer-text {
  text-align: center;
  margin-top: var(--spacing-4xl);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
