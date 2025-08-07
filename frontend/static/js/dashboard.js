const accessToken = localStorage.getItem("access_token");
const refreshToken = localStorage.getItem("refresh_token");
console.log("Js loaded");

fetch("/dashboard", {
  method: "GET",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "X-Refresh-Token": refreshToken,
  },
})
  .then(async (response) => {
    if (response.ok) {
      const text = await response.text();
      // Отобразить полученный html (если SPA — по-другому)
      document.open();
      document.write(text);
      document.close();

      // Если сервер отправил новый access токен в заголовках — обновим localStorage
      const newAccessToken = response.headers.get("X-New-Access-Token");
      if (newAccessToken) {
        localStorage.setItem("access_token", newAccessToken);
      }
    } else {
      // Обработка ошибок (например, редирект на /login)
      window.location.href = "/login";
    }
  })
  .catch((err) => {
    console.error("Ошибка запроса:", err);
  });
