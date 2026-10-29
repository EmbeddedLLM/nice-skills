"use strict";

const themes = JSON.parse(document.getElementById("theme-data").textContent);
const themeSelect = document.getElementById("theme");
const storageKey = "nice-skills-theme";

function applyTheme(slug) {
  const theme = themes.find((item) => item.slug === slug) || themes.find((item) => item.slug === "lavender");
  document.documentElement.dataset.palette = theme.slug;
  themeSelect.value = theme.slug;
  for (const role of ["primary", "secondary", "accent"]) {
    document.getElementById(`${role}-hex`).textContent = theme.colors[role];
  }
}

let savedTheme;
try {
  savedTheme = localStorage.getItem(storageKey);
} catch {
  // Theme switching still works when the browser blocks persistent storage.
}
applyTheme(savedTheme);
document.querySelector(".theme-control").hidden = false;
themeSelect.addEventListener("change", () => {
  applyTheme(themeSelect.value);
  try {
    localStorage.setItem(storageKey, themeSelect.value);
  } catch {
    // Browsing in a storage-restricted context does not disable the picker.
  }
});

const search = document.getElementById("search");
const category = document.getElementById("category");
const skills = [...document.querySelectorAll(".skill")];
const searchableSkills = skills.map((element) => ({ element, text: element.textContent.toLowerCase() }));

function filterSkills() {
  const query = search.value.trim().toLowerCase();
  let count = 0;
  for (const { element, text } of searchableSkills) {
    const visible = text.includes(query) && (!category.value || element.dataset.group === category.value);
    element.hidden = !visible;
    if (visible) count += 1;
  }
  document.getElementById("result-count").textContent = `${count} ${count === 1 ? "skill" : "skills"}`;
  document.getElementById("empty").hidden = count !== 0;
}

document.querySelector(".filters").hidden = false;
search.addEventListener("input", filterSkills);
category.addEventListener("change", filterSkills);
document.getElementById("reset").addEventListener("click", () => {
  search.value = "";
  category.value = "";
  filterSkills();
  search.focus();
});
