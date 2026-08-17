const BASE_URL = window.location.origin;

const qrContainer = document.getElementById("qrcode");
const timerElement = document.getElementById("timer");
const progressBar = document.getElementById("progress-bar");
const pfInput = document.getElementById("pfInput");
const sendEmailBtn = document.getElementById("sendEmailBtn");
const statusMsg = document.getElementById("statusMsg");

let qrcode = null;
if (qrContainer) {
    qrcode = new QRCode(qrContainer, { width: 300, height: 300 });
}

let timeLeft = 45;
const totalTime = 45;
let currentToken = "";
let idleTimer;

async function updateQR() {
    try {
        const response = await fetch('/get-current-qr-token');
        const data = await response.json();

        currentToken = data.token;
        const qrUrl = `${BASE_URL}/scan?token=${currentToken}`;


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

function updateUI() {
    if (timerElement) timerElement.innerText = timeLeft;

    if (progressBar) {
        const percentage = (timeLeft / totalTime) * 100;
        progressBar.style.width = `${percentage}%`;

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

function toggleEmailSection() {
    const section = document.getElementById('email-section');
    const chevron = document.getElementById('chevron-icon');
    if (!section) return;

    const isHidden = section.classList.toggle('hidden');
    if (chevron) {
        chevron.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
    }
}

function showStatus(text, colorClass) {
    if (!statusMsg) return;
    statusMsg.innerText = text;
    statusMsg.className = `text-xs text-center font-medium ${colorClass}`;
    statusMsg.classList.remove('hidden');
}

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
                    pf: pfNumber
                })
            });

            const result = await response.json();

            if (response.ok) {

                showStatus(
                    'If the account is eligible, an access link will be sent shortly.',
                    'text-emerald-400'
                );

                pfInput.value = '';

            } else {

                switch (response.status) {

                    case 403:
                        showStatus(
                            'Email requests are only allowed during working hours.',
                            'text-rose-400'
                        );
                        break;

                    case 404:
                        showStatus(
                            'No such user found in the system, please verify the PF number.',
                            'text-rose-400'
                        );
                        break;
                    case 429:
                        showStatus(
                            'You have reached the request limit. Please try again later.',
                            'text-rose-400'
                        );
                        break;

                    case 422:
                        showStatus(
                            'This account is not eligible for email dispatch. Please contact support.',
                            'text-rose-400'
                        );
                        break;
                    default:
                        showStatus(
                            'Unable to process request.',
                            'text-rose-400'
                        );
                }
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

const resetTimer = () => {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        window.location.href = '/';
    }, 45000);
};

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

updateQR();
resetTimer();