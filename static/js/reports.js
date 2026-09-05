/**
 * AI Face Recognition Attendance Management System - Reports & Analytics Controller
 */

let trendChart = null;
let deptReportChart = null;

class ReportsController {
  constructor() {
    this.periodSelect = document.getElementById('reportPeriod');
    this.deptSelect = document.getElementById('reportDepartment');
    this.studentsTable = document.getElementById('reportStudentsTable');
    
    this.initEvents();
    this.fetchAndRender();
  }

  initEvents() {
    if (this.periodSelect) this.periodSelect.addEventListener('change', () => this.fetchAndRender());
    if (this.deptSelect) this.deptSelect.addEventListener('change', () => this.fetchAndRender());
  }

  async fetchAndRender() {
    const period = this.periodSelect ? this.periodSelect.value : '7days';
    const dept = this.deptSelect ? this.deptSelect.value : 'ALL';

    try {
      const res = await apiFetch(`/api/reports/analytics?period=${period}&department=${dept}`);
      this.renderTrends(res.trends);
      this.renderDepartmentChart(res.departments);
      this.renderStudentsTable(res.students_table);
      
      // Update top badges
      const avgRateElem = document.getElementById('reportAvgRate');
      if (avgRateElem) avgRateElem.textContent = `${res.avg_attendance_rate}%`;

      const totalStuElem = document.getElementById('reportTotalStudents');
      if (totalStuElem) totalStuElem.textContent = res.total_students;
    } catch (err) {
      showToast('Failed to load reports: ' + err.message, 'danger');
    }
  }

  renderTrends(trends) {
    const ctx = document.getElementById('reportTrendChart');
    if (!ctx) return;

    if (trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: trends.labels,
        datasets: [
          {
            label: 'Present Students',
            data: trends.present,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: '#10b981'
          },
          {
            label: 'Absent Students',
            data: trends.absent,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.05)',
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            tension: 0.35,
            pointRadius: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#cbd5e1', font: { size: 12 } } },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8' }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8', stepSize: 1 }
          }
        }
      }
    });
  }

  renderDepartmentChart(depts) {
    const ctx = document.getElementById('reportDeptChart');
    if (!ctx) return;

    if (deptReportChart) deptReportChart.destroy();

    deptReportChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: depts.labels.length > 0 ? depts.labels : ['No Data'],
        datasets: [{
          label: 'Total Present Logs',
          data: depts.counts.length > 0 ? depts.counts : [0],
          backgroundColor: 'rgba(99, 102, 241, 0.65)',
          borderColor: '#6366f1',
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
            ticks: { color: '#94a3b8' }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8', stepSize: 1 }
          }
        }
      }
    });
  }

  renderStudentsTable(students) {
    if (!this.studentsTable) return;

    if (!students || students.length === 0) {
      this.studentsTable.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No students found for this period.</td></tr>`;
      return;
    }

    this.studentsTable.innerHTML = students.map(s => {
      let badgeClass = 'badge-tech-present';
      if (s.attendance_rate < 75) badgeClass = 'badge-tech-absent';
      else if (s.attendance_rate < 85) badgeClass = 'badge-tech-late';

      return `
        <tr>
          <td>
            <a href="/student/${s.student_id}" class="fw-bold text-light">${s.name}</a>
            <div class="text-muted" style="font-size: 11px;">ID: ${s.student_id}</div>
          </td>
          <td>${s.department}</td>
          <td>${s.year} - ${s.section}</td>
          <td><strong class="text-light">${s.present_days}</strong> / ${s.total_days} days</td>
          <td>
            <div class="d-flex align-items-center gap-2">
              <div class="progress flex-grow-1" style="height: 6px; background: rgba(255,255,255,0.05); width: 80px;">
                <div class="progress-bar ${s.attendance_rate >= 75 ? 'bg-success' : 'bg-danger'}" style="width: ${s.attendance_rate}%"></div>
              </div>
              <span class="${badgeClass}">${s.attendance_rate}%</span>
            </div>
          </td>
          <td>
            <a href="/student/${s.student_id}" class="btn btn-sm btn-outline-info p-1 px-2" title="View Profile">
              <i class="bi bi-eye me-1"></i> Profile
            </a>
          </td>
        </tr>
      `;
    }).join('');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('reportTrendChart')) {
    window.reportsCtrl = new ReportsController();
  }
});
