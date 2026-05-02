const collectForm = document.getElementById("collect-form");
const marketplaceInput = document.getElementById("marketplace");
const productIdInput = document.getElementById("product-id");
const dateFromInput = document.getElementById("date-from");
const dateToInput = document.getElementById("date-to");
const collectMessage = document.getElementById("collect-message");
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("csv-file");
const uploadMessage = document.getElementById("upload-message");
const reviewsBody = document.getElementById("reviews-body");
const problemsBody = document.getElementById("problems-body");
const insightsSummary = document.getElementById("insights-summary");
const riskLevel = document.getElementById("risk-level");
const recommendationsList = document.getElementById("recommendations-list");

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

const sentimentLabels = {
  positive: "позитив",
  negative: "негатив",
  neutral: "нейтрально",
};

const riskLabels = {
  low: "низкий",
  medium: "средний",
  high: "высокий",
};

const aspectLabels = {
  quality: "Качество",
  delivery: "Доставка",
  packaging: "Упаковка",
  price: "Цена",
  usability: "Удобство",
  support: "Поддержка",
};

reviewsBody.addEventListener("click", async (event) => {
  const deleteButton = event.target.closest(".delete-btn");
  if (!deleteButton) {
    return;
  }

  const reviewId = deleteButton.dataset.id;
  const row = deleteButton.closest("tr");

  deleteButton.disabled = true;

  try {
    const response = await fetch(`/reviews/${reviewId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error("Ошибка удаления");
    }

    row.remove();
    renderEmptyReviewsMessageIfNeeded();
    await Promise.all([loadStats(), loadProblems(), loadInsights()]);
  } catch (error) {
    deleteButton.disabled = false;
    alert("Ошибка удаления");
  }
});

collectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  collectMessage.textContent = "Собираем отзывы из маркетплейса...";

  try {
    const response = await fetch("/collect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        marketplace: marketplaceInput.value,
        product_id: productIdInput.value,
        date_from: dateFromInput.value || null,
        date_to: dateToInput.value || null,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(formatApiError(payload.detail, "Не удалось собрать отзывы."));
    }

    collectMessage.textContent = `Отзывы собраны и проанализированы. Добавлено: ${payload.count}.`;
    await loadDashboard();
  } catch (error) {
    collectMessage.textContent = error.message;
  }
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files.length) {
    uploadMessage.textContent = "Сначала выберите CSV-файл.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  uploadMessage.textContent = "Загружаем и анализируем отзывы...";

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(formatApiError(payload.detail, "Не удалось загрузить файл."));
    }

    uploadMessage.textContent = `Отзывы загружены и проанализированы. Добавлено: ${payload.count}.`;
    fileInput.value = "";
    await loadDashboard();
  } catch (error) {
    uploadMessage.textContent = error.message;
  }
});

async function loadDashboard() {
  await Promise.all([loadReviews(), loadStats(), loadProblems(), loadInsights()]);
}

async function loadReviews() {
  const response = await fetch("/reviews");
  const reviews = await response.json();
  reviewsBody.innerHTML = "";

  if (!reviews.length) {
    renderEmptyReviewsMessageIfNeeded();
    return;
  }

  reviews.forEach((review) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${review.id}</td>
      <td>${escapeHtml(review.marketplace || "-")}</td>
      <td>${escapeHtml(review.product_id || "-")}</td>
      <td>${escapeHtml(review.external_review_id || "-")}</td>
      <td>${escapeHtml(review.author || "-")}</td>
      <td>${review.rating ?? "-"}</td>
      <td>${formatDate(review.review_date)}</td>
      <td>${escapeHtml(review.original_text)}</td>
      <td>${escapeHtml(review.processed_text)}</td>
      <td>
        <span class="sentiment-pill sentiment-${review.sentiment}">
          ${formatSentiment(review.sentiment)}
        </span>
      </td>
      <td>${Number(review.score).toFixed(2)}</td>
      <td>${formatDate(review.created_at)}</td>
      <td>
        <button
          class="delete-btn"
          type="button"
          data-id="${review.id}"
          title="Удалить отзыв"
          aria-label="Удалить отзыв ${review.id}"
        >
          ❌
        </button>
      </td>
    `;
    reviewsBody.appendChild(row);
  });
}

function renderEmptyReviewsMessageIfNeeded() {
  if (reviewsBody.children.length > 0) {
    return;
  }

  reviewsBody.innerHTML = `
    <tr>
      <td colspan="13">Отзывы пока не загружены.</td>
    </tr>
  `;
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

async function loadProblems() {
  const response = await fetch("/problems");
  const payload = await response.json();
  problemsBody.innerHTML = "";

  if (!payload.problems.length) {
    problemsBody.innerHTML = `
      <tr>
        <td colspan="3">Негативные аспекты пока не найдены.</td>
      </tr>
    `;
    return;
  }

  payload.problems.forEach((problem) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(formatAspect(problem.aspect))}</td>
      <td>${problem.count}</td>
      <td>${problem.percentage}%</td>
    `;
    problemsBody.appendChild(row);
  });
}

async function loadInsights() {
  const response = await fetch("/insights");
  const payload = await response.json();

  insightsSummary.textContent = payload.summary;
  riskLevel.textContent = riskLabels[payload.risk_level] || payload.risk_level;
  riskLevel.className = `risk-pill risk-${payload.risk_level}`;
  recommendationsList.innerHTML = "";

  payload.recommendations.forEach((recommendation) => {
    const item = document.createElement("li");
    item.textContent = recommendation;
    recommendationsList.appendChild(item);
  });
}

function formatAspect(value) {
  return aspectLabels[value] || value;
}

function formatSentiment(value) {
  return sentimentLabels[value] || value;
}

function formatApiError(message, fallback) {
  const translations = {
    "Only CSV files are supported.": "Поддерживаются только CSV-файлы.",
    'CSV must contain a "review" column.': 'CSV должен содержать колонку "review".',
    "CSV file is empty.": "CSV-файл пуст.",
    "Upload failed.": "Не удалось загрузить файл.",
    "Collection failed.": "Не удалось собрать отзывы.",
  };

  return translations[message] || message || fallback;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString("ru-RU");
}

loadDashboard();
