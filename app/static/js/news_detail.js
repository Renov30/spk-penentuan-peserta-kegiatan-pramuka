// --- Modal Login ---
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

// --- Toggle Reply Form ---
function toggleReplyForm(id) {
  const el = document.getElementById(`reply-form-${id}`);
  if (el) el.classList.toggle("hidden");
}

// --- Render Comment & Replies (Recursive) ---
function renderComment(comment) {
  let repliesHTML = "";
  if (comment.replies && comment.replies.length > 0) {
    comment.replies.forEach((reply) => {
      repliesHTML += `
        <div class="ml-6 mt-3 border-l pl-4">
          <p class="font-semibold text-sm">${reply.user.nama_lengkap}</p>
          <p class="text-sm">${reply.content}</p>
          <div class="mt-1">
            <button onclick="toggleReplyForm(${
              reply.id
            })" class="text-xs text-yellow-500 cursor-pointer">Balas</button>
          </div>
          <div id="reply-form-${reply.id}" class="hidden mt-2">
            <form onsubmit="submitReply(event, ${reply.id}, '${comment.slug}')">
              <textarea name="content" rows="2" class="w-full p-2 border rounded" required></textarea>
              <button type="submit" class="text-sm text-white bg-yellow-500 px-3 py-1 rounded mt-1 cursor-pointer">Kirim</button>
            </form>
          </div>
          ${reply.replies ? renderComment(reply) : ""}
        </div>
      `;
    });
  }

  return `
    <div class="mb-6" id="comment-${comment.id}">
      <p class="font-semibold">${comment.user.nama_lengkap}</p>
      <p class="text-sm text-gray-700">${comment.content}</p>
      <div class="flex gap-2 mt-1">
        <button onclick="toggleReplyForm(${
          comment.id
        })" class="text-xs text-yellow-500 cursor-pointer">Balas</button>
        <button onclick="likeComment(${comment.id})" class="text-xs">👍 ${
    comment.likes || 0
  }</button>
      </div>
      <div id="reply-form-${comment.id}" class="hidden mt-2">
        <form onsubmit="submitReply(event, ${comment.id}, '${comment.slug}')">
          <textarea name="content" rows="2" class="w-full p-2 border rounded" required></textarea>
          <button type="submit" class="text-sm text-white bg-yellow-500 px-3 py-1 rounded mt-1 cursor-pointer">Kirim</button>
        </form>
      </div>
      ${repliesHTML}
    </div>
  `;
}

// --- Load Comments via AJAX ---
let commentPage = 1;
function loadComments(slug) {
  const container = document.getElementById("comments-container");
  const count = document.getElementById("comment-count");

  fetch(`/news/${slug}/comments?page=${commentPage}`)
    .then((res) => res.json())
    .then((data) => {
      if (!container || !count) return;

      count.textContent = `(${data.total})`;

      data.comments.forEach((comment) => {
        container.insertAdjacentHTML("beforeend", renderComment(comment));
      });

      commentPage++;
    })
    .catch((err) => console.error("Load comments error:", err));
}

// --- Submit Comment via AJAX ---
function initCommentForm() {
  const commentForm = document.getElementById("commentForm");
  if (!commentForm) return;

  const container = document.getElementById("comments-container");
  const count = document.getElementById("comment-count");

  commentForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const textarea = this.querySelector('textarea[name="content"]');
    const content = textarea.value.trim();
    if (!content) return;

    fetch(this.dataset.action, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.dataset.csrf,
      },
      body: JSON.stringify({ content }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          textarea.value = "";
          container.insertAdjacentHTML(
            "afterbegin",
            renderComment(data.comment)
          );
          count.textContent = `(${data.total_comments})`;
        } else {
          alert(data.message || "Gagal mempublikasikan komentar.");
        }
      })
      .catch((err) => {
        console.error(err);
        alert("Terjadi kesalahan saat mengirim komentar.");
      });
  });
}

// --- Submit Reply via AJAX ---
function submitReply(event, parentId, slug) {
  event.preventDefault();
  const form = event.target;
  const textarea = form.querySelector('textarea[name="content"]');
  const content = textarea.value.trim();
  if (!content) return;

  fetch(`/news/${slug}/comment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.querySelector("#commentForm").dataset.csrf,
    },
    body: JSON.stringify({ content, parent_id: parentId }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        textarea.value = "";
        const parentDiv = document.getElementById(`comment-${parentId}`);
        parentDiv.insertAdjacentHTML("beforeend", renderComment(data.comment));
      } else {
        alert(data.message || "Gagal mempublikasikan balasan.");
      }
    })
    .catch((err) => {
      console.error(err);
      alert("Terjadi kesalahan saat mengirim balasan.");
    });
}

// --- Like Comment via AJAX ---
function likeComment(commentId) {
  fetch(`/news/comment/${commentId}/like`, { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const button = document.querySelector(
          `#comment-${commentId} button[onclick*="likeComment"]`
        );
        if (button) button.textContent = `👍 ${data.likes}`;
      } else {
        alert(data.message || "Gagal menyukai komentar.");
      }
    })
    .catch((err) => console.error(err));
}

// --- Initialize on DOMContentLoaded ---
document.addEventListener("DOMContentLoaded", () => {
  const slug = document.body.dataset.slug;
  if (slug) loadComments(slug);
  initCommentForm();
});
