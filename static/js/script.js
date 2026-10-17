// FraudShieldAI - Real-Time Security Simulation Engine
let currentTransactionId = null;

function loadScenario(type) {
    if (type === 'safe') {
        document.getElementById('amount').value = '34.50';
        document.getElementById('merchant_category').value = 'grocery';
        document.getElementById('hour_of_day').value = '13';
        document.getElementById('hourVal').innerText = '13:00';
        document.getElementById('tx_velocity_1h').value = '1';
        document.getElementById('velocityVal').innerText = '1';
        document.getElementById('avg_amount_ratio').value = '1.0';
        document.getElementById('ratioVal').innerText = '1.0x';
        document.getElementById('distance_from_home').value = '4';
        document.getElementById('distVal').innerText = '4 mi';
        document.getElementById('device_trust_score').value = '0.95';
        document.getElementById('devVal').innerText = '0.95';
        document.getElementById('ip_risk_score').value = '0.05';
        document.getElementById('ipVal').innerText = '0.05';
        document.getElementById('failed_logins_24h').value = '0';
        document.getElementById('is_international').checked = false;
        document.getElementById('is_first_merchant_use').checked = false;
    } else if (type === 'medium') {
        document.getElementById('amount').value = '920.00';
        document.getElementById('merchant_category').value = 'electronics';
        document.getElementById('hour_of_day').value = '21';
        document.getElementById('hourVal').innerText = '21:00';
        document.getElementById('tx_velocity_1h').value = '3';
        document.getElementById('velocityVal').innerText = '3';
        document.getElementById('avg_amount_ratio').value = '3.5';
        document.getElementById('ratioVal').innerText = '3.5x';
        document.getElementById('distance_from_home').value = '45';
        document.getElementById('distVal').innerText = '45 mi';
        document.getElementById('device_trust_score').value = '0.50';
        document.getElementById('devVal').innerText = '0.50';
        document.getElementById('ip_risk_score').value = '0.35';
        document.getElementById('ipVal').innerText = '0.35';
        document.getElementById('failed_logins_24h').value = '1';
        document.getElementById('is_international').checked = false;
        document.getElementById('is_first_merchant_use').checked = true;
    } else if (type === 'danger') {
        document.getElementById('amount').value = '4800.00';
        document.getElementById('merchant_category').value = 'crypto';
        document.getElementById('hour_of_day').value = '3';
        document.getElementById('hourVal').innerText = '3:00';
        document.getElementById('tx_velocity_1h').value = '6';
        document.getElementById('velocityVal').innerText = '6';
        document.getElementById('avg_amount_ratio').value = '8.0';
        document.getElementById('ratioVal').innerText = '8.0x';
        document.getElementById('distance_from_home').value = '1850';
        document.getElementById('distVal').innerText = '1850 mi';
        document.getElementById('device_trust_score').value = '0.05';
        document.getElementById('devVal').innerText = '0.05';
        document.getElementById('ip_risk_score').value = '0.95';
        document.getElementById('ipVal').innerText = '0.95';
        document.getElementById('failed_logins_24h').value = '3';
        document.getElementById('is_international').checked = true;
        document.getElementById('is_first_merchant_use').checked = true;
    }
}

async function submitTransaction(event) {
    event.preventDefault();
    const btn = document.getElementById('btnSubmitTx');
    btn.disabled = true;
    btn.innerText = '⚡ Inferencing on IBM LinuxONE...';

    const payload = {
        amount: parseFloat(document.getElementById('amount').value),
        merchant_category: document.getElementById('merchant_category').value,
        hour_of_day: parseInt(document.getElementById('hour_of_day').value),
        tx_velocity_1h: parseInt(document.getElementById('tx_velocity_1h').value),
        avg_amount_ratio: parseFloat(document.getElementById('avg_amount_ratio').value),
        distance_from_home: parseFloat(document.getElementById('distance_from_home').value),
        device_trust_score: parseFloat(document.getElementById('device_trust_score').value),
        ip_risk_score: parseFloat(document.getElementById('ip_risk_score').value),
        failed_logins_24h: parseInt(document.getElementById('failed_logins_24h').value),
        is_international: document.getElementById('is_international').checked ? 1 : 0,
        is_first_merchant_use: document.getElementById('is_first_merchant_use').checked ? 1 : 0
    };

    try {
        const response = await fetch('/api/analyze-transaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!data.success) {
            alert('Analysis Error: ' + (data.error || 'Unknown error'));
            btn.disabled = false;
            btn.innerText = '🚀 Run Real-Time Risk Analysis';
            return;
        }

        currentTransactionId = data.transaction_id;
        renderVerdict(data);
    } catch (err) {
        alert('Network/Server Error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerText = '🚀 Run Real-Time Risk Analysis';
    }
}

function renderVerdict(data) {
    document.getElementById('resultPlaceholder').style.display = 'none';
    const output = document.getElementById('resultOutput');
    output.style.display = 'block';

    const banner = document.getElementById('verdictBanner');
    const statusText = document.getElementById('verdictStatus');
    const txIdText = document.getElementById('verdictTxId');
    const gaugeFill = document.getElementById('gaugeFill');
    const gaugeScore = document.getElementById('gaugeScore');
    const metaMl = document.getElementById('metaMlProb');
    const metaCat = document.getElementById('metaRiskCategory');
    const reasonList = document.getElementById('reasonList');
    const promptContainer = document.getElementById('actionPromptContainer');

    txIdText.innerText = `Tx #${data.transaction_id}`;
    gaugeScore.innerText = `${data.risk_score} / 100`;
    metaMl.innerText = `${data.ml_probability}%`;
    metaCat.innerText = data.risk_category;

    // Reset Classes
    banner.className = 'verdict-banner';
    gaugeFill.className = 'gauge-fill';

    // Populate Reasons
    reasonList.innerHTML = '';
    if (data.risk_reasons && data.risk_reasons.length > 0) {
        data.risk_reasons.forEach(r => {
            const li = document.createElement('li');
            li.innerText = r;
            reasonList.appendChild(li);
        });
    }

    // Set Gauge and State
    gaugeFill.style.width = `${Math.max(5, data.risk_score)}%`;

    if (data.risk_category === 'LOW') {
        statusText.innerText = '✓ APPROVED (LOW RISK)';
        promptContainer.innerHTML = `
            <div class="alert alert-success">
                <span>Payment successfully approved in simulation. Funds cleared.</span>
            </div>
        `;
    } else if (data.risk_category === 'MEDIUM') {
        banner.classList.add('medium');
        gaugeFill.classList.add('medium');
        statusText.innerText = '⚠️ FLAGGED (MEDIUM RISK)';
        promptContainer.innerHTML = `
            <div class="alert alert-warning" style="display:flex; justify-content:space-between; align-items:center;">
                <span>Simulated step-up authentication required.</span>
                <button type="button" class="btn btn-primary-sm" onclick="openOtpModal('${data.simulated_otp}')">
                    Enter Demo OTP
                </button>
            </div>
        `;
        // Automatically open OTP modal for user convenience
        openOtpModal(data.simulated_otp);
    } else {
        banner.classList.add('danger');
        gaugeFill.classList.add('danger');
        statusText.innerText = '🛑 QUARANTINED (HIGH RISK)';
        promptContainer.innerHTML = `
            <div class="alert alert-danger">
                <span><strong>Quarantined on Hold:</strong> This transaction was blocked from automated clearance and forwarded to the Administrator review queue.</span>
            </div>
        `;
    }
}

function openOtpModal(otp) {
    document.getElementById('displayOtpCode').innerText = otp;
    document.getElementById('inputOtp').value = '';
    document.getElementById('otpError').style.display = 'none';
    document.getElementById('otpModal').style.display = 'flex';
}

function closeOtpModal() {
    document.getElementById('otpModal').style.display = 'none';
}

async function submitSimulatedOtp() {
    const inputVal = document.getElementById('inputOtp').value.trim();
    const errorDiv = document.getElementById('otpError');

    if (!inputVal) {
        errorDiv.innerText = 'Please enter the simulated OTP code.';
        errorDiv.style.display = 'block';
        return;
    }

    try {
        const response = await fetch('/api/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transaction_id: currentTransactionId,
                otp: inputVal
            })
        });

        const res = await response.json();
        if (res.success) {
            closeOtpModal();
            const banner = document.getElementById('verdictBanner');
            const statusText = document.getElementById('verdictStatus');
            banner.className = 'verdict-banner';
            statusText.innerText = '✓ OTP VERIFIED — APPROVED';
            document.getElementById('actionPromptContainer').innerHTML = `
                <div class="alert alert-success">
                    <span>${res.message}</span>
                </div>
            `;
        } else {
            errorDiv.innerText = res.error || 'Invalid OTP code.';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        errorDiv.innerText = 'Server error: ' + err.message;
        errorDiv.style.display = 'block';
    }
}
