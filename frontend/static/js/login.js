document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");
  const loginBtn = document.getElementById("loginBtn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault(); // Отменяем обычную отправку формы

    const login = document.getElementById("login").value.trim();
    const password = document.getElementById("password").value;

    if (!login || !password) {
      alert("Пожалуйста, заполните все поля!");
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = "Вход...";

    try {
      const body = new URLSearchParams();
      body.append("login", login);
      body.append("password", password);

      const response = await fetch("/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
      });

      if (!response.ok) {
        // Получаем html с ошибкой и показываем его (перезагрузка формы с ошибкой от сервера)
        const html = await response.text();
        document.open();
        document.write(html);
        document.close();
        return;
      }

      const data = await response.json();

      console.log("Токены получены:", data);

      // Сохраняем в localStorage
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);

      // Переходим на dashboard
      window.location.href = "/dashboard";
    } catch (error) {
      console.error("Ошибка при входе:", error);
      alert("Ошибка соединения с сервером, попробуйте позже.");
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = "Sign In";
    }
  });
});
