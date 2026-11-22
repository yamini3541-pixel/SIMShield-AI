const API_BASE_URL = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", function () {
    loadDashboardStats();
    loadTransactions();

    const fraudForm = document.getElementById("fraudForm");

    if (fraudForm) {
        fraudForm.addEventListener("submit", function (event) {
            event.preventDefault();
            checkFraud();
        });
    }
});


// ========================================================
// FRAUD CHECK
// ========================================================

async function checkFraud() {

    const button = document.getElementById("checkButton");

    if (button) {
        button.disabled = true;
        button.innerText = "Analyzing...";
    }

    const data = {
        user_id: document.getElementById("userId").value.trim(),

        sim_changed:
            Number(document.getElementById("simChanged").value),

        new_device:
            Number(document.getElementById("newDevice").value),

        location_changed:
            Number(document.getElementById("locationChanged").value),

        failed_otp_attempts:
            Number(document.getElementById("failedOtp").value) || 0,

        transaction_amount:
            Number(document.getElementById("transactionAmount").value) || 0,

        transaction_velocity:
            Number(document.getElementById("transactionVelocity").value) || 0
    };

    try {

        const response = await fetch(
            API_BASE_URL + "/api/fraud/check",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Fraud check failed"
            );
        }

        showResult(result);

        loadDashboardStats();
        loadTransactions();

    } catch (error) {

        console.error("Fraud check error:", error);

        alert(
            "Fraud check error: " +
            error.message
        );

    } finally {

        if (button) {
            button.disabled = false;
            button.innerText = "Check Transaction";
        }
    }
}


// ========================================================
// SHOW RESULT
// ========================================================

function showResult(result) {

    const section =
        document.getElementById("resultSection");

    const badge =
        document.getElementById("riskBadge");

    const score =
        document.getElementById("riskScore");

    const action =
        document.getElementById("recommendedAction");

    const reasonsList =
        document.getElementById("reasonsList");

    const transactionId =
        document.getElementById("transactionId");


    if (section) {
        section.style.display = "block";
    }


    if (badge) {
        badge.innerText =
            result.risk_level || "UNKNOWN";

        badge.className =
            "risk-badge " +
            String(
                result.risk_level || ""
            ).toLowerCase();
    }


    if (score) {
        score.innerText =
            Number(
                result.risk_score || 0
            ).toFixed(1) +
            " / 100";
    }


    if (action) {
        action.innerText =
            formatAction(result.action);
    }


    if (transactionId) {
        transactionId.innerText =
            result.transaction_id || "-";
    }


    let reasons = result.reasons || [];


    if (typeof reasons === "string") {

        try {
            reasons = JSON.parse(reasons);
        } catch (error) {
            reasons = [reasons];
        }
    }


    if (reasonsList) {

        reasonsList.innerHTML = "";

        if (reasons.length === 0) {

            const item =
                document.createElement("li");

            item.innerText =
                "No major risk signals detected.";

            reasonsList.appendChild(item);

        } else {

            reasons.forEach(function (reason) {

                const item =
                    document.createElement("li");

                item.innerText = reason;

                reasonsList.appendChild(item);
            });
        }
    }


    // RESET VERIFICATION PANELS

    const recovery =
        document.getElementById(
            "recoveryVerification"
        );

    const biometric =
        document.getElementById(
            "biometricVerification"
        );

    const eyeScan =
        document.getElementById(
            "eyeScanPanel"
        );

    const eyeScanActions =
        document.getElementById(
            "eyeScanActions"
        );

    const scanResult =
        document.getElementById(
            "scanResult"
        );


    if (recovery) {
        recovery.classList.add("hidden");
    }

    if (biometric) {
        biometric.classList.add("hidden");
    }

    if (eyeScan) {
        eyeScan.classList.add("hidden");
    }

    if (eyeScanActions) {
        eyeScanActions.classList.add("hidden");
    }

    if (scanResult) {
        scanResult.classList.add("hidden");
        scanResult.innerHTML = "";
    }


    // HIGH RISK → ASK ABOUT PHONE

    if (
        String(
            result.risk_level || ""
        ).toUpperCase() === "HIGH"
    ) {

        if (recovery) {

            recovery.classList.remove("hidden");

            recovery.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });
        }
    }


    if (section) {

        section.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
}


// ========================================================
// FORMAT ACTION
// ========================================================

function formatAction(action) {

    if (!action) {
        return "No action";
    }

    return String(action)
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, function (letter) {
            return letter.toUpperCase();
        });
}


// ========================================================
// DASHBOARD STATS
// ========================================================

async function loadDashboardStats() {

    try {

        const response =
            await fetch(
                API_BASE_URL +
                "/api/dashboard/stats"
            );

        const stats =
            await response.json();

        if (!response.ok) {
            throw new Error(
                stats.error ||
                "Unable to load dashboard stats"
            );
        }

        setText(
            "totalTransactions",
            stats.total_transactions || 0
        );

        setText(
            "highRisk",
            stats.high_risk || 0
        );

        setText(
            "mediumRisk",
            stats.medium_risk || 0
        );

        setText(
            "lowRisk",
            stats.low_risk || 0
        );

    } catch (error) {

        console.error(
            "Dashboard stats error:",
            error
        );
    }
}


// ========================================================
// TRANSACTIONS
// ========================================================

async function loadTransactions() {

    try {

        const response =
            await fetch(
                API_BASE_URL +
                "/api/transactions"
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to load transactions"
            );
        }

        const transactions =
            data.transactions ||
            data ||
            [];

        const table =
            document.getElementById(
                "transactionsTable"
            );

        if (!table) {
            return;
        }

        table.innerHTML = "";

        if (transactions.length === 0) {

            table.innerHTML =
                "<tr>" +
                "<td colspan='7'>" +
                "No transactions yet." +
                "</td>" +
                "</tr>";

            return;
        }

        transactions.forEach(function (transaction) {

            const row =
                document.createElement("tr");

            row.innerHTML =

                "<td>" +
                escapeHTML(transaction.id) +
                "</td>" +

                "<td>" +
                escapeHTML(transaction.user_id) +
                "</td>" +

                "<td>" +
                escapeHTML(
                    transaction.risk_level || "-"
                ) +
                "</td>" +

                "<td>" +
                Number(
                    transaction.risk_score || 0
                ).toFixed(1) +
                "</td>" +

                "<td>" +
                escapeHTML(
                    formatAction(transaction.action)
                ) +
                "</td>" +

                "<td>" +
                (
                    transaction.fraud_prediction
                        ? "Fraud"
                        : "Legitimate"
                ) +
                "</td>" +

                "<td>" +
                formatDate(transaction.created_at) +
                "</td>";

            table.appendChild(row);
        });

    } catch (error) {

        console.error(
            "Transactions error:",
            error
        );
    }
}


// ========================================================
// HELPERS
// ========================================================

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {
        element.innerText = value;
    }
}


function formatDate(dateString) {

    if (!dateString) {
        return "-";
    }

    const date =
        new Date(dateString);

    if (isNaN(date.getTime())) {
        return dateString;
    }

    return date.toLocaleString();
}


function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ========================================================
// YES → BIOMETRIC
// ========================================================

 function showBiometricVerification() {

    const recovery =
        document.getElementById(
            "recoveryVerification"
        );

    const biometric =
        document.getElementById(
            "biometricVerification"
        );

    if (recovery) {
        recovery.classList.add("hidden");
    }

    if (biometric) {

        biometric.classList.remove("hidden");

        biometric.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
}


// ========================================================
// NO → HUMAN REVIEW
// ========================================================

function cancelRecoveryVerification() {

    const recovery =
        document.getElementById(
            "recoveryVerification"
        );

    if (recovery) {
        recovery.classList.add("hidden");
    }

    updateFinalDecision(
        "BLOCK + HUMAN REVIEW",
        "The high-risk transaction remains blocked and requires human review."
    );

    alert(
        "High-risk transaction remains blocked and requires human review."
    );
}
// ========================================================
// FINGERPRINT VERIFICATION
// ========================================================

function startFingerprintDemo() {

    const biometric =
        document.getElementById(
            "biometricVerification"
        );

    const panel =
        document.getElementById(
            "fingerprintPanel"
        );

    const button =
        document.getElementById(
            "fingerprintButton"
        );

    const status =
        document.getElementById(
            "fingerprintStatus"
        );

    const animation =
        document.getElementById(
            "fingerprintAnimation"
        );

    const actions =
        document.getElementById(
            "fingerprintActions"
        );


    if (biometric) {
        biometric.classList.add("hidden");
    }

    if (panel) {
        panel.classList.remove("hidden");

        panel.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }


    if (button) {
        button.disabled = true;
    }

    if (status) {
        status.innerText =
            "Scanning fingerprint...";
    }

    if (animation) {
        animation.innerText = "👆 🔍";
    }


    setTimeout(function () {

        if (button) {
            button.innerText =
                "Fingerprint Scan Completed";
        }

        if (status) {
            status.innerText =
                "Scan completed. Select verification result.";
        }

        if (animation) {
            animation.innerText = "👆";
        }

        if (actions) {
            actions.classList.remove("hidden");
        }

    }, 2000);
}


// ========================================================
// FINGERPRINT PASSED
// ========================================================

function fingerprintPassed() {

    const panel =
        document.getElementById(
            "fingerprintPanel"
        );

    const eyeScan =
        document.getElementById(
            "eyeScanPanel"
        );

    const actions =
        document.getElementById(
            "fingerprintActions"
        );

    if (actions) {
        actions.classList.add("hidden");
    }

    if (panel) {
        panel.classList.add("hidden");
    }

    if (eyeScan) {

        eyeScan.classList.remove("hidden");

        eyeScan.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
}


// ========================================================
// FINGERPRINT FAILED
// ========================================================

function fingerprintFailed() {

    const panel =
        document.getElementById(
            "fingerprintPanel"
        );

    const actions =
        document.getElementById(
            "fingerprintActions"
        );

    if (actions) {
        actions.classList.add("hidden");
    }

    if (panel) {
        panel.classList.add("hidden");
    }

    updateFinalDecision(
        "BLOCK + HUMAN REVIEW",
        "Fingerprint verification failed. The high-risk transaction remains blocked and is sent for human review."
    );

    alert(
        "Fingerprint verification failed. Transaction blocked and sent for human review."
    );
}

// ========================================================
// BIOMETRIC → EYESCAN
// ========================================================

function showEyeScan() {

    const biometric =
        document.getElementById(
            "biometricVerification"
        );

    const eyeScan =
        document.getElementById(
            "eyeScanPanel"
        );

    if (biometric) {
        biometric.classList.add("hidden");
    }

    if (eyeScan) {

        eyeScan.classList.remove("hidden");

        eyeScan.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
}


// ========================================================
// START EYESCAN
// ========================================================

function startEyeScanDemo() {

    const button =
        document.getElementById(
            "startEyeScan"
        );

    const status =
        document.getElementById(
            "scanStatus"
        );

    const animation =
        document.getElementById(
            "scanAnimation"
        );

    const actions =
        document.getElementById(
            "eyeScanActions"
        );


    if (button) {

        button.disabled = true;
        button.innerText = "Scanning...";
    }


    if (status) {
        status.innerText =
            "Scanning biometric pattern...";
    }


    if (animation) {
        animation.innerText = "👁️ 🔍";
    }


    setTimeout(function () {

        if (button) {
            button.innerText =
                "Scan Completed";
        }

        if (status) {
            status.innerText =
                "Scan completed. Select verification result.";
        }

        if (animation) {
            animation.innerText = "👁️";
        }

        if (actions) {
            actions.classList.remove("hidden");
        }

    }, 2000);
}


// ========================================================
// EYESCAN PASS / FAIL
// ========================================================
async function showEyeScanResult(type) {

    const result =
        document.getElementById(
            "scanResult"
        );

    const status =
        document.getElementById(
            "scanStatus"
        );

    const animation =
        document.getElementById(
            "scanAnimation"
        );

    const actions =
        document.getElementById(
            "eyeScanActions"
        );


    if (!result) {

        alert(
            "EyeScan result panel not found."
        );

        return;
    }


    /*
     * Get the transaction ID from the
     * result displayed on the dashboard.
     */
    const transactionId =
        document.getElementById(
            "transactionId"
        )?.innerText;


    if (!transactionId || transactionId === "-") {

        alert(
            "Transaction ID not found."
        );

        return;
    }


    let finalDecision;


    // ========================================================
    // EYESCAN PASSED
    // ========================================================

    if (type === "pass") {

        finalDecision =
            "ALLOW_WITH_MONITORING";

        result.innerHTML =
            "<strong>✅ EyeScan Passed</strong><br>" +
            "Biometric verification successful.<br><br>" +
            "<strong>Final Action: ALLOW WITH MONITORING</strong>";

        if (status) {

            status.innerText =
                "Biometric verification passed.";
        }

        if (animation) {

            animation.innerText =
                "👁️ ✅";
        }

        updateFinalDecision(
            "ALLOW WITH MONITORING",
            "Fingerprint and EyeScan verification passed. The high-risk transaction is allowed with continuous monitoring."
        );
    }


    // ========================================================
    // EYESCAN FAILED
    // ========================================================

    else {

        finalDecision =
            "BLOCK_AND_REVIEW";

        result.innerHTML =
            "<strong>❌ EyeScan Failed</strong><br>" +
            "Biometric verification unsuccessful.<br><br>" +
            "<strong>Final Action: BLOCK + HUMAN REVIEW</strong>";

        if (status) {

            status.innerText =
                "Biometric verification failed.";
        }

        if (animation) {

            animation.innerText =
                "👁️ ❌";
        }

        updateFinalDecision(
            "BLOCK + HUMAN REVIEW",
            "EyeScan verification failed. The high-risk transaction remains blocked and is sent for human review."
        );
    }


    // ========================================================
    // SAVE FINAL DECISION TO DATABASE
    // ========================================================

    try {

        const response =
            await fetch(
                API_BASE_URL +
                "/api/transactions/" +
                transactionId +
                "/final-decision",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        decision:
                            finalDecision
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Could not save final decision."
            );
        }


        console.log(
            "Final biometric decision saved:",
            data
        );


        if (actions) {

            actions.classList.add(
                "hidden"
            );
        }


        // Refresh dashboard so the
        // Recent Transactions table
        // shows the new action.

        loadDashboardStats();

        loadTransactions();


    } catch (error) {

        console.error(
            "Final decision error:",
            error
        );

        alert(
            "Final decision could not be saved: " +
            error.message
        );
    }
}


   