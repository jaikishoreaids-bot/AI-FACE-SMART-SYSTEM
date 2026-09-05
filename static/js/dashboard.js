/**
 * AI Face Recognition Attendance Management System - Dashboard Analytics JS
 */

let deptChart = null;
let statusDonutChart = null;

function initDashboardCharts(summary) {
  // 1. Department Breakdown Bar Chart
  const deptCtx = document.getElementById('deptAttendanceChart');
  if (deptCtx) {
    const labels = Object.keys(summary.department_breakdown || {});
    const values = Object.values(summary.department_breakdown || {});

    deptChart = new Chart(deptCtx, {
      type: 'bar',
      data: {
        labels: labels.length > 0 ? labels : ['No Data'],
        datasets: [{
          label: 'Students Present Today',
          data: values.length > 0 ? values : [0],
          backgroundColor: 'rgba(6, 182, 212, 0.65)',
          borderColor: '#06b6d4',
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8', font: { size: 11 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8', stepSize: 1, font: { size: 11 } }
          }
        }
      }
    });
  }

  // 2. Present vs Absent Ratio Donut Chart
  const statusCtx = document.getElementById('statusDonutChart');
  if (statusCtx) {
    statusDonutChart = new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: ['Present', 'Late', 'Absent'],
        datasets: [{
          data: [summary.present_count - summary.late_count, summary.late_count, summary.absent_count],
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
          borderWidth: 0,
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#cbd5e1', font: { size: 12 }, padding: 16 }
          }
        },
        cutout: '72%'
      }
    });
  }
}

// Auto-refresh Dashboard Stats every 15 seconds
async function refreshDashboardStats() {
  try {
    const res = await apiFetch('/api/dashboard/stats');
    if (res) {
      document.getElementById('dashTotalStudents').textContent = res.total_students;
      document.getElementById('dashPresentToday').textContent = res.present_count;
      document.getElementById('dashAbsentToday').textContent = res.absent_count;
      document.getElementById('dashAttendanceRate').textContent = `${res.attendance_rate}%`;

      // Update charts
      if (deptChart) {
        deptChart.data.labels = Object.keys(res.department_breakdown);
        deptChart.data.datasets[0].data = Object.values(res.department_breakdown);
        deptChart.update();
      }

      if (statusDonutChart) {
        statusDonutChart.data.datasets[0].data = [
          res.present_count - res.late_count,
          res.late_count,
          res.absent_count
        ];
        statusDonutChart.update();
      }
    }
  } catch (e) {
    console.debug('Dashboard background refresh error:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (window.INITIAL_SUMMARY) {
    initDashboardCharts(window.INITIAL_SUMMARY);
    setInterval(refreshDashboardStats, 15000);
  }
});
