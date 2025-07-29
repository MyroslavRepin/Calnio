// static/js/dashboard.js

import { fetchWithAutoRefresh } from "./api.js";

document.addEventListener("DOMContentLoaded", () => {
  // Просто вызываем запрос к защищённому эндпоинту /dashboard, чтобы проверить авторизацию и обновить токен
  fetchWithAutoRefresh("/dashboard")
    .then((res) => {
      if (!res.ok) throw new Error(`Ошибка ${res.status}`);
      return res.text(); // предположим, что /dashboard отдает html
    })
    .then((html) => {
      console.log("Dashboard загружен успешно");
      // Можешь вставить html куда надо или просто использовать для проверки
    })
    .catch((err) => {
      console.error("Ошибка доступа к /dashboard:", err);
    });
});
