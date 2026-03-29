<script setup>
import {computed, ref} from 'vue';

const heroFeatures = ref([
  'Session Time Tracking',
  'Project Analytics',
  'Productivity Insights',
  'Code Metrics Dashboard'
]);

const sessionTime = ref('2h 34m');
const projectName = ref('React Dashboard');
let year = ref( new Date().getFullYear() );

const clients = ref([
  'Hoo Lee Sheet',
  'Me (developer)',
]);

const clientCount = computed(() => {
  return clients.value.length;
})

const features = ref([
  {
    title: 'Simple Time Tracking',
    year: year.value,
    description: 'Start tracking your work with a single action. Track focused coding sessions and clearly see how much time you invest in your project.'
  },
  {
    title: 'Progress Insights',
    year: year.value,
    description: 'Understand how your project is moving forward through clear analytics and visual graphs that show your activity over time.'
  },
  {
    title: 'Project Overview',
    year: year.value,
    description: 'Get a high-level view of your project progress. See patterns, consistency, and growth to make better decisions and stay on track.'
  }
]);


const toggleMenu = () => {
  console.log('Menu toggled');
};

const startTracking = () => {
  console.log('Start tracking clicked');
};
</script>

<template>
  <div class="landing-page">
    <div class="container">
        <div class="header-background">
          <header>
            <nav>
              <div class="logo">reflectly®</div>
              <div class="nav-links">
                <RouterLink to="/login">Login</RouterLink>
                <RouterLink to="/signup">Sign Up</RouterLink>
                <a href="mailto:myroslavrepin@gmail.com">Contact Developer</a>
              </div>
              <div class="hamburger" @click="toggleMenu">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </nav>
          </header>
        </div>
      <main>
        <section class="hero">
          <div class="decorative-plus plus-1">+</div>
          <div class="decorative-plus plus-2">+</div>
          <div class="decorative-plus plus-3">+</div>
          <div class="decorative-plus plus-4">+</div>

          <div class="hero-content">
            <div class="hero-text">
              <h1>reflectly<span class="registered">®</span></h1>
              <p class="hero-subtitle">Tracker</p>
              <ul class="features-list">
                <li v-for="feature in heroFeatures" :key="feature">{{ feature }}</li>
              </ul>
              <div class="tagline">
                <strong>No guesswork. No forgotten hours.</strong> Just accurate tracking that helps you understand your coding patterns and optimize your workflow.
              </div>
            </div>

            <div class="hero-card">
              <div class="session-info">
                <div class="session-label">Current Session</div>
                <div class="session-value">{{ sessionTime }}</div>
              </div>
              <div class="session-name">{{ projectName }}</div>
              <a href="/login" class="cta-button">Start Tracking</a>
              <div class="rating">
                <div v-for="star in 5" :key="star" class="star"></div>
              </div>
            </div>
          </div>

          <div class="footer-text">© {{ year }} Reflectly Tracker</div>
        </section>

        <section class="clients">
          <div class="clients-header">
            <div class="clients-title">
              <span style="width: 8px; height: 8px; background: #000; border-radius: 50%; display: inline-block;"></span>
              Trusted by peoples
            </div>
            <div class="clients-count">({{ clientCount }}+ peoples)</div>
          </div>
          <div class="clients-grid">
            <div v-for="client in clients" :key="client" class="client-card">{{ client }}</div>
          </div>
        </section>

        <section class="projects">
          <div class="projects-number">(03)</div>
          <div class="projects-header">
            <div>
              <h2 class="projects-title">Features.</h2>
              <p class="projects-year">©{{ year }}</p>
            </div>
            <div class="projects-description">
              I built powerful features to help developers track their time accurately. Here are some of the key capabilities.
            </div>
          </div>

          <div class="features-grid">
            <div v-for="feature in features" :key="feature.title" class="feature-card">
              <h3 class="feature-title">{{ feature.title }}</h3>
              <p class="feature-label">{{ feature.year }}</p>
              <p class="feature-description">{{ feature.description }}</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped>
.landing-page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #e8e8e8;
  color: #000;
  min-height: 100vh;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
.header-background {
  position: sticky;
  top: 0;
  z-index: 100;
}
header {
  background: #fff;
  padding: 20px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  border-radius: 16px;
  margin-left: 20px;
  margin-right: 20px;
}

nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
}

.logo {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.nav-links {
  display: flex;
  gap: 40px;
  align-items: center;
}

.nav-links a {
  text-decoration: none;
  color: #000;
  font-size: 15px;
  font-weight: 400;
  transition: opacity 0.3s;
}

.nav-links a:hover {
  opacity: 0.6;
}

.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  cursor: pointer;
}

.hamburger span {
  width: 25px;
  height: 2px;
  background: #000;
}

.hero {
  background: #0a0a0a;
  border-radius: 24px;
  margin: 20px;
  padding: 80px 60px;
  min-height: 600px;
  position: relative;
  overflow: hidden;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 60px;
}

.hero-text {
  flex: 1;
  max-width: 600px;
}

.hero-text h1 {
  font-size: clamp(48px, 8vw, 96px);
  font-weight: 700;
  color: #fff;
  line-height: 1;
  letter-spacing: -3px;
  margin-bottom: 20px;
}

.hero-text .registered {
  font-size: clamp(32px, 5vw, 64px);
}

.hero-subtitle {
  font-size: clamp(20px, 3vw, 32px);
  font-weight: 500;
  color: #fff;
  margin-bottom: 40px;
  letter-spacing: -1px;
}

.features-list {
  list-style: none;
  margin-bottom: 60px;
}

.features-list li {
  color: #fff;
  font-size: 16px;
  margin-bottom: 12px;
  padding-left: 0;
}

.tagline {
  color: #fff;
  font-size: 18px;
  line-height: 1.6;
  max-width: 400px;
  margin-top: 60px;
}

.tagline strong {
  font-weight: 600;
}

.hero-card {
  background: #fff;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  max-width: 320px;
}

.session-info {
  margin-bottom: 20px;
}

.session-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.session-value {
  font-size: 24px;
  font-weight: 700;
  color: #000;
}

.session-name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
}

.cta-button {
  background: #000;
  color: #fff;
  border: none;
  padding: 14px 32px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  transition: background 0.3s;
}

.cta-button:hover {
  background: #333;
}

.decorative-plus {
  position: absolute;
  color: #1a1a1a;
  font-size: 24px;
  font-weight: 300;
}

.plus-1 { top: 280px; left: 100px; }
.plus-2 { top: 280px; left: 300px; }
.plus-3 { top: 280px; right: 400px; }
.plus-4 { top: 280px; right: 150px; }

.footer-text {
  position: absolute;
  bottom: 40px;
  right: 60px;
  color: #666;
  font-size: 13px;
}

.clients {
  background: #fff;
  border-radius: 24px;
  margin: 20px;
  padding: 40px 60px;
}

.clients-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.clients-title {
  font-size: 14px;
  color: #000;
  display: flex;
  align-items: center;
  gap: 10px;
}

.clients-count {
  color: #666;
}

.clients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.client-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  font-weight: 700;
  font-size: 20px;
}

.projects {
  margin: 80px 20px;
  padding: 0 60px;
}

.projects-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 60px;
}

.projects-title {
  font-size: clamp(48px, 8vw, 96px);
  font-weight: 700;
  line-height: 1;
  letter-spacing: -3px;
}

.projects-year {
  font-size: 24px;
  margin-top: 10px;
}

.projects-description {
  max-width: 400px;
  font-size: 15px;
  line-height: 1.6;
  color: #666;
}

.projects-number {
  font-size: 18px;
  color: #000;
  margin-bottom: 40px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 30px;
  margin-top: 60px;
}

.feature-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  border: 1px solid #e0e0e0;
}

.feature-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 12px;
}

.feature-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.feature-description {
  font-size: 15px;
  line-height: 1.6;
  color: #666;
}

.rating {
  display: flex;
  gap: 4px;
  margin-top: 20px;
}

.star {
  width: 20px;
  height: 20px;
  background: #FFD700;
  clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%);
}

@media (max-width: 1024px) {
  .hero-content {
    flex-direction: column;
    text-align: center;
  }

  .hero-text {
    max-width: 100%;
  }

  .tagline {
    margin: 40px auto 0;
  }

  .decorative-plus {
    display: none;
  }

  .projects-header {
    flex-direction: column;
    gap: 30px;
  }
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
  }

  .hamburger {
    display: flex;
  }

  .hero, .clients {
    padding: 40px 30px;
    margin: 10px;
  }

  nav {
    padding: 0 20px;
  }

  .projects {
    padding: 0 30px;
    margin: 40px 10px;
  }

  .footer-text {
    bottom: 20px;
    right: 30px;
  }
}
</style>
