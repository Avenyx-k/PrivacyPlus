/* =========================================
   PRIVACY+ INTERACTIONS
   ========================================= */


/* SIDEBAR */

function toggleSidebar() {

    const sidebar =
        document.getElementById("sidebar");

    if (!sidebar) {
        return;
    }

    if (window.innerWidth <= 850) {

        sidebar.classList.toggle("mobile-open");

    } else {

        sidebar.classList.toggle("collapsed");

    }
}



/* DARK / LIGHT MODE */

function toggleTheme() {

    document.body.classList.toggle("dark-mode");

    if (
        document.body.classList.contains("dark-mode")
    ) {

        localStorage.setItem(
            "privacyTheme",
            "dark"
        );

    } else {

        localStorage.setItem(
            "privacyTheme",
            "light"
        );
    }
}



/* REMEMBER THEME */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const savedTheme =
            localStorage.getItem("privacyTheme");

        if (savedTheme === "dark") {

            document.body.classList.add(
                "dark-mode"
            );

        }

    }
);