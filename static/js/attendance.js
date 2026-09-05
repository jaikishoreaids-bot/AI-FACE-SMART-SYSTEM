/**
 * AI Face Recognition Attendance Management System - Attendance Table Controller
 */

class AttendanceTableController {
  constructor() {
    this.tableBody = document.getElementById('attendanceTableBody');
    this.paginationElem = document.getElementById('attendancePagination');
    this.totalRecordsElem = document.getElementById('attendanceTotalRecords');
    
    this.dateInput = document.getElementById('filterDate');
    this.deptSelect = document.getElementById('filterDepartment');
    this.statusSelect = document.getElementById('filterStatus');
    this.searchInput = document.getElementById('searchQuery');
    
    this.csvExportBtn = document.getElementById('exportCsvBtn');
    this.excelExportBtn = document.getElementById('exportExcelBtn');
    
    this.currentPage = 1;
    this.perPage = 15;

    this.initEvents();
    this.loadData();
  }

  initEvents() {
    if (this.dateInput) this.dateInput.addEventListener('change', () => { this.currentPage = 1; this.loadData(); });
    if (this.deptSelect) this.deptSelect.addEventListener('change', () => { this.currentPage = 1; this.loadData(); });
    if (this.statusSelect) this.statusSelect.addEventListener('change', () => { this.currentPage = 1; this.loadData(); });
    
    if (this.searchInput) {
      let debounce = null;
      this.searchInput.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(() => { this.currentPage = 1; this.loadData(); }, 300);
      });
    }

    if (this.csvExportBtn) {
      this.csvExportBtn.addEventListener('click', () => this.handleExport('csv'));
    }
    if (this.excelExportBtn) {
      this.excelExportBtn.addEventListener('click', () => this.handleExport('excel'));
    }
  }

  async loadData() {
    if (!this.tableBody) return;

    this.tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4"><span class="spinner-border spinner-border-sm me-2 text-primary"></span> Loading records...</td></tr>`;

    const params = new URLSearchParams({
      page: this.currentPage,
      per_page: this.perPage,
      date: this.dateInput ? this.dateInput.value : '',
      department: this.deptSelect ? this.deptSelect.value : 'ALL',
      status: this.statusSelect ? this.statusSelect.value : 'ALL',
      search: this.searchInput ? this.searchInput.value : ''
    });

    try {
      const res = await apiFetch(`/api/attendance/list?${params.toString()}`);
      this.renderTable(res.records);
      this.renderPagination(res.pages, res.current_page);
      if (this.totalRecordsElem) this.totalRecordsElem.textContent = res.total;
    } catch (e) {
      this.tableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Failed to load attendance records: ${e.message}</td></tr>`;
    }
  }

  renderTable(records) {
    if (!records || records.length === 0) {
      this.tableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-5 text-muted">
            <i class="bi bi-inbox fs-2 mb-2 d-block opacity-50"></i>
            No attendance records found matching filters.
          </td>
        </tr>`;
      return;
    }

    this.tableBody.innerHTML = records.map(r => `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="user-avatar" style="width: 32px; height: 32px; font-size: 12px;">${r.student_name.charAt(0)}</div>
            <div>
              <a href="/student/${r.student_id}" class="fw-bold text-light">${r.student_name}</a>
              <div class="text-muted" style="font-size: 11px;">ID: ${r.student_id}</div>
            </div>
          </div>
        </td>
        <td><span class="text-muted">${r.department}</span></td>
        <td>${r.attendance_date}</td>
        <td><span class="font-monospace text-primary">${r.attendance_time}</span></td>
        <td>
          <span class="badge-tech-${r.status === 'Present' ? 'present' : (r.status === 'Late' ? 'late' : 'absent')}">
            ${r.status}
          </span>
        </td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="progress flex-grow-1" style="height: 6px; background: rgba(255,255,255,0.05); width: 60px;">
              <div class="progress-bar bg-info" style="width: ${r.confidence}%"></div>
            </div>
            <small class="text-muted">${r.confidence}%</small>
          </div>
        </td>
        <td><span class="badge bg-dark border border-secondary">${r.verification_method}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-danger p-1 px-2" title="Delete Record" onclick="window.attendanceCtrl.deleteRecord(${r.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `).join('');
  }

  renderPagination(totalPages, currentPage) {
    if (!this.paginationElem) return;
    if (totalPages <= 1) {
      this.paginationElem.innerHTML = '';
      return;
    }

    let html = '';
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
      <button class="page-link bg-dark text-light border-secondary" onclick="window.attendanceCtrl.goToPage(${currentPage - 1})">&laquo;</button>
    </li>`;

    for (let p = 1; p <= totalPages; p++) {
      if (p === 1 || p === totalPages || (p >= currentPage - 2 && p <= currentPage + 2)) {
        html += `<li class="page-item ${p === currentPage ? 'active' : ''}">
          <button class="page-link ${p === currentPage ? 'btn-tech-primary' : 'bg-dark text-light border-secondary'}" onclick="window.attendanceCtrl.goToPage(${p})">${p}</button>
        </li>`;
      }
    }

    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
      <button class="page-link bg-dark text-light border-secondary" onclick="window.attendanceCtrl.goToPage(${currentPage + 1})">&raquo;</button>
    </li>`;

    this.paginationElem.innerHTML = html;
  }

  goToPage(page) {
    this.currentPage = page;
    this.loadData();
  }

  async deleteRecord(recordId) {
    if (!confirm('Are you sure you want to delete this attendance record?')) return;
    try {
      await apiFetch(`/api/attendance/delete/${recordId}`, { method: 'POST' });
      showToast('Attendance record deleted.', 'success');
      this.loadData();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  }

  handleExport(type) {
    const params = new URLSearchParams({
      date: this.dateInput ? this.dateInput.value : '',
      department: this.deptSelect ? this.deptSelect.value : 'ALL'
    });
    window.location.href = `/api/attendance/export/${type}?${params.toString()}`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('attendanceTableBody')) {
    window.attendanceCtrl = new AttendanceTableController();
  }
});
