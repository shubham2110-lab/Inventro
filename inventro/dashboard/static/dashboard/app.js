/* Global app bootstrap */
document.addEventListener("DOMContentLoaded", () => {
  bootstrapEnableTooltips();
  setupLogin();
  setupInventory();
  setupAddItem();
  setupAnalytics();
  // Check if we're on the dashboard page
  if (document.getElementById("inventoryTrendChart") || document.querySelector(".stat")) {
    setupDashboard();
  }
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

/* ---- Dashboard stats and charts ---- */
async function setupDashboard() {
  // Load dashboard stats
  await loadDashboardStats();
  // Load dashboard charts
  await setupDashboardCharts();
}

async function loadDashboardStats() {
  if (!window.InventroAPI) return;
  
  try {
    const stats = await InventroAPI.getStats();
    
    // Update stat boxes by ID (more reliable than title matching)
    const totalEl = document.getElementById('statTotalItems');
    if (totalEl) totalEl.textContent = stats.total_items.toLocaleString();
    
    const lowStockEl = document.getElementById('statLowStock');
    if (lowStockEl) lowStockEl.textContent = stats.low_stock.toLocaleString();
    
    const outOfStockEl = document.getElementById('statOutOfStock');
    if (outOfStockEl) outOfStockEl.textContent = stats.out_of_stock.toLocaleString();
    
    const valueEl = document.getElementById('statInventoryValue');
    if (valueEl) {
      const value = stats.inventory_value;
      if (value >= 1000) {
        valueEl.textContent = `$${(value / 1000).toFixed(1)}k`;
      } else {
        valueEl.textContent = `$${value.toFixed(0)}`;
      }
    }
    
    const newItemsEl = document.getElementById('statNewItems');
    if (newItemsEl) newItemsEl.textContent = stats.new_items_7d.toLocaleString();
    
    const vendorsEl = document.getElementById('statVendors');
    if (vendorsEl) vendorsEl.textContent = stats.categories.toLocaleString();
  } catch (e) {
    console.warn("Failed to load dashboard stats", e);
  }
}

async function setupDashboardCharts() {
  const elTrend = document.getElementById("inventoryTrendChart");
  const elCat = document.getElementById("itemsByCategoryChart");
  if (!elTrend && !elCat) return;
  
  if (!window.InventroAPI || !window.Chart) return;
  
  try {
    const m = await InventroAPI.getMetrics();
    
    if (elTrend) {
      // Destroy existing chart if it exists
      if (window.inventoryTrendChart) {
        window.inventoryTrendChart.destroy();
      }
      window.inventoryTrendChart = new Chart(elTrend, {
        type: "line",
        data: {
          labels: m.inventoryTrend.labels,
          datasets: [{ 
            label: "Total Items",
            data: m.inventoryTrend.data,
            fill: false,
            tension: 0.35
          }],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { 
            y: { beginAtZero: false, grid: { color: 'rgba(0,0,0,0.05)' } },
            x: { grid: { display: false } }
          },
        },
      });
    }
    
    if (elCat) {
      // Destroy existing chart if it exists
      if (window.itemsByCategoryChart) {
        window.itemsByCategoryChart.destroy();
      }
      window.itemsByCategoryChart = new Chart(elCat, {
        type: "bar",
        data: {
          labels: m.itemsByCategory.labels,
          datasets: [{ 
            label: "Items",
            data: m.itemsByCategory.data
          }],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { 
            y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
            x: { grid: { display: false } }
          },
        },
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
  
  if (!window.InventroAPI || !window.Chart) return;
  
  try {
    const m = await InventroAPI.getMetrics();
    
    if (elStatus) {
      // Destroy existing chart if it exists
      if (window.statusTrendsChart) {
        window.statusTrendsChart.destroy();
      }
      window.statusTrendsChart = new Chart(elStatus, {
        type: "line",
        data: {
          labels: m.statusTrends.labels,
          datasets: (m.statusTrends.series || []).map((s, idx) => ({
            label: s.label,
            data: s.data,
            tension: 0.3,
            borderColor: idx === 0 ? 'rgb(75, 192, 192)' : idx === 1 ? 'rgb(255, 206, 86)' : 'rgb(255, 99, 132)',
            backgroundColor: idx === 0 ? 'rgba(75, 192, 192, 0.1)' : idx === 1 ? 'rgba(255, 206, 86, 0.1)' : 'rgba(255, 99, 132, 0.1)',
          })),
        },
        options: {
          responsive: true,
          interaction: { mode: "nearest", intersect: false },
          plugins: {
            legend: { display: true, position: 'top' }
          },
          scales: {
            y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
            x: { grid: { display: false } }
          }
        },
      });
    }
    
    if (elValue) {
      // Destroy existing chart if it exists
      if (window.valueOverTimeChart) {
        window.valueOverTimeChart.destroy();
      }
      window.valueOverTimeChart = new Chart(elValue, {
        type: "line",
        data: {
          labels: m.valueOverTime.labels,
          datasets: [
            {
              label: "Inventory Value",
              data: m.valueOverTime.data,
              fill: true,
              borderColor: 'rgb(75, 192, 192)',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              tension: 0.4,
            },
          ],
        },
        options: { 
          responsive: true, 
          plugins: { legend: { display: false } },
          scales: {
            y: { 
              beginAtZero: false,
              grid: { color: 'rgba(0,0,0,0.05)' },
              ticks: {
                callback: function(value) {
                  if (value >= 1000) {
                    return '$' + (value / 1000).toFixed(1) + 'k';
                  }
                  return '$' + value.toFixed(0);
                }
              }
            },
            x: { grid: { display: false } }
          }
        },
      });
    }
  } catch (e) {
    console.warn("Analytics metrics fallback in use", e);
  }
}

