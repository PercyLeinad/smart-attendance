/**
 * Admin Dashboard - Attendance Reports Logic
 */

// 1. Element Selectors
const form = document.getElementById("reportForm");
const exportBtn = document.getElementById("exportBtn");
const body = document.getElementById("reportBody");
const title = document.getElementById("reportTitle");

// 2. Main Report Generation Handler
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const startDate = formData.get("start_date");
    const endDate = formData.get("end_date");

    if (!startDate || !endDate) return;

    // Update UI Header
    if (title) {
        title.innerHTML = `
            Attendance Report 
            <span class="text-indigo-500 font-medium ml-2 text-sm">
                (${startDate} to ${endDate})
            </span>
        `;
    }

    // Modern Loading State (matches the 3-column UI)
    body.innerHTML = `
        <tr>
            <td colspan="3" class="px-8 py-20 text-center">
                <div class="flex flex-col items-center justify-center gap-3">
                    <i class="fa-solid fa-circle-notch fa-spin text-3xl text-indigo-600"></i>
                    <p class="text-slate-500 font-medium animate-pulse">Analyzing attendance data...</p>
                </div>
            </td>
        </tr>
    `;

    try {
        const res = await fetch(`/admin/report?start_date=${startDate}&end_date=${endDate}`);
        
        if (!res.ok) throw new Error("Server responded with an error");
        
        const data = await res.json();
        renderTable(data);
    } catch (err) {
        console.error("Fetch Error:", err);
        showErrorState();
    }
});

// 3. Table Rendering Engine
function renderTable(data) {
    // Clear the loading state
    body.innerHTML = "";

    // Handle Empty Results
    if (!data || data.length === 0) {
        body.innerHTML = `
            <tr>
                <td colspan="3" class="px-8 py-20 text-center">
                    <div class="flex flex-col items-center justify-center gap-2 text-slate-400">
                        <i class="fa-solid fa-magnifying-glass text-4xl mb-2 opacity-20"></i>
                        <p class="font-semibold text-slate-500">No records found</p>
                        <p class="text-xs">Try selecting a different date range.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    // Map data to table rows
    // Using .join('') is more performant than += for large datasets
    const rowsHtml = data.map(row => `
        <tr class="hover:bg-slate-50/80 transition-colors group">
            <td class="px-8 py-4">
                <div class="flex items-center gap-3">
                    <div class="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-500 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors">
                        PF
                    </div>
                    <span class="font-mono font-bold text-slate-700">${row.pf}</span>
                </div>
            </td>
            <td class="px-8 py-4">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                    <i class="fa-solid fa-check-double mr-1.5 text-[10px]"></i>
                    ${row.days_present} ${row.days_present === 1 ? 'Day' : 'Days'}
                </span>
            </td>
            <td class="px-8 py-4 text-right">
                <span class="text-xs font-bold uppercase tracking-widest text-slate-300 group-hover:text-slate-500 transition-colors">
                    Verified
                </span>
            </td>
        </tr>
    `).join('');

    body.innerHTML = rowsHtml;
}

// 4. Export to CSV Handler
exportBtn.addEventListener("click", () => {
    const formData = new FormData(form);
    const startDate = formData.get("start_date");
    const endDate = formData.get("end_date");

    if (!startDate || !endDate) {
        // Trigger a subtle alert or focus the input
        alert("Please select both a Start and End date before exporting.");
        return;
    }

    // Redirect to the export endpoint
    window.location.href = `/admin/report/export?start_date=${startDate}&end_date=${endDate}`;
});

// 5. Helper: Error State UI
function showErrorState() {
    body.innerHTML = `
        <tr>
            <td colspan="3" class="px-8 py-16 text-center bg-red-50/30">
                <div class="flex flex-col items-center justify-center gap-2 text-red-500">
                    <i class="fa-solid fa-triangle-exclamation text-3xl"></i>
                    <p class="font-bold">System Connection Error</p>
                    <p class="text-xs text-red-400">Failed to communicate with the attendance database.</p>
                    <button onclick="location.reload()" class="mt-4 text-xs font-bold uppercase tracking-widest bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition">
                        Retry Connection
                    </button>
                </div>
            </td>
        </tr>
    `;
}