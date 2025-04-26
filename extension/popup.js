document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("callBtn");
    btn.onclick = async () => {
        const phone = document.getElementById("phoneInput").value;
        console.log("Phone number:", phone);
        try {
            const res = await fetch("http://localhost:8000/call", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ phone })
            });
            if (res.ok) {
                console.log("Call request sent successfully");
            } else {
                console.error("Call request failed:", res.statusText);
            }
        } catch (err) {
            console.error("Error sending call request:", err);
        }
    };
});