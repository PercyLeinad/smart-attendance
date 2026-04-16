const BASE_URL = window.location.origin; // Automatically set to current origin

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        window.location.reload();
    }
});

window.addEventListener('load', function () {
    console.log("Window load event triggered");

    startClock();

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    const msg = document.getElementById('message');
    const btn = document.getElementById('btn');
    const staffInput = document.getElementById('staffId');

    if (!token) {
        console.log("No token found - triggering lockdown UI");

        if (msg) {
            msg.innerText = "❌\nNo QR Token found.\nPlease scan the QR code to proceed.";
            msg.className = "mt-4 text-sm font-medium text-red-600 bg-red-50 p-3 rounded-lg";
        }

        if (btn) btn.style.display = 'none';
        if (staffInput) staffInput.style.display = 'none';
    }
});


function startClock() {
    const clockElement = document.getElementById('clock');
    if (!clockElement) return;

    function updateTime() {
        const now = new Date();

        const seconds = now.getSeconds();
        clockElement.classList.toggle('opacity-100', seconds % 2 === 0);
        clockElement.classList.toggle('opacity-80', seconds % 2 !== 0);

        const timeString = now.toLocaleTimeString([], {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        clockElement.innerText = timeString;
    }

    updateTime();
    setInterval(updateTime, 1000);
}

async function submitAttendance(confirm = false) {
    const staffIdInput = document.getElementById('staffId');
    const staffId = staffIdInput.value.trim();
    const msg = document.getElementById('message');
    const btn = document.getElementById('btn');
    const icon = document.getElementById('main-icon-fa');
    const token = new URLSearchParams(window.location.search).get('token');

    msg.innerText = "";
    msg.classList.remove('text-red-500', 'text-green-500');

    if (!staffId) {
        msg.innerText = "⚠️ ID Number Required";
        msg.className = "mt-6 text-sm font-bold min-h-[3rem] flex items-center justify-center px-4 rounded-xl text-amber-600 bg-amber-50";
        return;
    }

    try {
        const response = await fetch(`${BASE_URL}/check-in`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                staff_id: staffId,
                token: token,
                confirm: confirm 
            })
        });

        const result = await response.json();

        // --- ERROR HANDLING (400, 404, etc.) ---
        if (!response.ok) {
            msg.innerText = `❌ ${result.detail || "Error occurred"}`;
            msg.className = "mt-6 text-sm font-bold min-h-[3rem] flex items-center justify-center px-4 rounded-xl text-red-600 bg-red-50 border border-red-100";
            if(icon) icon.className = "fa-solid fa-circle-exclamation text-3xl text-red-500";
            return; // Stop execution here
        }

        // --- SUCCESS SCENARIOS ---
        if (result.status === "confirm_checkout") {
            document.getElementById('confirmText').innerText = `Staff: ${result.staff}\nAlready signed in. Wish to Sign out?`;
            const modal = document.getElementById('confirmModal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            return;
        }

        if (result.status === "checked_in") {
            msg.innerText = `✅ Welcome, ${result.staff}!`;
            msg.className = "mt-6 text-sm font-bold min-h-[3rem] flex items-center justify-center px-4 rounded-xl text-emerald-700 bg-emerald-100";
            if(icon) icon.className = "fa-solid fa-check-double text-3xl text-emerald-600";
        } else if (result.status === "checked_out") {
            msg.innerText = `👋 Goodbye, ${result.staff}!`;
            msg.className = "mt-6 text-sm font-bold min-h-[3rem] flex items-center justify-center px-4 rounded-xl text-amber-700 bg-amber-100";
            if(icon) icon.className = "fa-solid fa-door-open text-3xl text-amber-600";
        } else if (result.status === "completed") {
            msg.innerText = "🚫 Attendance already completed today";
            msg.className = "mt-6 text-sm font-bold min-h-[3rem] flex items-center justify-center px-4 rounded-xl text-slate-600 bg-slate-100";
        }
        
        // Hide inputs on success
        if(btn) btn.style.display = 'none';
        staffIdInput.style.display = 'none';
        
        closeModal();
        startResetTimer();

    } catch (err) {
        msg.innerText = "📡 Connection Error";
        msg.className = "mt-6 text-sm font-bold min-h-[3rem] flex items-center justify-center px-4 rounded-xl text-red-600 bg-red-50";
        console.error(err);
    }
}

function closeModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// This is the function the MODAL "Confirm" button should call
function proceedAttendance() {
    submitAttendance(true);
}


function startResetTimer() {
    const msg = document.getElementById('message');
    let timeLeft = 10;

    // Create a small reset button dynamically or show a hidden one
    const resetBtn = document.getElementById('resetBtn');
    resetBtn.classList.remove('hidden');

    const interval = setInterval(() => {
        timeLeft--;
        resetBtn.innerText = `Reset Now (${timeLeft}s)`;

        if (timeLeft <= 0) {
            clearInterval(interval);
            window.location.href = '/scan'; // Redirect to scan page
        }
    }, 1000);
}

// Redirect manually if they don't want to wait 10 seconds
function manualReset() {
    window.location.href = '/scan';
}

