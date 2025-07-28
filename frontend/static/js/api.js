// fetchWithRefresh.js

async function fetchWithRefresh(url, options = {}) {
  options.credentials = "include"; // чтобы куки автоматически отправлялись

  let response = await fetch(url, options);

  if (response.status === 401) {
    // access токен истёк, пробуем обновить
    const refreshResponse = await fetch("/refresh", {
      method: "POST",
      credentials: "include",
    });

    if (refreshResponse.ok) {
      // обновление прошло успешно, повторяем исходный запрос
      response = await fetch(url, options);
    } else {
      // refresh не удался, нужно логиниться заново
      throw new Error("Сессия истекла, пожалуйста, войдите заново");
    }
  }
  return response;
}

// Пример использования:

async function getProtectedData() {
  try {
    const response = await fetchWithRefresh("/protected");
    if (response.ok) {
      const data = await response.json();
      console.log("Данные с защищённого роута:", data);
    } else {
      console.error("Ошибка при получении данных:", response.status);
    }
  } catch (error) {
    console.error(error.message);
    // Тут можно сделать редирект на страницу логина или показать сообщение
  }
}

// Можно вызвать функцию, например, при загрузке страницы или по кнопке
getProtectedData();
