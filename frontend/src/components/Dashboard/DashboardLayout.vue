<script setup>
import DashboardTimerSection from "./DashboardTimerSection.vue";
import SideMenuDashboard from "./DashboardSideMenu.vue";
import DashboardUserGreeting from "./DashboardUserGreeting.vue";
import DashboardEntries from "./DashboardEntries.vue";
import DashboardStats from "@/components/Dashboard/DashboardStats.vue";

import axios from "axios";
import { API_BASE_URL } from "@/config/api.js";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const isVerified = ref(false);

const isUserVerified = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/auth/verify`, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true,
    });
    
    if (response.data?.ok) {
      isVerified.value = true;
      return true;
    }
    return false;
  } catch (error) {
    console.error("Error verifying user:", error);
    isVerified.value = false;
    return false;
  }
};

onMounted(async () => {
  const verified = await isUserVerified();
  if (!verified) {
    router.push('/login');
  }
});
</script>

<template>
  <div v-if="isVerified" class="settings-page">
    <div class="container">
      <div class="settings-wrapper">
        <aside class="sidebar">
          <SideMenuDashboard />
        </aside>
        <main class="main-content">
<!--          <DashboardUserGreeting />-->
          <DashboardTimerSection />
          <DashboardStats />
          <DashboardEntries />
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: var(--color-off-white);
  padding: 0;
  overflow-x: hidden;
}

.container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 !important;
  width: 100%;
  min-height: 100vh;
}

.settings-wrapper {
  display: flex;
  flex-direction: row;
  gap: 24px;
  width: 100%;
  min-height: 100vh;
  padding: 15px;
  //padding-left: 102px;
  box-sizing: border-box;
}

.sidebar {
  flex-shrink: 0;
  width: 72px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: calc(100% - 96px);
  overflow-x: hidden;
}
</style>