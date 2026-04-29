const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("csv-file");
const uploadMessage = document.getElementById("upload-message");
const reviewsBody = document.getElementById("reviews-body");

const statsTargets = {
  positive: document.getElementById("positive-stat"),
  negative: document.getElementById("negative-stat"),
  neutral: document.getElementById("neutral-stat"),
  total: document.getElementById("total-stat"),
};

const bars = {
  positive: document.getElementById("positive-bar"),
  negative: document.getElementById("negative-bar"),
  neutral: document.getElementById("neutral-bar"),
};

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files.length) {
    uploadMessage.textContent = "Please choose a CSV file first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  uploadMessage.textContent = "Uploading and analyzing reviews...";

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Upload failed.");
    }

    uploadMessage.textContent = `${payload.message} Added ${payload.count} review(s).`;
    fileInput.value = "";
    await loadDashboard();
  } catch (error) {
    uploadMessage.textContent = error.message;
  }
});

async function loadDashboard() {
  await Promise.all([loadReviews(), loadStats()]);
}

async function loadReviews() {
  const response = await fetch("/reviews");
  const reviews = await response.json();
  reviewsBody.innerHTML = "";

  if (!reviews.length) {
    reviewsBody.innerHTML = `
      <tr>
        <td colspan="6">No reviews uploaded yet.</td>
      </tr>
    `;
    return;
  }

  reviews.forEach((review) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${review.id}</td>
      <td>${escapeHtml(review.original_text)}</td>
      <td>${escapeHtml(review.processed_text)}</td>
      <td>
        <span class="sentiment-pill sentiment-${review.sentiment}">
          ${review.sentiment}
        </span>
      </td>
      <td>${Number(review.score).toFixed(2)}</td>
      <td>${new Date(review.created_at).toLocaleString()}</td>
    `;
    reviewsBody.appendChild(row);
  });
}

async function loadStats() {
  const response = await fetch("/stats");
  const stats = await response.json();

  statsTargets.positive.textContent = `${stats.positive_percentage}%`;
  statsTargets.negative.textContent = `${stats.negative_percentage}%`;
  statsTargets.neutral.textContent = `${stats.neutral_percentage}%`;
  statsTargets.total.textContent = stats.total_reviews;

  bars.positive.style.width = `${stats.positive_percentage}%`;
  bars.negative.style.width = `${stats.negative_percentage}%`;
  bars.neutral.style.width = `${stats.neutral_percentage}%`;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadDashboard();
