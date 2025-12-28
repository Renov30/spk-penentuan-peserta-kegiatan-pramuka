function redirectToLoginWithGoogle() {
  let next = window.location.pathname + window.location.search;

  if (next === "/login" || next === "/login/") {
    next = "";
  }

  const url = next
    ? `/login/google/?next=${encodeURIComponent(next)}`
    : `/login/google/`;

  window.location.href = url;
}
