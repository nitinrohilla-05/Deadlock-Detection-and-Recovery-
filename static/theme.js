document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("theme-toggle");
    const html = document.documentElement;
    
    // Check saved theme
    const saved = localStorage.getItem("theme");
    if (saved) {
        html.setAttribute("data-theme", saved);
    }
    
    toggleBtn.addEventListener("click", () => {
        const current = html.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        html.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
    });
});
