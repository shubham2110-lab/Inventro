// Dashboard charts (placeholder data)
(function () {
  const trendEl = document.getElementById('inventoryTrendChart');
  if (trendEl) {
    new Chart(trendEl, {
      type: 'line',
      data: {
        labels: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct'],
        datasets: [{
          label: 'Total Items',
          data: [980,1020,1040,1030,1080,1100,1125,1160,1210,1284],
          fill: false,
          tension: 0.35
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: false, grid: { color: 'rgba(0,0,0,0.05)' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  const catEl = document.getElementById('itemsByCategoryChart');
  if (catEl) {
    new Chart(catEl, {
      type: 'bar',
      data: {
        labels: ['Electronics','Apparel','Office','Food','Other'],
        datasets: [{
          label: 'Items',
          data: [420, 260, 190, 140, 274]
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
          x: { grid: { display: false } }
        }
      }
    });
  }
})();
