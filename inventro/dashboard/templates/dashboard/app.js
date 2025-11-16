/* Global app bootstrap */
document.addEventListener("DOMContentLoaded", () => {
  bootstrapEnableTooltips();
  setupLogin();
  setupInventory();
  setupAddItem();
  setupAnalytics();
  setupDashboardCharts();
});

function bootstrapEnableTooltips() {
  if (!window.bootstrap) return;
  document
    .querySelectorAll('[data-bs-toggle="tooltip"]')
    .forEach((el) => new bootstrap.Tooltip(el));
}

/* ---- Login page ---- */
function setupLogin() {
  const form = document.querySelector(
    'form[action="index.html"], form#loginForm'
  );
  if (!form || !window.InventroAPI) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = form.querySelector('input[type="email"]').value.trim();
    const password = form.querySelector('input[type="password"]').value;
    try {
      await InventroAPI.login(email, password);
      InventroUI.toast("Signed in successfully", "success");
      window.location.href = "index.html";
    } catch (err) {
      InventroUI.toast("Login failed. Check credentials.", "danger", 5000);
      console.error(err);
    }
  });
}

/* ---- Inventory page ---- */
async function setupInventory() {
  const tableBody = document.getElementById("tableBody");
  if (!tableBody || !window.InventroAPI) return;

  const searchInput = document.getElementById("q");
  const pagination = document.createElement("div");
  pagination.id = "inventoryPagination";
  pagination.className = "mt-2";
  tableBody.parentElement.parentElement.appendChild(pagination);

  let state = { page: 1, page_size: 10, ordering: "name", q: "" };

  async function load() {
    try {
      const res = await InventroAPI.getItems(state);
      const items = Array.isArray(res.results)
        ? res.results
        : Array.isArray(res)
        ? res
        : res.items || [];
      const total = res.count ?? items.length;
      tableBody.innerHTML = InventroUI.renderInventoryRows(items);
      bindRowActions();
      InventroUI.renderPagination(
        pagination,
        state.page,
        state.page_size,
        total,
        (p) => {
          state.page = p;
          load();
        }
      );
    } catch (err) {
      console.warn("Falling back to static sample rows due to API error", err);
      InventroUI.toast("Using demo data (API not reachable)", "warning", 4000);
    }
  }

  function bindRowActions() {
    document.querySelectorAll(".js-delete").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const tr = e.currentTarget.closest("tr");
        const id = tr?.dataset.id;
        if (!id) {
          tr.remove();
          return;
        }
        if (!confirm("Delete this item?")) return;
        try {
          await InventroAPI.deleteItem(id);
          tr.remove();
          InventroUI.toast("Item deleted", "success");
        } catch (err) {
          InventroUI.toast("Delete failed", "danger");
        }
      });
    });
    document.querySelectorAll(".js-edit").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const tr = e.currentTarget.closest("tr");
        const id = tr?.dataset.id;
        const sku = tr.children[0].textContent.trim();
        const name = tr.children[1].textContent.trim();
        const url = new URL("add-item.html", window.location.href);
        if (id) url.searchParams.set("id", id);
        url.searchParams.set("sku", sku);
        url.searchParams.set("name", name);
        window.location.href = url.toString();
      });
    });
  }

  // search
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      state.q = e.target.value.trim();
      state.page = 1;
      load();
    });
  }

  // column sort (simple demo: click header with ⇅)
  const sortableHeader = document.querySelector("th:nth-child(2)");
  if (sortableHeader) {
    sortableHeader.style.cursor = "pointer";
    sortableHeader.title = "Sort by name";
    sortableHeader.addEventListener("click", () => {
      state.ordering = state.ordering === "name" ? "-name" : "name";
      load();
    });
  }

  await load();
}

/* ---- Add item page ---- */
function setupAddItem() {
  const form =
    document.querySelector("form.add-item-form") ||
    document.querySelector("form.row");
  const isAddItemPage = document.title.toLowerCase().includes("add item");
  if (!form || !isAddItemPage || !window.InventroAPI) return;

  // Prefill if redirected from edit
  const url = new URL(window.location.href);
  const id = url.searchParams.get("id");
  const sku = url.searchParams.get("sku");
  const name = url.searchParams.get("name");
  if (sku) form.querySelector('input[placeholder="ELEC-WM-001"]').value = sku;
  if (name)
    form.querySelector('input[placeholder="Wireless Mouse"]').value = name;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = InventroUI.formToJSON(form);
    // light validation
    const required = [
      "Item Name *",
      "SKU *",
      "Category *",
      "Location *",
      "Quantity *",
      "Minimum Quantity *",
      "Price ($) *",
    ];
    const empties = Array.from(
      form.querySelectorAll("input,select,textarea")
    ).filter((el) => el.hasAttribute("required") && !el.value.trim());
    if (empties.length) {
      InventroUI.toast("Please fill all required fields", "warning");
      empties[0].focus();
      return;
    }
    try {
      if (id) {
        await InventroAPI.patchItem(id, payload);
        InventroUI.toast("Item updated", "success");
      } else {
        await InventroAPI.createItem(payload);
        InventroUI.toast("Item created", "success");
      }
      setTimeout(() => (window.location.href = "inventory.html"), 600);
    } catch (err) {
      InventroUI.toast("Save failed. Check API and payload.", "danger", 5000);
      console.error(err);
    }
  });
}

/* ---- Dashboard & Analytics charts ---- */
async function setupDashboardCharts() {
  const elTrend = document.getElementById("inventoryTrend");
  const elCat = document.getElementById("itemsByCategory");
  if (!elTrend && !elCat) return;
  try {
    const m = await InventroAPI.getMetrics();
    if (elTrend && window.Chart) {
      new Chart(elTrend, {
        type: "bar",
        data: {
          labels: m.inventoryTrend.labels,
          datasets: [{ label: "Items", data: m.inventoryTrend.data }],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } },
        },
      });
    }
    if (elCat && window.Chart) {
      new Chart(elCat, {
        type: "pie",
        data: {
          labels: m.itemsByCategory.labels,
          datasets: [{ data: m.itemsByCategory.data }],
        },
        options: { responsive: true },
      });
    }
  } catch (e) {
    console.warn("Dashboard metrics fallback in use", e);
  }
}

async function setupAnalytics() {
  const elStatus = document.getElementById("statusTrends");
  const elValue = document.getElementById("valueOverTime");
  if (!elStatus && !elValue) return;
  try {
    const m = await InventroAPI.getMetrics();
    if (elStatus && window.Chart) {
      new Chart(elStatus, {
        type: "line",
        data: {
          labels: m.statusTrends.labels,
          datasets: (m.statusTrends.series || []).map((s) => ({
            label: s.label,
            data: s.data,
            tension: 0.3,
          })),
        },
        options: {
          responsive: true,
          interaction: { mode: "nearest", intersect: false },
        },
      });
    }
    if (elValue && window.Chart) {
      new Chart(elValue, {
        type: "line",
        data: {
          labels: m.valueOverTime.labels,
          datasets: [
            {
              label: "Inventory Value",
              data: m.valueOverTime.data,
              fill: true,
            },
          ],
        },
        options: { responsive: true, plugins: { legend: { display: false } } },
      });
    }
  } catch (e) {
    console.warn("Analytics metrics fallback in use", e);
  }
}
