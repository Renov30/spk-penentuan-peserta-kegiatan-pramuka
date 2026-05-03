function redirectToRegisterWithGoogle() {
  const base = window.location.pathname.includes('/saringpramuka') ? '/saringpramuka' : '';
  window.location.href = base + "/login/google?mode=register";
}
