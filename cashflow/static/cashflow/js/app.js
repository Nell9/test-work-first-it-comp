// Небольшой набор хелперов для общения с REST API.
// Намеренно без сторонних библиотек — хватает fetch.

// Достаём CSRF-токен из куки (её ставит Django на страницах через ensure_csrf_cookie).
function getCookie(name) {
  const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return match ? decodeURIComponent(match.pop()) : "";
}

const API = {
  async request(method, url, data) {
    const options = {
      method,
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    };
    if (data !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(data);
    }
    const response = await fetch(url, options);

    // DELETE обычно возвращает пустое тело — отдельно обрабатываем.
    let payload = null;
    if (response.status !== 204) {
      const text = await response.text();
      payload = text ? JSON.parse(text) : null;
    }
    if (!response.ok) {
      throw { status: response.status, data: payload };
    }
    return payload;
  },
  get(url) {
    return this.request("GET", url);
  },
  post(url, data) {
    return this.request("POST", url, data);
  },
  put(url, data) {
    return this.request("PUT", url, data);
  },
  patch(url, data) {
    return this.request("PATCH", url, data);
  },
  del(url) {
    return this.request("DELETE", url);
  },
};

// Превращаем ответ DRF с ошибками валидации в читаемый текст.
function formatApiError(error) {
  if (!error || !error.data) {
    return "Не удалось выполнить запрос. Попробуйте ещё раз.";
  }
  const data = error.data;
  if (typeof data === "string") {
    return data;
  }
  if (data.detail) {
    return data.detail;
  }
  // Собираем сообщения по полям.
  const parts = [];
  for (const [field, messages] of Object.entries(data)) {
    const text = Array.isArray(messages) ? messages.join(" ") : messages;
    parts.push(`${field}: ${text}`);
  }
  return parts.join("\n") || "Ошибка запроса.";
}

// Простейшее экранирование, чтобы пользовательский текст не ломал разметку.
function escapeHtml(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
