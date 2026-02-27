// let IP = 'http://172.20.93.21:8000'; // Change to your backend URL if different
let IP = 'http://10.10.10.199:8000'; // Change to your backend URL if different

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
    const staffId = document.getElementById('staffId').value.trim();
    const msg = document.getElementById('message');
    const token = new URLSearchParams(window.location.search).get('token');

    msg.innerText = "";
    msg.classList.remove('text-red-500', 'text-green-500');

    if (!staffId) {
        msg.innerText = "⚠️ ID Required";
        return;
    }

    try {
        const response = await fetch(`${IP}/check-in`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                staff_id: staffId,
                token: token,
                confirm: confirm
            })
        });

        const result = await response.json();

        // ✅ HANDLE FASTAPI ERRORS FIRST
        if (!response.ok) {
            msg.innerText = `❌ ${result.detail || "Request failed"}`;
            msg.classList.add('text-red-500');
            return;
        }

        // 🔵 Scenario: Show confirmation modal
        if (result.status === "confirm_checkout") {
            document.getElementById('confirmText').innerText =
                "Already signed in.\nWish to Sign out and proceed?";
            const modal = document.getElementById('confirmModal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            return;
        }

        // 🟢 Success Scenarios
        if (result.status === "checked_in") {
            msg.innerText = `✅ Welcome, ${result.staff}!`;
            msg.classList.add('text-green-500');
        } else if (result.status === "checked_out") {
            msg.innerText = `👋 Goodbye, ${result.staff}!`;
            msg.classList.add('text-green-500');
        } else if (result.status === "completed") {
            msg.innerText = "🚫 Attendance already completed today";
            msg.classList.add('text-red-500');
        }

        btn.style.display = 'none';
        document.getElementById('staffId').style.display = 'none';

        closeModal();
        startResetTimer();

    } catch (err) {
        msg.innerText = "📡 Connection Error";
        msg.classList.add('text-red-500');
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

