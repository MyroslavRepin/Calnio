// static/js/api.js

export async function fetchWithAutoRefresh(url, options = {}) {
  options.credentials = "include";
  options.method = options.method || "GET";

  let response = await fetch(url, options);

  if (response.status === 401) {
    console.warn("Access token expired. Attempting refresh...");

    const refreshResponse = await fetch("/refresh", {
      method: "POST",
      credentials: "include",
    });

    if (refreshResponse.ok) {
      console.log("Token refreshed successfully. Retrying request...");
      response = await fetch(url, options);
    } else {
      console.error("Token refresh failed. Redirecting to login...");
      window.location.href = "/login";
    }
  }

  return response;
}
