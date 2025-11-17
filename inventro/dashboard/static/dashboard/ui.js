/**
 * Inventro UI helpers
 */
(function (window) {
  function toast(message, type = "info", timeout = 3000) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container position-fixed top-0 end-0 p-3";
      document.body.appendChild(container);
    }
    const el = document.createElement("div");
    el.className = `toast align-items-center text-bg-${type} border-0 show mb-2`;
    el.setAttribute("role", "alert");
    el.innerHTML = `<div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" aria-label="Close"></button></div>`;
    container.appendChild(el);
    el.querySelector("button").addEventListener("click", () => el.remove());
    if (timeout) setTimeout(() => el.remove(), timeout);
  }

  function formToJSON(form) {
    const data = {};
    new FormData(form).forEach((v, k) => {
      if (v === "") return;
      // Try numeric fields
      if (["quantity", "min_quantity", "price"].includes(k)) {
        const num = Number(v);
        data[k] = isNaN(num) ? v : num;
      } else {
        data[k] = v;
      }
    });
    return data;
  }

  function formatMoney(n) {
    if (n == null || isNaN(n)) return "$0.00";
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: "USD",
    }).format(Number(n));
  }

  function renderInventoryRows(items) {
    return items
      .map((item) => {
        const qty = Number(item.quantity || 0);
        const minq = Number(item.min_quantity || 0);
        const status = qty <= 0 ? "danger" : qty < minq ? "warning" : "success";
        const statusLabel =
          qty <= 0 ? "Out of Stock" : qty < minq ? "Low Stock" : "In Stock";
        return `
        <tr data-id="${item.id || ""}">
          <td>${item.sku || ""}</td>
          <td>${item.name || ""}</td>
          <td>${item.category || ""}</td>
          <td>${item.location || ""}</td>
          <td>${qty} / ${minq}</td>
          <td>${formatMoney(item.price)}</td>
          <td><span class="chip chip-${status}">${statusLabel}</span></td>
          <td>${
            item.updated_at
              ? new Date(item.updated_at).toLocaleDateString()
              : ""
          }</td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-primary js-edit"><i class="bi bi-pencil-square"></i></button>
            <button class="btn btn-sm btn-outline-danger js-delete"><i class="bi bi-trash"></i></button>
          </td>
        </tr>`;
      })
      .join("");
  }

  function renderPagination(container, page, pageSize, total, onPage) {
    if (!container) return;
    const pages = Math.max(1, Math.ceil(total / pageSize));
    const prev = Math.max(1, page - 1);
    const next = Math.min(pages, page + 1);
    container.innerHTML = `
      <nav aria-label="Inventory pagination">
        <ul class="pagination justify-content-end mb-0">
          <li class="page-item ${
            page === 1 ? "disabled" : ""
          }"><a class="page-link" href="#" data-page="${prev}">Previous</a></li>
          ${Array.from({ length: pages })
            .map((_, i) => {
              const p = i + 1;
              return `<li class="page-item ${
                p === page ? "active" : ""
              }"><a class="page-link" href="#" data-page="${p}">${p}</a></li>`;
            })
            .join("")}
          <li class="page-item ${
            page === pages ? "disabled" : ""
          }"><a class="page-link" href="#" data-page="${next}">Next</a></li>
        </ul>
      </nav>`;
    container.querySelectorAll("a.page-link").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const p = Number(a.dataset.page);
        if (onPage) onPage(p);
      });
    });
  }

  window.InventroUI = {
    toast,
    formToJSON,
    renderInventoryRows,
    renderPagination,
    formatMoney,
  };
})(window);

