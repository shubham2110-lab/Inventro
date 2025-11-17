/**
 * Inventro API client (Phase 2 frontend)
 * - Centralizes auth token handling, base URL, fetch wrappers, and common endpoints.
 * - Designed to plug directly into a Django backend (DRF) with JWT/session tokens.
 * - Set API base at runtime with: localStorage.setItem('API_BASE', 'https://your-domain/api');
 */
(function (window) {
  const DEFAULT_BASE = (
    window.INVENTRO_API_BASE ||
    localStorage.getItem("API_BASE") ||
    "http://localhost:8000"
  ).replace(/\/+$/, "");

  const state = {
    baseUrl: DEFAULT_BASE,
    get token() {
      return localStorage.getItem("AUTH_TOKEN") || "";
    },
    set token(v) {
      localStorage.setItem("AUTH_TOKEN", v || "");
    },
  };

  function headers(extra) {
    const h = Object.assign(
      { "Content-Type": "application/json" },
      extra || {}
    );
    if (state.token) h["Authorization"] = `Bearer ${state.token}`;
    return h;
  }

  async function apiFetch(path, options = {}) {
    const url = path.startsWith("http")
      ? path
      : `${state.baseUrl}${path.startsWith("/") ? "" : "/"}${path}`;
    const res = await fetch(url, {
      credentials: "include",
      ...options,
      headers: headers(options.headers),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      const error = new Error(`API ${res.status}: ${text || res.statusText}`);
      error.status = res.status;
      try {
        error.data = JSON.parse(text);
      } catch {}
      throw error;
    }
    const contentType = res.headers.get("content-type") || "";
    return contentType.includes("application/json") ? res.json() : res.text();
  }

  // --- Auth ---
  async function login(email, password) {
    // Supports DRF JWT (/api/auth/login/) or custom /api/login
    try {
      const data = await apiFetch("/api/auth/login/", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (data && (data.access || data.token))
        state.token = data.access || data.token;
      return data;
    } catch (e) {
      // fallback to /api/login
      const data = await apiFetch("/api/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (data && (data.access || data.token))
        state.token = data.access || data.token;
      return data;
    }
  }

  function logout() {
    state.token = "";
  }

  // --- Inventory ---
  function buildQuery(obj) {
    const p = new URLSearchParams();
    Object.entries(obj || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") p.append(k, v);
    });
    const qs = p.toString();
    return qs ? `?${qs}` : "";
  }

  async function getItems(params = {}) {
    return apiFetch(`/api/items/${buildQuery(params)}`);
  }

  async function getItem(id) {
    return apiFetch(`/api/items/${id}/`);
  }

  async function createItem(payload) {
    return apiFetch("/api/items/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async function updateItem(id, payload) {
    return apiFetch(`/api/items/${id}/`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }

  async function patchItem(id, payload) {
    return apiFetch(`/api/items/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  async function deleteItem(id) {
    return apiFetch(`/api/items/${id}/`, { method: "DELETE" });
  }

  // --- Dashboard Stats ---
  async function getStats() {
    try {
      return await apiFetch("/api/stats/");
    } catch (e) {
      console.warn("Stats API error, using fallback", e);
      return {
        total_items: 0,
        low_stock: 0,
        out_of_stock: 0,
        inventory_value: 0,
        new_items_7d: 0,
        categories: 0,
      };
    }
  }

  // --- Metrics (Analytics) ---
  async function getMetrics() {
    // Expect backend to provide computed metrics
    // Fallback: return placeholders the charts can use
    try {
      return await apiFetch("/api/metrics/");
    } catch (e) {
      console.warn("Metrics API error, using fallback", e);
      return {
        inventoryTrend: {
          labels: ["Jan", "Feb", "Mar", "Apr", "May"],
          data: [1080, 1120, 1200, 1150, 1230],
        },
        itemsByCategory: {
          labels: [
            "Electronics 36%",
            "Furniture 26%",
            "Accessories 22%",
            "Office 16%",
          ],
          data: [36, 26, 22, 16],
        },
        statusTrends: {
          labels: ["Week 1", "Week 2", "Week 3", "Week 4"],
          series: [
            { label: "In Stock", data: [1180, 1180, 1190, 1210] },
            { label: "Low Stock", data: [18, 18, 19, 20] },
            { label: "Out of Stock", data: [4, 4, 3, 5] },
          ],
        },
        valueOverTime: {
          labels: ["Jan", "Feb", "Mar", "Apr", "May"],
          data: [235000, 242000, 255000, 252000, 268000],
        },
      };
    }
  }

  window.InventroAPI = {
    state,
    apiFetch,
    login,
    logout,
    getItems,
    getItem,
    createItem,
    updateItem,
    patchItem,
    deleteItem,
    getStats,
    getMetrics,
  };
})(window);

