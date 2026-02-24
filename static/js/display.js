const qrContainer = document.getElementById("qrcode");
const timerElement = document.getElementById("timer");
const progressBar = document.getElementById("progress-bar"); // New reference
const qrcode = new QRCode(qrContainer, { width: 300, height: 300 });

let timeLeft = 30;
const totalTime = 30;
IP = 'http://172.20.93.21:8000'; // Change to your backend URL if different

async function updateQR() {
    try {
        const response = await fetch('/get-current-qr-token');
        const data = await response.json();
        
        // const baseUrl = 
        // const qrUrl = `${baseUrl}/scan?token=${data.token}`;
        const baseUrl = IP; // Change to your backend URL if different
        const qrUrl = `${baseUrl}/scan?token=${data.token}`;
        
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