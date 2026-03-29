<script setup>
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend
} from "chart.js"
import {onMounted, ref} from "vue";
import { API_BASE_URL } from "@/config/api.js";
import axios from "axios";

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend
)

const chartCanvas = ref(null)
let chartInstance = null



onMounted(() => {
  chartInstance = new Chart(chartCanvas.value, {
    type: "line",
    data: {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri"],
      datasets: [
        {
          label: "Productivity",
          data: [5, 8, 6, 9, 7],
          borderColor: "rgb(75, 192, 192)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderWidth: 2,
          tension: 0.1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: "top"
        },
        title: {
          display: true,
          text: "Weekly Productivity"
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  })
})

</script>

<template>
  <h2>Summary</h2>
  <canvas ref="chartCanvas"></canvas>
</template>

<style scoped>
h2{
  color: var(--color-primary);
}
</style>