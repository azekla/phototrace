const processing = document.getElementById("processing");
if (processing) {
  const url = processing.dataset.statusUrl;
  const label = document.getElementById("processing-label");
  async function poll() {
    try {
      const response = await fetch(url, { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      if (data.done) { window.location.reload(); return; }
      label.textContent = `${data.state_text}. Страница обновится автоматически.`;
      window.setTimeout(poll, 2000);
    } catch {
      label.textContent = "Связь прервалась. Обновите страницу, чтобы узнать состояние проверки.";
    }
  }
  window.setTimeout(poll, 2000);
}

const privateButton = document.getElementById("show-private");
privateButton?.addEventListener("click", async () => {
  privateButton.disabled = true;
  try {
    const response = await fetch(privateButton.dataset.url, { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error();
    const data = await response.json();
    const list = document.getElementById("private-fields");
    for (const [key, value] of Object.entries(data.fields)) {
      const row = document.createElement("div");
      const term = document.createElement("dt");
      const detail = document.createElement("dd");
      term.textContent = key;
      detail.textContent = value;
      row.append(term, detail);
      list.append(row);
    }
    list.hidden = false;
    privateButton.remove();
  } catch {
    privateButton.textContent = "Не удалось загрузить поля. Повторить";
    privateButton.disabled = false;
  }
});
