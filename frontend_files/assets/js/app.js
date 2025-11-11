/* Dashboard charts */
const elTrend = document.getElementById('inventoryTrend');
if (elTrend) {
  new Chart(elTrend, {
    type: 'bar',
    data: {
      labels: ['Jan','Feb','Mar','Apr','May'],
      datasets: [{ label: 'Items', data: [1080,1120,1200,1150,1230] }]
    },
    options: { responsive: true, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}} }
  });
}

const elCat = document.getElementById('itemsByCategory');
if (elCat) {
  new Chart(elCat, {
    type: 'pie',
    data: {
      labels: ['Electronics 36%','Furniture 26%','Accessories 22%','Office 16%'],
      datasets: [{ data: [36,26,22,16] }]
    },
    options: { responsive: true }
  });
}
