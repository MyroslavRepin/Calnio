import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'

import './assets/css/variables.css';
import LandingPage from './components/LandingPage.vue'
import LoginPage from './components/LoginPage.vue';
import SignupPage from './components/SignupPage.vue';
import DashboardLayout from './components/Dashboard/DashboardLayout.vue';
import EntryModal from "./components/EntryModal/EntryModal.vue";
import SettingsLayout from "@/components/Settings/SettingsLayout.vue";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            name: 'Landing',
            path: '/',
            component: LandingPage
        },
        {
            name: 'Login',
            path: '/login',
            component: LoginPage
        },
        {
            name: 'Signup',
            path: '/signup',
            component: SignupPage
        },
        {
            name: 'Dashboard',
            path: '/dashboard',
            component: DashboardLayout,
        },
        {
            name: 'EntryModal',
            path: '/entries/:entry_id',
            component: EntryModal,
        },
        {
            name: 'Settings',
            path: '/settings',
            component: SettingsLayout,
        },
    ]
});

const app = createApp(App)
app.use(router)
app.mount('#app')
