/**
 * TaskFlow — Reports Page Charts (Chart.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Task Status Distribution (Donut Chart)
  const statusCtx = document.getElementById('statusDonut');
  if (statusCtx && typeof statusData !== 'undefined') {
    new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: ['Completed', 'Pending', 'Overdue'],
        datasets: [{
          data: [statusData.completed, statusData.pending, statusData.overdue || 0],
          backgroundColor: ['#16A34A', '#D97706', '#DC2626'],
          borderWidth: 0,
          hoverOffset: 4
        }]
      },
      options: {
        cutout: '74%',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.parsed} tasks`
            }
          }
        },
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }

  // 2. Tasks by Priority (Bar Chart)
  const priorityCtx = document.getElementById('priorityBar');
  if (priorityCtx && typeof priorityData !== 'undefined') {
    new Chart(priorityCtx, {
      type: 'bar',
      data: {
        labels: ['High', 'Medium', 'Low'],
        datasets: [{
          label: 'Tasks',
          data: [priorityData.high, priorityData.medium, priorityData.low],
          backgroundColor: ['#DC2626', '#F59E0B', '#10B981'],
          borderRadius: 6,
          barThickness: 36
        }]
      },
      options: {
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.y} tasks`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1 },
            grid: { color: '#F1F5F9' }
          },
          x: {
            grid: { display: false }
          }
        },
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }

  // 3. Weekly Activity (Line Chart)
  const weekCtx = document.getElementById('weekLine');
  if (weekCtx && typeof weekLabels !== 'undefined' && typeof weekCounts !== 'undefined') {
    new Chart(weekCtx, {
      type: 'line',
      data: {
        labels: weekLabels,
        datasets: [{
          label: 'Tasks Created',
          data: weekCounts,
          borderColor: '#4F46E5',
          backgroundColor: 'rgba(79, 70, 229, 0.08)',
          borderWidth: 2.5,
          tension: 0.35,
          fill: true,
          pointBackgroundColor: '#4F46E5',
          pointBorderColor: '#FFFFFF',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.y} created`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1 },
            grid: { color: '#F1F5F9' }
          },
          x: {
            grid: { display: false }
          }
        },
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }
});
