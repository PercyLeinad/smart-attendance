/**
 * Admin Dashboard - Attendance & Device Risk Logic
 */

// Global State - Attendance
let currentPage = 1;
const rowsPerPage = 5;
let reportData = [];

// Element Selectors - Attendance
const form = document.getElementById("reportForm");
const exportBtn = document.getElementById("exportBtn");
const body = document.getElementById("reportBody");
const title = document.getElementById("reportTitle");

// Main Attendance Generation Handler
if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const startDate = formData.get("start_date");
        const endDate = formData.get("end_date");

        if (!startDate || !endDate) return;

        currentPage = 1;

        if (title) {
            title.innerHTML = `
                Attendance Report Dated
                <span class="text-indigo-500 font-medium ml-2 text-sm">
                    (${startDate} to ${endDate})
                </span>
            `;
        }

        body.innerHTML = `
            <tr>
                <td colspan="5" class="px-8 py-20 text-center">
                    <div class="flex flex-col items-center justify-center gap-3">
                        <i class="fa-solid fa-circle-notch fa-spin text-3xl text-indigo-600"></i>
                        <p class="text-slate-500 font-medium animate-pulse">Analyzing attendance data...</p>
                    </div>
                </td>
            </tr>
        `;

        try {
            const res = await fetch(`/admin/report/attendance?start_date=${startDate}&end_date=${endDate}`);
            if (!res.ok) throw new Error("Server responded with an error");

            reportData = await res.json();
            renderTable();
        } catch (err) {
            console.error("Fetch Error:", err);
            showErrorState();
        }
    });
}

function renderTable() {
    if (!reportData || reportData.length === 0) {
        body.innerHTML = `
            <tr>
                <td colspan="5" class="px-8 py-20 text-center">
                    <div class="flex flex-col items-center justify-center gap-2 text-slate-400">
                        <i class="fa-solid fa-magnifying-glass text-4xl mb-2 opacity-20"></i>
                        <p class="font-semibold text-slate-500">No records found</p>
                    </div>
                </td>
            </tr>
        `;
        renderPaginationControls(0, 0);
        return;
    }

    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    const paginatedItems = reportData.slice(startIndex, endIndex);
    const totalPages = Math.ceil(reportData.length / rowsPerPage);

    body.innerHTML = paginatedItems.map(row => `
        <tr class="hover:bg-slate-50/80 transition-colors group">   
            <td class="px-8 py-4">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                    <i class="fa-solid fa-user mr-1.5 text-[10px]"></i>
                    ${row.Pf || 'N/A'}
                </span>
            </td>
            <td class="px-8 py-4">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                    <i class="fa-solid fa-user mr-1.5 text-[10px]"></i>
                    ${row.Name || 'N/A'}
                </span>
            </td>
            <td class="px-8 py-4 text-center">
                <span class="text-[10px] font-bold uppercase tracking-widest text-slate-500 bg-slate-100 px-2 py-1 rounded">
                    ${row["Department Name"] || 'N/A'}
                </span>
            </td>
            <td class="px-8 py-4 text-right">
                <span class="text-xs font-mono font-bold text-indigo-600">
                    ${row.Arrival || '--:--'}
                </span>
            </td>
            <td class="px-8 py-4 text-right">
                <span class="text-xs font-mono font-bold text-slate-500">
                    ${row.Checkout || '--:--'}
                </span>
            </td>
        </tr>
    `).join('');

    renderPaginationControls(reportData.length, totalPages);
}

window.changePage = function (direction) {
    currentPage += direction;
    renderTable();
};

function renderPaginationControls(totalCount, totalPages) {
    const start = totalCount === 0 ? 0 : (currentPage - 1) * rowsPerPage + 1;
    const end = Math.min(currentPage * rowsPerPage, totalCount);

    document.getElementById('startRange').innerText = start;
    document.getElementById('endRange').innerText = end;
    document.getElementById('totalRecords').innerText = totalCount;

    document.getElementById('prevBtn').disabled = currentPage === 1;
    document.getElementById('nextBtn').disabled = currentPage === totalPages || totalPages === 0;
}

if (exportBtn) {
    exportBtn.addEventListener("click", () => {
        const formData = new FormData(form);
        const startDate = formData.get("start_date");
        const endDate = formData.get("end_date");
        if (!startDate || !endDate) {
            alert("Please select both a Start and End date before exporting.");
            return;
        }
        window.location.href = `/admin/report/attendance/export?start_date=${startDate}&end_date=${endDate}`;
    });
}

function showErrorState() {
    body.innerHTML = `
        <tr>
            <td colspan="5" class="px-8 py-16 text-center bg-red-50/30">
                <div class="flex flex-col items-center justify-center gap-2 text-red-500">
                    <i class="fa-solid fa-triangle-exclamation text-3xl"></i>
                    <p class="font-bold">System Connection Error</p>
                    <button onclick="location.reload()" class="mt-4 text-xs font-bold uppercase tracking-widest bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition">
                        Retry Connection
                    </button>
                </div>
            </td>
        </tr>
    `;
}

// Global State - Device Risk
let riskCurrentPage = 1;
const riskRowsPerPage = 5;
let riskData = [];

// Define fetchRiskReport Globally so inline `onclick="fetchRiskReport()"` can access it
window.fetchRiskReport = async function() {
    const tableBody = document.getElementById('deviceRiskBody');
    if (!tableBody) return;

    tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="px-6 py-12 text-center text-emerald-900/40">
                <div class="animate-pulse font-medium">Analyzing device fingerprints...</div>
            </td>
        </tr>`;

    try {
        const response = await fetch('/admin/report/device-risk');
        if (!response.ok) throw new Error('Network error');

        const json = await response.json();

        // Handles standard array responses or JSON formatted as { data: [...] }
        riskData = Array.isArray(json) ? json : (json.data || []);
        riskCurrentPage = 1;

        renderRiskTable();

    } catch (error) {
        console.error('Fetch error:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-red-500 font-semibold">
                    Error loading risk data.
                </td>
            </tr>`;
    }
};

window.changeRiskPage = function (direction) {
    riskCurrentPage += direction;
    renderRiskTable();
};

function renderRiskPagination(totalCount, totalPages) {
    const start = totalCount === 0 ? 0 : (riskCurrentPage - 1) * riskRowsPerPage + 1;
    const end = Math.min(riskCurrentPage * riskRowsPerPage, totalCount);

    const startEl = document.getElementById('riskStartRange');
    const endEl = document.getElementById('riskEndRange');
    const totalEl = document.getElementById('riskTotalRecords');
    const prevBtn = document.getElementById('riskPrevBtn');
    const nextBtn = document.getElementById('riskNextBtn');

    if (startEl) startEl.innerText = start;
    if (endEl) endEl.innerText = end;
    if (totalEl) totalEl.innerText = totalCount;

    if (prevBtn) prevBtn.disabled = riskCurrentPage === 1;
    if (nextBtn) nextBtn.disabled = riskCurrentPage === totalPages || totalPages === 0;
}

function renderRiskTable() {
    const tableBody = document.getElementById('deviceRiskBody');
    if (!tableBody) return;

    if (!Array.isArray(riskData) || riskData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-slate-400">
                    No risk anomalies detected.
                </td>
            </tr>`;
        renderRiskPagination(0, 0);
        return;
    }

    const startIndex = (riskCurrentPage - 1) * riskRowsPerPage;
    const endIndex = startIndex + riskRowsPerPage;
    const paginatedItems = riskData.slice(startIndex, endIndex);
    const totalPages = Math.ceil(riskData.length / riskRowsPerPage);

    tableBody.innerHTML = paginatedItems.map(item => {
        const score = Number(item.risk_score || 0);
        const riskColor =
            score >= 8 ? 'text-red-600 font-bold' :
            score >= 5 ? 'text-orange-500 font-semibold' :
            'text-emerald-600';

        return `
            <tr class="hover:bg-emerald-50/50 transition-colors">
                <td class="px-8 py-4">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                        <i class="fa-solid fa-user mr-1.5 text-[10px]"></i>
                        ${item.staff_pf || item.pf || 'N/A'}
                    </span>
                </td>
                <td class="px-8 py-4">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                        <i class="fa-solid fa-user mr-1.5 text-[10px]"></i>
                        ${item.name || 'N/A'}
                    </span>
                </td>
                <td class="px-6 py-4 text-sm text-slate-600">
                    ${item.device_count ?? 0}
                </td>
                <td class="px-6 py-4 text-sm text-slate-600">
                    ${item.ip_changes ?? 0}
                </td>
                <td class="px-6 py-4">
                    <span class="${item.shared_device_flag
                        ? 'bg-red-100 text-red-700'
                        : 'bg-emerald-50 text-emerald-600'} text-[10px] px-2 py-0.5 rounded uppercase font-bold">
                        ${item.shared_device_flag ? 'Shared Device' : 'Private'}
                    </span>
                </td>
                <td class="px-6 py-4 text-right">
                    <span class="${riskColor}">
                        ${score}
                    </span>
                </td>
            </tr>
        `;
    }).join('');

    renderRiskPagination(riskData.length, totalPages);
}

// Bind events on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    const exportRiskBtn = document.getElementById('exportRiskBtn');

    // Auto-fetch report on initial page load
    fetchRiskReport();

    if (exportRiskBtn) {
        exportRiskBtn.addEventListener("click", () => {
            window.location.href = `/admin/report/device-risk/export`;
        });
    }
});