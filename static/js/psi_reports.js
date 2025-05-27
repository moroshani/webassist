// psi_reports.js
// All JavaScript for PSI Reports List page

document.addEventListener('DOMContentLoaded', function() {
    // Search filter
    const searchInput = document.getElementById('reportSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('.reports-table tbody tr');
            rows.forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(filter) ? '' : 'none';
            });
        });
    }

    // Sorting (simple, by clicking headers)
    document.querySelectorAll('.reports-table th').forEach((th, idx) => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', function() {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr')).filter(r => r.querySelector('td'));
            const asc = th.classList.toggle('asc');
            rows.sort((a, b) => {
                let aText = a.children[idx].textContent.trim();
                let bText = b.children[idx].textContent.trim();
                if (!isNaN(parseFloat(aText)) && !isNaN(parseFloat(bText))) {
                    aText = parseFloat(aText);
                    bText = parseFloat(bText);
                }
                return asc ? (aText > bText ? 1 : -1) : (aText < bText ? 1 : -1);
            });
            rows.forEach(row => tbody.appendChild(row));
        });
    });

    // Delete report
    document.querySelectorAll('.reports-table').forEach(function(table) {
        table.addEventListener('click', function(e) {
            if (e.target.closest('.delete-report-btn')) {
                const btn = e.target.closest('.delete-report-btn');
                showConfirm('Are you sure you want to delete this report?', () => {
                    const reportId = btn.getAttribute('data-report-id');
                    showLoading();
                    fetch(`/reports/${reportId}/delete/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            btn.closest('tr').remove();
                            showToast('Report deleted.', 'success');
                        } else {
                            showToast(data.message || 'Failed to delete report.', 'danger');
                        }
                    })
                    .catch(() => showToast('Failed to delete report.', 'danger'))
                    .finally(() => hideLoading());
                });
            }
        });
    });

    // Export CSV
    const exportReportsCsvBtn = document.getElementById('exportReportsCsvBtn');
    if (exportReportsCsvBtn) {
        exportReportsCsvBtn.addEventListener('click', function() {
            showLoading();
            window.location.href = window.location.pathname + 'export/csv/';
            setTimeout(hideLoading, 1000);
        });
    }

    // Date range filter
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const reportsTableRows = document.querySelectorAll('.reports-table tbody tr');
    function filterByDate() {
        const start = startDate && startDate.value ? new Date(startDate.value) : null;
        const end = endDate && endDate.value ? new Date(endDate.value) : null;
        reportsTableRows.forEach(row => {
            const dateText = row.children[0].textContent.trim();
            const rowDate = new Date(dateText);
            let show = true;
            if (start && rowDate < start) show = false;
            if (end && rowDate > end) show = false;
            row.style.display = show ? '' : 'none';
        });
    }
    if (startDate) startDate.addEventListener('change', filterByDate);
    if (endDate) endDate.addEventListener('change', filterByDate);

    // Score filter
    const minScore = document.getElementById('minScore');
    const maxScore = document.getElementById('maxScore');
    function filterByScore() {
        const min = minScore && minScore.value ? parseFloat(minScore.value) : null;
        const max = maxScore && maxScore.value ? parseFloat(maxScore.value) : null;
        reportsTableRows.forEach(row => {
            const scoreText = row.children[2].textContent.trim();
            const score = parseFloat(scoreText);
            let show = true;
            if (min !== null && (isNaN(score) || score < min)) show = false;
            if (max !== null && (isNaN(score) || score > max)) show = false;
            if (row.style.display !== 'none') row.style.display = show ? '' : 'none';
        });
    }
    if (minScore) minScore.addEventListener('input', filterByScore);
    if (maxScore) maxScore.addEventListener('input', filterByScore);

    // Delete report group
    document.querySelectorAll('.delete-report-group-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const groupId = btn.getAttribute('data-group-id');
            const linkTitle = btn.getAttribute('data-link-title');
            const date = btn.getAttribute('data-date');
            const time = btn.getAttribute('data-time');
            showConfirm(
                `Are you sure you want to delete <b>both the mobile and desktop reports</b> for <b>${linkTitle}</b> on <b>${date}</b> at <b>${time}</b>?<br><br><span class='text-danger'>This will remove all associated data for this test run. This action cannot be undone.</span>`,
                () => {
                    showLoading();
                    fetch(`/reports/group/${groupId}/delete/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            document.querySelectorAll(`tr[data-group-id='${groupId}']`).forEach(row => row.remove());
                            showToast('Both mobile and desktop reports deleted.', 'success');
                        } else {
                            showToast(data.message || 'Failed to delete reports.', 'danger');
                        }
                    })
                    .catch(() => showToast('Failed to delete reports.', 'danger'))
                    .finally(() => hideLoading());
                }
            );
        });
    });
}); 