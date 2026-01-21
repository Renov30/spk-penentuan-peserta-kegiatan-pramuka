// ================= MODAL LOGIN =================
console.log("[DEBUG] news_detail.js loaded");
const lang = document.body.dataset.lang || "id";
const messages = {
  id: {
    reply: "Balas",
    seeReplies: (count) => `Lihat ${count} balasan lainnya`,
    seeReplies2: "Lihat balasan lainnya",
    hideReplies: "Sembunyikan balasan",
    delete: "Hapus",
    cancel: "Batal",
    send: "Kirim",
    deleteConfirm: "Apakah Anda yakin ingin menghapus komentar ini?",
  },
  en: {
    reply: "Reply",
    cancel: "Cancel",
    seeReplies: (count) => `See ${count} more replies`,
    seeReplies2: "See more replies",
    hideReplies: "Hide replies",
    delete: "Delete",
    cancel: "Cancel",
    send: "Send",
    deleteConfirm: "Are you sure you want to delete this comment?",
  },
};

// pilih pesan sesuai bahasa
const t = messages[lang];

function openLoginModal() {
  const modal = document.getElementById("loginModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeLoginModal() {
  const modal = document.getElementById("loginModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

// ================= UTIL =================
function escapeHTML(str) {
  return str.replace(
    /[&<>"']/g,
    (m) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[m],
  );
}

// ================= RENDER COMMENT =================
function renderComment(comment) {
  if (!comment || !comment.user) return "";

  const isReply = comment.parent_id !== null;
  const userName = comment.user.nama_lengkap || "User";
  const foto = comment.user.foto;
  const defaultFoto = "/static/images/profil-default.jpg";
  let avatar = "";

  // ===== AVATAR LOGIC (MENIRU JINJA) =====
  if (foto && typeof foto === "string") {
    let fotoUrl = null;
    if (foto.startsWith("http://") || foto.startsWith("https://")) {
      fotoUrl = foto;
    } else if (foto.startsWith("uploads/") || foto.startsWith("img/")) {
      fotoUrl = `/static/${foto}`;
    }
    if (fotoUrl) {
      avatar = `
        <img
          src="${fotoUrl}"
          alt="Foto ${escapeHTML(userName)}"
          class="w-8 h-8 rounded-full object-cover"
          onerror="this.src='${defaultFoto}'"
        />
      `;
    }
  }

  // ===== FALLBACK ICON =====
  if (!avatar) {
    avatar = `
      <div class="w-8 h-8 rounded-full bg-gray-400 text-white
                  flex items-center justify-center">
        <i class="fa-solid fa-user text-sm"></i>
      </div>
    `;
  }

  return `
    <div id="comment-${comment.id}" class="mb-6 ${
      isReply ? "ml-6 border-l pl-4" : ""
    }">
      <div class="flex items-start gap-3">
        ${avatar}
        <div class="w-full">
          <p class="font-semibold">${escapeHTML(userName)}</p>
          <p class="text-sm {{ 'text-gray-400' if current_theme == 'dark' else 'text-gray-600' }}">${escapeHTML(
            comment.content,
          )}</p>
          <div class="flex gap-4 text-xs mt-1">
            <button id="reply-btn-${comment.id}" onclick="openReplyForm(${
              comment.id
            }, '${escapeHTML(
              userName,
            )}')" class="text-blue-600 hover:text-blue-700 cursor-pointer">${
              t.reply
            }</button>
            ${
              comment.is_owner
                ? `
                    <div class="text-xs text-gray-400 gap-4">
                      <button
                        onclick="editComment(${comment.id})"
                        class="edit-btn text-yellow-500 hover:text-yellow-600 cursor-pointer">
                        Edit
                      </button>
                      ·
                      <button
                        onclick="deleteComment(${comment.id})"
                        class="text-red-500 hover:text-red-600 cursor-pointer">
                        ${t.delete}
                      </button>
                    </div>
                  `
                : ""
            }
            <button onclick="likeComment(${
              comment.id
            }, this)" class="like-btn text-xs flex items-center gap-1 ${
              comment.is_liked ? "text-red-500" : "text-gray-500"
            } hover:text-red-500 transition cursor-pointer">
              <span class="heart">❤️</span>
              <span class="like-count">${comment.likes}</span>
            </button>
            ${
              !isReply && comment.reply_count > 0
                ? `<button data-state="hidden" onclick="toggleReplies(${
                    comment.id
                  }, this)" class="text-yellow-500 hover:text-yellow-600 cursor-pointer">${t.seeReplies(
                    comment.reply_count,
                  )}</button>`
                : ""
            }
          </div>
          <div id="reply-form-${comment.id}" class="hidden mt-2"></div>
          <div id="replies-${comment.id}" class="mt-3 hidden"></div>
        </div>
      </div>
    </div>
  `;
}

// ================= Toggle Replies =================
function toggleReplies(commentId, button) {
  const container = document.getElementById(`replies-${commentId}`);
  const state = button.dataset.state;

  // === HIDE ===
  if (state === "shown") {
    container.classList.add("hidden");
    button.textContent = t.seeReplies2;
    button.dataset.state = "hidden";
    return;
  }

  // === FIRST LOAD ===
  if (!container.dataset.loaded) {
    fetch(`/news/comment/${commentId}/replies`)
      .then((res) => res.json())
      .then((data) => {
        container.innerHTML = data.replies.map(renderComment).join("");
        container.dataset.loaded = "1";
        container.classList.remove("hidden");
        button.textContent = t.hideReplies;
        button.dataset.state = "shown";
      });
  } else {
    container.classList.remove("hidden");
    button.textContent = t.hideReplies;
    button.dataset.state = "shown";
  }
}

// ================= FORM BALAS + TAG USER (@username) =================
function openReplyForm(commentId, userName) {
  closeReplyForm(commentId);

  const container = document.getElementById(`reply-form-${commentId}`);
  const replyBtn = document.getElementById(`reply-btn-${commentId}`);
  container.innerHTML = `
    <form class="reply-form" data-parent="${commentId}">
      <textarea
        rows="2"
        required
        class="w-full p-2 border rounded text-sm"
      >@${userName} </textarea>

      <div class="flex gap-3 mt-2">
        <button
          type="submit"
          class="text-xs bg-yellow-500 hover:bg-yellow-600 px-3 py-1 rounded text-white cursor-pointer">
          ${t.send}
        </button>

        <button
          type="button"
          onclick="closeReplyForm(${commentId})"
          class="text-xs bg-red-500 hover:bg-red-600 px-3 py-1 rounded text-white cursor-pointer">
          ${t.cancel}
        </button>
      </div>
    </form>
  `;

  container.classList.remove("hidden");
  if (replyBtn) replyBtn.classList.add("hidden");

  const textarea = container.querySelector("textarea");
  textarea.focus();
  const cancelBtn = container.querySelector("button[type='button']");
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => closeReplyForm(commentId));
  }
}

function closeReplyForm(commentId) {
  const container = document.getElementById(`reply-form-${commentId}`);
  const replyBtn = document.getElementById(`reply-btn-${commentId}`);
  if (!container) return;
  container.innerHTML = "";
  container.classList.add("hidden");
  if (replyBtn) replyBtn.classList.remove("hidden");
}

// ================= COMMENTS SCROLL =================
let commentPage = 1;
let loadingComments = false;
let hasNextComments = true;

function enableCommentsScroll(slug) {
  const container = document.getElementById("comments-container");
  if (!container) return;

  container.style.maxHeight = "400px";
  container.style.overflowY = "auto";
  let debounceTimer;
  container.addEventListener("scroll", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (
        container.scrollTop + container.clientHeight >=
        container.scrollHeight - 10
      ) {
        loadComments(slug);
      }
    }, 100);
  });
}

// ================= LOADER =================
function showLoader() {
  let loader = document.getElementById("comments-loader");
  if (!loader) {
    loader = document.createElement("div");
    loader.id = "comments-loader";
    loader.className = "text-center py-2";
    loader.innerHTML = `<span class="text-gray-500">Loading...</span>`;
    document.getElementById("comments-container").appendChild(loader);
  }
  loader.style.display = "block";
}

function hideLoader() {
  const loader = document.getElementById("comments-loader");
  if (loader) loader.style.display = "none";
}

// ================= LOAD COMMENTS =================
function loadComments(slug, reset = false) {
  const container = document.getElementById("comments-container");
  const count = document.getElementById("comment-count");
  const emptyState = document.getElementById("empty-comments");
  if (!container) return;

  if (reset) {
    container.innerHTML = "";
    commentPage = 1;
    hasNextComments = true;
    container.scrollTop = 0; // reset scroll
  }

  if (loadingComments || !hasNextComments) return;
  loadingComments = true;
  showLoader();
  fetch(`/news/${slug}/comments?page=${commentPage}`)
    .then((res) => res.json())
    .then((data) => {
      count.textContent = `(${data.total})`;
      if (data.total === 0) emptyState.classList.remove("hidden");
      else emptyState.classList.add("hidden");

      data.comments.forEach((comment) => {
        container.insertAdjacentHTML("beforeend", renderComment(comment));
      });

      commentPage++;
      hasNextComments = data.has_next;
      loadingComments = false;
      hideLoader();

      if (!container.dataset.scrollAttached) {
        enableCommentsScroll(slug);
        container.dataset.scrollAttached = "1";
      }
      checkAutoLoad(slug);
    })
    .catch((err) => {
      console.error("Load comments error:", err);
      loadingComments = false;
      hideLoader();
    });
}

// ================= AUTO LOAD UNTUK SCROLL =================
function checkAutoLoad(slug) {
  const container = document.getElementById("comments-container");
  if (!container) return;
  while (container.scrollHeight <= container.clientHeight && hasNextComments) {
    loadComments(slug);
  }
}

// ================= INIT =================
document.addEventListener("DOMContentLoaded", () => {
  const slug = document.body.dataset.slug;
  if (slug) loadComments(slug, true);
  initCommentForm();
  initInlineReactions();
  initShareButtons();
});

// ================= LOAD BALASAN (ON DEMAND) =================
function loadReplies(commentId, button) {
  const container = document.getElementById(`replies-${commentId}`);

  if (!container.classList.contains("hidden")) {
    container.classList.add("hidden");
    return;
  }

  fetch(`/news/comment/${commentId}/replies`)
    .then((res) => res.json())
    .then((data) => {
      container.innerHTML = data.replies
        .map((reply) => renderComment(reply))
        .join("");

      container.classList.remove("hidden");
      button.remove();
    })
    .catch((err) => console.error("Load replies error:", err));
}

// ================= SHARE BUTTON INTERACTIONS =================
function initShareButtons() {
  const buttons = document.querySelectorAll("#shareNav .share-btn");
  if (!buttons.length) return;

  buttons.forEach((btn) => {
    // === MOUSE EVENTS ===
    btn.addEventListener("mouseenter", () => {
      btn.classList.add("ring-2", "ring-white/70");
    });

    btn.addEventListener("mouseleave", () => {
      btn.classList.remove("ring-2", "ring-white/70");
    });

    // === KEYBOARD EVENTS ===
    btn.addEventListener("keydown", (e) => {
      // Enter / Space → trigger click
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        btn.click();
      }

      // Escape → blur (keluar fokus)
      if (e.key === "Escape") {
        btn.blur();
      }
    });

    // === CLICK FEEDBACK ===
    btn.addEventListener("click", () => {
      btn.classList.add("scale-90");
      setTimeout(() => btn.classList.remove("scale-90"), 150);
    });
  });
}

// ================= SUBMIT KOMENTAR =================
function initCommentForm() {
  const form = document.getElementById("commentForm");
  if (!form) return;
  const slug = document.body.dataset.slug;
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const textarea = this.querySelector("textarea");
    const content = textarea.value.trim();
    if (!content) return;

    fetch(this.dataset.action, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf,
      },
      body: JSON.stringify({ content }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          textarea.value = "";
          loadComments(slug, true);
        } else {
          alert(data.message || "Gagal mempublikasikan komentar.");
        }
      })
      .catch(() => alert("Terjadi kesalahan."));
  });
}

// ================= SUBMIT REPLY (EVENT DELEGATION) =================
document.addEventListener("submit", function (e) {
  if (!e.target.classList.contains("reply-form")) return;
  e.preventDefault();

  const slug = document.body.dataset.slug;
  const parentId = e.target.dataset.parent;
  const textarea = e.target.querySelector("textarea");
  const content = textarea.value.trim();
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  if (!content) return;
  fetch(`/news/${slug}/comment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf,
    },
    body: JSON.stringify({ content, parent_id: parentId }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        textarea.value = "";
        closeReplyForm(parentId);

        const repliesContainer = document.getElementById(`replies-${parentId}`);
        if (repliesContainer) {
          if (repliesContainer.classList.contains("hidden")) {
            repliesContainer.classList.remove("hidden");
          }
          const newReplyHTML = renderComment(data.comment);
          repliesContainer.insertAdjacentHTML("beforeend", newReplyHTML);
          const newEl = document.getElementById(`comment-${data.comment.id}`);
          if (newEl) {
            newEl.scrollIntoView({ behavior: "smooth", block: "center" });
            newEl.classList.add("bg-gray-700", "animate-pulse");
            setTimeout(() => {
              newEl.classList.remove("bg-gray-700", "animate-pulse");
            }, 2000);
          }
        }
      } else {
        alert(data.message || "Gagal mempublikasikan balasan.");
      }
    })
    .catch(() => alert("Terjadi kesalahan saat mempublikasikan balasan."));
});

// ================= LIKE COMMENT (REALTIME + ANIMATION) =================
function likeComment(commentId, button) {
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  fetch(`/news/comment/${commentId}/like`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrf,
    },
  })
    .then((res) => res.json())
    .then((data) => {
      if (!data.success) {
        alert(data.message || "Gagal memberi like");
        return;
      }

      const heart = button.querySelector(".heart");
      const countEl = button.querySelector(".like-count");
      countEl.textContent = data.likes;

      if (data.is_liked) {
        button.classList.remove("text-gray-500");
        button.classList.add("text-red-500");
        heart.classList.add("animate-bounce", "scale-125");
      } else {
        button.classList.remove("text-red-500");
        button.classList.add("text-gray-500");
        heart.classList.add("animate-pulse");
      }
      setTimeout(() => {
        heart.classList.remove("animate-bounce", "animate-pulse", "scale-125");
      }, 600);
    })
    .catch(() => {
      alert("Terjadi kesalahan saat like komentar");
    });
}

// ================= DELETE COMENT =================
function deleteComment(id) {
  showConfirmModal(t.deleteConfirm, () => {
    fetch(`/comment/${id}/delete`, {
      method: "POST",
      headers: {
        "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')
          .content,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          document.getElementById(`comment-${id}`)?.remove();

          const commentEl = document.getElementById(`comment-${id}`);
          if (commentEl) {
            commentEl.classList.add(
              "opacity-0",
              "transition-all",
              "duration-300",
            );
            setTimeout(() => commentEl.remove(), 300);
          }

          const repliesEl = document.getElementById(`replies-${id}`);
          if (repliesEl) {
            repliesEl.classList.add(
              "opacity-0",
              "transition-all",
              "duration-300",
            );
            setTimeout(() => repliesEl.remove(), 300);
          }

          const count = document.getElementById("comment-count");
          if (count) {
            let total = parseInt(count.textContent.replace(/[()]/g, "")) || 0;
            total = Math.max(total - 1, 0);
            count.textContent = `(${total})`;
          }

          if (
            container &&
            hasNextComments &&
            container.scrollHeight <= container.clientHeight
          ) {
            loadComments(slug);
          }

          alert(data.message);
        } else {
          alert(data.message || "Terjadi kesalahan saat menghapus komentar");
        }
      })
      .catch((err) => {
        console.error("Delete comment error:", err);
        alert("Terjadi kesalahan saat menghapus komentar");
      });
  });
}

// ================= EDIT KOMENTAR =================
function editComment(id) {
  const commentEl = document.getElementById(`comment-${id}`);
  if (!commentEl) return;
  const contentEl = commentEl.querySelector("p.text-sm.text-gray-400");
  const originalContent = contentEl.textContent;
  const editBtn = commentEl.querySelector(".edit-btn");
  if (editBtn) editBtn.style.display = "none";

  // Tampilkan form edit
  contentEl.innerHTML = `
    <textarea class="w-full p-2 border rounded text-sm">${originalContent}</textarea>
    <div class="flex gap-2 mt-2">
      <button type="button" class="save-btn bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded cursor-pointer">${t.send}</button>
      <button type="button" class="cancel-btn bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded cursor-pointer">${t.cancel}</button>
    </div>
  `;

  const textarea = contentEl.querySelector("textarea");
  textarea.focus();
  const cancelEdit = () => {
    contentEl.textContent = originalContent;
    if (editBtn) editBtn.style.display = "inline-block";
  };

  contentEl.querySelector(".cancel-btn").onclick = cancelEdit;
  contentEl.querySelector(".save-btn").onclick = () => {
    const newContent = textarea.value.trim();
    if (!newContent) {
      alert(t.emptyContent);
      return;
    }

    const csrf = document.querySelector('meta[name="csrf-token"]').content;
    fetch(`/comment/${id}/edit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf,
      },
      body: JSON.stringify({ content: newContent }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          contentEl.textContent = data.comment.content;
          commentEl.classList.add("bg-gray-700", "animate-pulse");
          setTimeout(
            () => commentEl.classList.remove("bg-gray-700", "animate-pulse"),
            2000,
          );
          if (editBtn) editBtn.style.display = "inline-block";
        } else {
          alert(data.message || "Terjadi kesalahan saat mengedit komentar.");
        }
      })
      .catch(() => alert("Terjadi kesalahan saat mengedit komentar."));
  };
}

// ================= MODAL KONFIRMASI =================
function showConfirmModal(message, onConfirm) {
  let modal = document.getElementById("confirmModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "confirmModal";
    modal.className = `
      fixed inset-0 z-50 flex items-center justify-center 
      bg-black/50 backdrop-blur-sm hidden
    `;
    modal.innerHTML = `
      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-xl w-full max-w-sm p-6 transform transition-transform duration-200 scale-95">
        <p class="text-center text-gray-800 dark:text-gray-200 mb-6" id="confirmMessage"></p>
        <div class="flex justify-center gap-4">
          <button id="confirmCancelBtn" class="px-4 py-2 rounded-lg bg-gray-300 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-400 dark:hover:bg-gray-600 cursor-pointer">${t.cancel}</button>
          <button id="confirmOkBtn" class="px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600 cursor-pointer">${t.delete}</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  modal.querySelector("#confirmMessage").textContent = message;
  modal.classList.remove("hidden");
  setTimeout(() => {
    modal.querySelector("div").classList.remove("scale-95");
  }, 10);
  const closeModal = () => {
    modal.querySelector("div").classList.add("scale-95");
    setTimeout(() => modal.classList.add("hidden"), 200);
  };
  modal.querySelector("#confirmCancelBtn").onclick = closeModal;
  modal.querySelector("#confirmOkBtn").onclick = () => {
    onConfirm();
    closeModal();
  };
}

// ================= INIT =================
document.addEventListener("DOMContentLoaded", () => {
  const slug = document.body.dataset.slug;
  if (slug) loadComments(slug);
  initCommentForm();
});

// ================= LOGIN REDIRECT (HEADER ICON) =================
document.addEventListener("click", function (e) {
  const link = e.target.closest("[data-login-intent]");
  if (!link) return;
  e.preventDefault();
  const next = window.location.pathname + window.location.search;
  fetch("/api/auth/intent", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    credentials: "same-origin",
    body: JSON.stringify({ next }),
  }).then(() => {
    window.location.href = link.href;
  });
});

// ================= SIMPLE INLINE REACTIONS =================
function initInlineReactions() {
  const buttons = document.querySelectorAll(".reaction-btn");
  if (!buttons.length) return;

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const emoji = btn.dataset.emoji;
      if (!emoji) return;

      btn.textContent = emoji;
      btn.classList.add("animate-bounce");

      setTimeout(() => {
        btn.classList.remove("animate-bounce");
      }, 600);

      alert(`You reacted with ${emoji}!`);
    });
  });
}
