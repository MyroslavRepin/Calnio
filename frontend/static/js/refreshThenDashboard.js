// static/js/refreshThenDashboard.js

async function refreshAndOpenDashboard() {
  try {
    // Отправляем POST-запрос на /refresh, чтобы обновить токен
    const refreshResponse = await fetch("/refresh", {
      method: "POST",
      credentials: "include", // важно, чтобы куки шли
    });

    if (!refreshResponse.ok) {
      // Если обновление токена не удалось — редирект на логин
      window.location.href = "/login";
      return;
    }

    // Если обновление прошло успешно — открываем /dashboard
    window.location.href = "/dashboard";
  } catch (error) {
    console.error("Ошибка обновления токена:", error);
    // При ошибке тоже редирект на логин
    window.location.href = "/login";
  }
}

// Запускаем сразу после загрузки страницы
document.addEventListener("DOMContentLoaded", refreshAndOpenDashboard);
