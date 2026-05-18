fetch("/save_chat", {
    method: "POST",
    headers: {
        "Content-Type": "application/x-www-form-urlencoded"
    },
    body: "message=" + encodeURIComponent(userMessage)
});