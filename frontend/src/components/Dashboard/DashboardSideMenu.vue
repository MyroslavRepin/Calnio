<script setup>
import homeIcon from '@/assets/icons/home-icon.svg'
import profileIcon from '@/assets/icons/profile-icon.svg'
import settingsIcon from '@/assets/icons/settings-icon.svg'

</script>
<template>
  <div class="sidebar-menu">
    <div class="top-navigation">
      <RouterLink to="/dashboard">
        <div class="link-square">
          <img :src="homeIcon" alt="Home icon"/>
        </div>
      </RouterLink>
    </div>
    <div class="bottom-navigation">
<!--      <RouterLink to="/profile">-->
<!--        <div class="link-square">-->
<!--          <img :src="profileIcon" alt="Profile icon"/>-->
<!--        </div>-->
<!--      </RouterLink>-->
      <RouterLink to="/settings">
        <div class="link-square">
          <img :src="settingsIcon" alt="Settings icon"/>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.sidebar-menu {
  position: fixed;
  top: 15px;
  left: 15px;
  bottom: 15px;
  width: 60px;
  background-color: #0a0a0a;
  color: #000000;
  display: flex;
  padding: 10px 0;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  border-radius: 12px;
}

.top-navigation {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.link-square {
  box-sizing: border-box;
  width: 40px;
  height: 40px;
  background-color: #efefef;
  border-radius: 7px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.link-square img {
  width: 25px;
  height: 25px;
}
.bottom-navigation {
  display: flex;
  gap: 10px;
  flex-direction: column;
  align-items: center;
}
</style>