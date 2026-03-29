<script setup>
import SideMenuDashboard from "../Dashboard/DashboardSideMenu.vue";
import SettingsProfile from "@/components/Settings/SettingsProfile.vue";
import SettingsSecurity from "@/components/Settings/SettingsSecurity.vue";

import axios from "axios";
import { API_BASE_URL } from "@/config/api.js";
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import Notification from "@/components/Notification.vue";

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

const activeSettingTab = ref('general')

const settingsMap = {
  general: SettingsProfile,
  security: SettingsSecurity,
}

const activeComponent = computed(() => {
  return settingsMap[activeSettingTab.value]
})

onMounted(async () => {
  const verified = await isUserVerified();
  if (!verified) {
    await router.push('/login');
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
        <!--- This section is for settings topics--->
        <SettingsProfile />
      </div>
    </div>
  </div>
</template>
<style scoped>
* {
  color: #000000;
  margin: 0;
  padding: 0;
}
h1{
  margin: 0;
  color: #000000;
}
h*, p* {
  margin: 0;
}
.settings-page {
  min-height: 100vh;
  background: var(--color-off-white);
  padding: 0;
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
</style>