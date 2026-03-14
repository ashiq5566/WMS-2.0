export default defineNuxtRouteMiddleware((to, from) => {
  const access = useCookie("access");

  // If no access token, redirect to login
  if (!access.value) {
    return navigateTo("/login");
  }
});
