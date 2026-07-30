const BASE_URL = window.location.origin;

const qrContainer = document.getElementById('qrcode');
const timerElement = document.getElementById('timer');
const progressBar = document.getElementById('progress-bar');
const pfInput = document.getElementById('pfInput');
const sendEmailBtn = document.getElementById('sendEmailBtn');
const statusMsg = document.getElementById('statusMsg');

let qrcode = null;
if (qrContainer) {
    qrcode = new QRCode(qrContainer, { width: 300, height: 300 });
}

let timeLeft = 45;
const totalTime = 45;
let idleTimer;

async function updateQR() {
    try {
        const response = await fetch('/get-current-qr-token');
        const data = await response.json();

        const qrUrl = `${BASE_URL}/scan?token=${data.token}`;

        if (qrcode) {
            qrcode.clear();
            qrcode.makeCode(qrUrl);
        }

        timeLeft = totalTime;
        updateUI();

    } catch (err) {
        console.error('Failed to fetch token', err);
    }
}

function updateUI() {
    if (timerElement) {
        timerElement.innerText = timeLeft;
    }

    if (progressBar) {
        const percentage = (timeLeft / totalTime) * 100;
        progressBar.style.width = `${percentage}%`;

        if (timeLeft <= 5) {
            progressBar.classList.remove('bg-blue-600');
            progressBar.classList.add('bg-red-500');
        } else {
            progressBar.classList.remove('bg-red-500');
            progressBar.classList.add('bg-blue-600');
        }
    }
}

function showStatus(text, colorClass) {
    if (!statusMsg) return;

    statusMsg.textContent = text;
    statusMsg.className = `text-xs text-center font-medium ${colorClass}`;
    statusMsg.classList.remove('hidden');
}

if (sendEmailBtn) {
    sendEmailBtn.addEventListener('click', async () => {

        const pfNumber = pfInput?.value.trim();

        statusMsg?.classList.add('hidden');

        if (!pfNumber) {
            showStatus('Please enter a valid PF number.', 'text-amber-400');
            return;
        }

        sendEmailBtn.disabled = true;
        sendEmailBtn.textContent = 'Dispatching...';

        try {
            const response = await fetch('/send-link', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pf: pfNumber })
            });

            const result = await response.json();

            if (response.ok) {
                showStatus(
                    'If the account is eligible, an access link will be sent shortly.',
                    'text-emerald-400'
                );

                pfInput.value = '';

            } else {
                showStatus(
                    result.detail || 'Unable to process request.',
                    'text-rose-400'
                );
            }

        } catch (err) {
            console.error(err);
            showStatus('Network error. Please try again.', 'text-rose-400');

        } finally {
            sendEmailBtn.disabled = false;
            sendEmailBtn.textContent = 'Send Access Link';
        }
    });
}

function resetTimer() {
    clearTimeout(idleTimer);

    idleTimer = setTimeout(() => {
        window.location.href = '/';
    }, 45000);
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        window.location.href = '/';
    }
});

['mousemove', 'mousedown', 'keypress', 'touchstart']
    .forEach(evt => window.addEventListener(evt, resetTimer));

setInterval(() => {
    timeLeft--;

    if (timeLeft <= 0) {
        updateQR();
    } else {
        updateUI();
    }
}, 1000);

updateQR();
resetTimer();