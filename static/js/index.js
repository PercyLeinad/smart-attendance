const IP = 'http://172.20.93.21:8000'; // Backend URL

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


async function submitAttendance() {
    const btn = document.getElementById('btn');
    const msg = document.getElementById('message');
    const staffInput = document.getElementById('staffId');

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (!staffInput || !staffInput.value) {
        if (msg) {
            msg.innerText = "⚠️ ID Required";
            msg.className = "mt-4 text-sm font-medium text-amber-600";
        }
        return;
    }

    btn.disabled = true;
    btn.innerText = "Processing...";

    try {
        const response = await fetch(`${IP}/check-in`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                staff_id: staffInput.value,
                token: token
            })
        });

        const result = await response.json();

        if (response.ok) {
            // Success message
            if (result.status === "checked_in") {
                msg.innerText = `✅ Welcome, ${result.staff}! Checked in successfully.`;
                msg.className = "mt-4 text-sm font-medium text-green-600";
            } else {
                msg.innerText = `👋 Goodbye, ${result.staff}! Checked out successfully.`;
                msg.className = "mt-4 text-sm font-medium text-blue-600";
            }

            // Hide form
            staffInput.classList.add('hidden');
            btn.classList.add('hidden');

            // 🔄 Auto refresh after 5 seconds
            setTimeout(() => {
                location.replace(location.pathname);
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