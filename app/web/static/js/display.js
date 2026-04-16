const BASE_URL = window.location.origin; // Automatically set to current origin

const qrContainer = document.getElementById("qrcode");
const timerElement = document.getElementById("timer");
const progressBar = document.getElementById("progress-bar"); // New reference
const qrcode = new QRCode(qrContainer, { width: 300, height: 300 });


let timeLeft = 45; // Initial time left in seconds
const totalTime = 45; // Total time for the countdown

async function updateQR() {
    try {
        const response = await fetch('/get-current-qr-token');
        const data = await response.json();
        
        const qrUrl = `${BASE_URL}/scan?token=${data.token}`;
        
        qrcode.clear();
        qrcode.makeCode(qrUrl);
        
        // Reset Logic
        timeLeft = totalTime;
        updateUI(); 
    } catch (err) {
        console.error("Failed to fetch token", err);
    }
}

function updateUI() {
    // Update Text
    timerElement.innerText = timeLeft;
    
    // Update Progress Bar Width
    const percentage = (timeLeft / totalTime) * 100;
    progressBar.style.width = `${percentage}%`;

    // Optional: Change color to red when time is low
    if (timeLeft <= 5) {
        progressBar.classList.replace('bg-blue-600', 'bg-red-500');
    } else {
        progressBar.classList.replace('bg-red-500', 'bg-blue-600');
    }
}

setInterval(() => {
    timeLeft--;
    if (timeLeft <= 0) {
        updateQR();
    } else {
        updateUI();
    }
}, 1000);

// Initial load
updateQR();


// 1. Keyboard Shortcut: Escape key to go home
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        window.location.href = '/';
    }
});

// 2. Auto-Timeout: Redirect to home after 45 seconds of inactivity
// This resets whenever the user moves the mouse or touches the screen
let idleTimer;

const resetTimer = () => {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        window.location.href = '/';
    }, 45000); // 45000ms = 45 seconds
};

// Listen for user interaction to reset the idle clock
window.addEventListener('mousemove', resetTimer);
window.addEventListener('mousedown', resetTimer);
window.addEventListener('keypress', resetTimer);
window.addEventListener('touchstart', resetTimer);

// Initialize the timer on page load
resetTimer();