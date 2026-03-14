// import axios from "axios";

// export default defineNuxtPlugin(() => {
//   const api = axios.create({
//     baseURL: "http://127.0.0.1:8000", // your Django backend
//   });

//   return {
//     provide: {
//       axios: api,
//     },
//   };
// });

import axios from "axios";

export default defineNuxtPlugin((nuxtApp) => {
  const api = axios.create({
    baseURL: "http://127.0.0.1:8000",
  });

  api.interceptors.request.use((config) => {
    // SSR-safe token access
    const accessToken = useCookie("access").value;

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  });

  api.interceptors.response.use(
    (res) => res,
    (err) => {
      if (err.response?.status === 401) {
        // Clear tokens (SSR-safe)
        useCookie("access").value = null;
        useCookie("refresh").value = null;

        if (import.meta.client) {
          navigateTo("/login");
        }
      }
      return Promise.reject(err);
    }
  );

  return {
    provide: { axios: api },
  };
});
