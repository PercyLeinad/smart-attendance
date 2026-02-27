// let IP = 'http://172.20.93.21:8000'; // Change to your backend URL if different
let IP = 'http://10.10.10.199:8000'; // Change to your backend URL if different

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

async function submitAttendance(confirm = false) {
    const staffId = document.getElementById('staffId').value.trim();
    const msg = document.getElementById('message');
    const token = new URLSearchParams(window.location.search).get('token');

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
                confirm: confirm // This tells the backend to override if already signed in
            })
        });

        const result = await response.json();

        // 🔵 Scenario: Show confirmation modal
        if (result.status === "confirm_checkout") {
            document.getElementById('confirmText').innerText = "Already signed in.\nWish to Sign out and proceed?";
            const modal = document.getElementById('confirmModal');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            return; 
        }

        // 🟢 Other Scenarios: Success/Error
        if (result.status === "checked_in") {
            msg.innerText = `✅ Welcome, ${result.staff}!`;
        } else if (result.status === "checked_out") {
            msg.innerText = `👋 Goodbye, ${result.staff}!`;
        } else if (result.status === "completed") {
            msg.innerText = "🚫 Attendance already completed today";
        }
        
        // Hide the submit button and input to prevent double-taps
        btn.style.display = 'none';
        document.getElementById('staffId').style.display = 'none';
        
        // Close modal if it was open
        closeModal();
        
        // Start the 10-second redirect process
        startResetTimer();

    } catch (err) {
        msg.innerText = "📡 Connection Error";
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


