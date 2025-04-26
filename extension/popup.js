document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("callBtn");
    btn.onclick = async () => {
        try {
            const res = await fetch("/call", { method: "POST" });
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