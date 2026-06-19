const BASE_URL = window.location.origin;

// DOM Element References
const qrContainer = document.getElementById("qrcode");
const timerElement = document.getElementById("timer");
const progressBar = document.getElementById("progress-bar");
const pfInput = document.getElementById("pfInput");
const sendEmailBtn = document.getElementById("sendEmailBtn");
const statusMsg = document.getElementById("statusMsg");

// --- FIX 1: Only initialize the QRCode library if its container actually exists on this page ---
let qrcode = null;
if (qrContainer) {
    qrcode = new QRCode(qrContainer, { width: 300, height: 300 });
}

// State Management
let timeLeft = 45;
const totalTime = 45;
let currentToken = ""; 
let idleTimer;

/**
 * Core QR Code & Token Synchronization
 */
async function updateQR() {
    try {
        const response = await fetch('/get-current-qr-token');
        const data = await response.json();
        
        currentToken = data.token; 
        const qrUrl = `${BASE_URL}/scan?token=${currentToken}`;
        
        // --- FIX 2: Only attempt to update the QR component visually if it is loaded on the screen ---
        if (qrcode) {
            qrcode.clear();
            qrcode.makeCode(qrUrl);
        }
        
        timeLeft = totalTime;
        updateUI(); 
    } catch (err) {
        console.error("Failed to fetch token", err);
    }
}

/**
 * UI State Synchronization (Timer and Progress Bar)
 */
function updateUI() {
    if (timerElement) timerElement.innerText = timeLeft;
    
    if (progressBar) {
        const percentage = (timeLeft / totalTime) * 100;
        progressBar.style.width = `${percentage}%`;

        // Safely check if classes exist before attempting to replace them
        if (timeLeft <= 5) {
            if (progressBar.classList.contains('bg-blue-600')) {
                progressBar.classList.replace('bg-blue-600', 'bg-red-500');
            }
        } else {
            if (progressBar.classList.contains('bg-red-500')) {
                progressBar.classList.replace('bg-red-500', 'bg-blue-600');
            }
        }
    }
}

/**
 * UI Toggle for Collapsible Email Accordion Section
 */
function toggleEmailSection() {
    const section = document.getElementById('email-section');
    const chevron = document.getElementById('chevron-icon');
    if (!section) return;
    
    const isHidden = section.classList.toggle('hidden');
    if (chevron) {
        chevron.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
    }
}

/**
 * Helper to display operational status alerts
 */
function showStatus(text, colorClass) {
    if (!statusMsg) return;
    statusMsg.innerText = text;
    statusMsg.className = `text-xs text-center font-medium ${colorClass}`;
    statusMsg.classList.remove('hidden');
}

/**
 * Email Submission Event Handler
 */
if (sendEmailBtn) {
    sendEmailBtn.addEventListener("click", async () => {
        const pfNumber = pfInput ? pfInput.value.trim() : "";
        if (statusMsg) statusMsg.classList.add('hidden');
        
        if (!pfNumber) {
            showStatus("Please enter a valid PF number.", "text-amber-400");
            return;
        }

        if (!currentToken) {
            showStatus("No active sync token available. Please wait for a fresh cycle.", "text-amber-400");
            return;
        }

        sendEmailBtn.disabled = true;
        sendEmailBtn.innerText = "Dispatching...";

        try {
            const response = await fetch('/send-link', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pf: pfNumber,
                    qr_link: `${BASE_URL}/scan?token=${currentToken}`
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                showStatus("Success! Check your primary or personal inbox.", "text-emerald-400");
                if (pfInput) pfInput.value = ""; 
            } else {
                showStatus(`Error: ${result.detail || 'Failed processing request'}`, "text-rose-400");
            }
        } catch (err) {
            console.error("Transmission error:", err);
            showStatus("Network failure. Connection to dispatch route lost.", "text-rose-400");
        } finally {
            sendEmailBtn.disabled = false;
            sendEmailBtn.innerText = "Send Access Link";
        }
    });
}

/**
 * Global Interactivity Auto-Timeout Operations (Inactivity Redirection)
 */
const resetTimer = () => {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        window.location.href = '/';
    }, 45000); 
};

// Global Execution Intervals
setInterval(() => {
    timeLeft--;
    if (timeLeft <= 0) {
        updateQR();
    } else {
        updateUI();
    }
}, 1000);

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        window.location.href = '/';
    }
});

window.addEventListener('mousemove', resetTimer);
window.addEventListener('mousedown', resetTimer);
window.addEventListener('keypress', resetTimer);
window.addEventListener('touchstart', resetTimer);

// Initial execution hooks
updateQR();
resetTimer();