const input = document.getElementById("image-input");
const dropZone = document.getElementById("drop-zone");
const selected = document.getElementById("file-selected");
const form = document.getElementById("upload-form");
const submitButton = document.getElementById("submit-button");

function showFile(file) {
  if (!file) return;
  selected.hidden = false;
  selected.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} МБ`;
}

input?.addEventListener("change", () => showFile(input.files[0]));
dropZone?.addEventListener("dragover", event => { event.preventDefault(); dropZone.classList.add("dragover"); });
dropZone?.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone?.addEventListener("drop", event => {
  event.preventDefault();
  dropZone.classList.remove("dragover");
  if (event.dataTransfer.files.length) {
    input.files = event.dataTransfer.files;
    showFile(input.files[0]);
  }
});
form?.addEventListener("submit", () => {
  submitButton.disabled = true;
  submitButton.textContent = "Загрузка…";
});
