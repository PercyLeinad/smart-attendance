let IP = 'http://172.20.93.21:8000'; // Change to your backend URL if different

window.addEventListener('load', function () {
    console.log("Window load event triggered");
    startClock();
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    console.log("Detected Token:", token);

    const msg = document.getElementById('message');
    const btn = document.getElementById('btn');
    const staffInput = document.getElementById('staffId');

    if (!token) {
        console.log("No token found - triggering lockdown UI");
        msg.innerText = "❌\nNo QR Token found.\nPlease scan the QR code to proceed.";
        msg.className = "mt-4 text-sm font-medium text-red-600 bg-red-50 p-3 rounded-lg";

        // Force hide the elements
        if (btn) btn.style.display = 'none';
        if (staffInput) staffInput.style.display = 'none';
    } else {
        console.log("Token valid. UI remains open.");
    }
});
function startClock() {
    const clockElement = document.getElementById('clock');

    function updateTime() {
        const now = new Date();

        const seconds = now.getSeconds();
        if (seconds % 2 === 0) {
            clockElement.classList.add('opacity-100');
            clockElement.classList.remove('opacity-80');
        } else {
            clockElement.classList.add('opacity-80');
            clockElement.classList.remove('opacity-100');
        }

        // Formats time as HH:MM:SS
        const timeString = now.toLocaleTimeString([], {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        if (clockElement) {
            clockElement.innerText = timeString;
        }
    }

    // Run immediately, then every 1000ms (1 second)
    updateTime();
    setInterval(updateTime, 1000);
}

async function submitAttendance() {

    const staffId = document.getElementById('staffId').value;
    const msg = document.getElementById('message');

    if (!staffId) {
        msg.innerText = "⚠️ ID Required";
        msg.className = "mt-4 text-sm font-medium text-amber-600";
        return;
    }

    try {
        // Ask backend for current status
        const statusResponse = await fetch(`${IP}/attendance-status?pf=${staffId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        const statusData = await statusResponse.json();

        let actionText = "";

        if (statusData.current_status === "checked_in") {
            actionText = "Confirm Check-Out?";
        } else {
            actionText = "Confirm Check-In?";
        }

        document.getElementById('confirmText').innerText =
            `${actionText} (PF/ID: ${staffId})`;

        document.getElementById('confirmModal').classList.remove('hidden');
        document.getElementById('confirmModal').classList.add('flex');

    } catch (err) {
        msg.innerText = "📡 Unable to verify status";
        msg.className = "mt-4 text-sm font-medium text-red-500";
    }
}

function closeModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

async function proceedAttendance() {

    closeModal();

    const btn = document.getElementById('btn');
    const msg = document.getElementById('message');
    const staffId = document.getElementById('staffId').value;
    const iconCont = document.getElementById('icon-container');

    const token = new URLSearchParams(window.location.search).get('token');

    btn.disabled = true;
    btn.innerText = "Processing...";

    try {
        const response = await fetch(`${IP}/check-in`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                staff_id: staffId,
                token: token
            })
        });

        const result = await response.json();

        if (response.ok) {

            if (result.status === "checked_in") {
                msg.innerText = `✅ Welcome, ${result.staff}! Checked in.`;
                msg.className = "mt-4 text-sm font-medium text-green-600";
                iconCont.className = "mb-4 text-green-500";
            } else {
                msg.innerText = `👋 Goodbye, ${result.staff}! Checked out.`;
                msg.className = "mt-4 text-sm font-medium text-blue-600";
                iconCont.className = "mb-4 text-blue-500";
            }

            document.getElementById('staffId').classList.add('hidden');
            btn.classList.add('hidden');

            // Optional: Auto reset after 5 sec
            setTimeout(() => {
                window.history.replaceState({}, document.title, window.location.pathname);
                window.location.reload();
            }, 5000);

        } else {
            msg.innerText = "❌ " + (result.detail || "Error");
            msg.className = "mt-4 text-sm font-medium text-red-600";
            btn.disabled = false;
            btn.innerText = "Try Again";
        }

    } catch (err) {
        msg.innerText = "📡 Connection Error";
        msg.className = "mt-4 text-sm font-medium text-red-500";
        btn.disabled = false;
        btn.innerText = "Retry";
    }
}
