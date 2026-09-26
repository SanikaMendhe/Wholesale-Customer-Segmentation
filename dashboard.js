/* =========================================================
   ML-BASED WHOLESALE CUSTOMER SEGMENTATION
   Dashboard JavaScript
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       1. SIDEBAR TOGGLE
       ===================================================== */

    const menuButton = document.getElementById("menuButton");
    const sidebar = document.querySelector(".sidebar");

    if (menuButton && sidebar) {

        menuButton.addEventListener("click", function () {

            sidebar.classList.toggle("open");

        });

    }


    /* =====================================================
       2. CLOSE SIDEBAR WHEN CLICKING OUTSIDE
       ===================================================== */

    document.addEventListener("click", function (event) {

        if (!sidebar || !sidebar.classList.contains("open")) {
            return;
        }

        const clickedInsideSidebar =
            sidebar.contains(event.target);

        const clickedMenuButton =
            menuButton && menuButton.contains(event.target);

        if (!clickedInsideSidebar && !clickedMenuButton) {

            sidebar.classList.remove("open");

        }

    });


    /* =====================================================
       3. PASSWORD SHOW / HIDE
       ===================================================== */

    const passwordToggles =
        document.querySelectorAll(".password-toggle");


    passwordToggles.forEach(function (button) {

        button.addEventListener("click", function () {

            const wrapper = button.closest(".password-wrapper");

            if (!wrapper) {
                return;
            }

            const input =
                wrapper.querySelector("input");

            if (!input) {
                return;
            }


            if (input.type === "password") {

                input.type = "text";

                button.textContent = "🙈";

            } else {

                input.type = "password";

                button.textContent = "👁";

            }

        });

    });


    /* =====================================================
       4. FLASH MESSAGE AUTO HIDE
       ===================================================== */

    const flashMessages =
        document.querySelectorAll(".flash-message");


    flashMessages.forEach(function (message) {

        const closeButton =
            message.querySelector(".flash-close");


        if (closeButton) {

            closeButton.addEventListener("click", function () {

                hideFlashMessage(message);

            });

        }


        setTimeout(function () {

            hideFlashMessage(message);

        }, 5000);

    });


    function hideFlashMessage(message) {

        if (!message || message.dataset.hidden === "true") {
            return;
        }

        message.dataset.hidden = "true";

        message.style.transition =
            "opacity 0.3s ease, transform 0.3s ease";

        message.style.opacity = "0";

        message.style.transform =
            "translateX(20px)";


        setTimeout(function () {

            if (message.parentElement) {

                message.parentElement.removeChild(message);

            }

        }, 300);

    }


    /* =====================================================
       5. GLOBAL SEARCH
       ===================================================== */

    const globalSearch =
        document.querySelector(".global-search input");


    if (globalSearch) {

        globalSearch.addEventListener("keydown", function (event) {

            if (event.key !== "Enter") {
                return;
            }

            const searchValue =
                globalSearch.value.trim();


            if (searchValue === "") {
                return;
            }


            /*
             * Customer search page.
             * The Flask route already handles the actual search.
             */

            const customerSearchUrl =
                "/customers";


            window.location.href =
                customerSearchUrl +
                "?search=" +
                encodeURIComponent(searchValue);

        });

    }


    /* =====================================================
       6. DATA TABLE SEARCH
       ===================================================== */

    const tableSearchInputs =
        document.querySelectorAll("[data-table-search]");


    tableSearchInputs.forEach(function (input) {

        const targetSelector =
            input.getAttribute("data-table-search");

        const table =
            document.querySelector(targetSelector);


        if (!table) {
            return;
        }


        const rows =
            table.querySelectorAll("tbody tr");


        input.addEventListener("input", function () {

            const searchText =
                input.value.toLowerCase().trim();


            rows.forEach(function (row) {

                const rowText =
                    row.textContent.toLowerCase();


                if (rowText.includes(searchText)) {

                    row.style.display = "";

                } else {

                    row.style.display = "none";

                }

            });

        });

    });


    /* =====================================================
       7. FILE UPLOAD NAME DISPLAY
       ===================================================== */

    const fileInputs =
        document.querySelectorAll('input[type="file"]');


    fileInputs.forEach(function (input) {

        input.addEventListener("change", function () {

            if (!input.files || input.files.length === 0) {
                return;
            }


            const file =
                input.files[0];


            const fileNameElements =
                document.querySelectorAll(
                    "[data-file-name]"
                );


            fileNameElements.forEach(function (element) {

                element.textContent =
                    file.name;

            });


            const fileSizeElements =
                document.querySelectorAll(
                    "[data-file-size]"
                );


            fileSizeElements.forEach(function (element) {

                element.textContent =
                    formatFileSize(file.size);

            });

        });

    });


    function formatFileSize(bytes) {

        if (bytes === 0) {
            return "0 Bytes";
        }


        const units = [
            "Bytes",
            "KB",
            "MB",
            "GB"
        ];


        const index =
            Math.floor(
                Math.log(bytes) /
                Math.log(1024)
            );


        const size =
            bytes /
            Math.pow(1024, index);


        return size.toFixed(2) +
            " " +
            units[index];

    }


    /* =====================================================
       8. DRAG AND DROP UPLOAD
       ===================================================== */

    const uploadAreas =
        document.querySelectorAll(".upload-area");


    uploadAreas.forEach(function (area) {

        const fileInput =
            area.querySelector('input[type="file"]');


        if (!fileInput) {
            return;
        }


        area.addEventListener(
            "dragover",
            function (event) {

                event.preventDefault();

                area.classList.add("drag-over");

            }
        );


        area.addEventListener(
            "dragleave",
            function () {

                area.classList.remove("drag-over");

            }
        );


        area.addEventListener(
            "drop",
            function (event) {

                event.preventDefault();

                area.classList.remove("drag-over");


                const files =
                    event.dataTransfer.files;


                if (!files || files.length === 0) {
                    return;
                }


                /*
                 * Only use the first selected file.
                 */

                fileInput.files = files;


                fileInput.dispatchEvent(
                    new Event("change")
                );

            }
        );

    });


    /* =====================================================
       9. CSV FILE VALIDATION
       ===================================================== */

    const csvInputs =
        document.querySelectorAll(
            'input[type="file"][accept*="csv"]'
        );


    csvInputs.forEach(function (input) {

        input.addEventListener("change", function () {

            const file =
                input.files[0];


            if (!file) {
                return;
            }


            const fileName =
                file.name.toLowerCase();


            if (!fileName.endsWith(".csv")) {

                alert(
                    "Please select a CSV file."
                );

                input.value = "";

            }

        });

    });


    /* =====================================================
       10. DELETE CONFIRMATION
       ===================================================== */

    const deleteForms =
        document.querySelectorAll(
            "form[data-confirm-delete]"
        );


    deleteForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const message =
                form.getAttribute(
                    "data-confirm-delete"
                ) ||
                "Are you sure you want to delete this item?";


            const confirmed =
                window.confirm(message);


            if (!confirmed) {

                event.preventDefault();

            }

        });

    });


    /* =====================================================
       11. PREVENT DOUBLE FORM SUBMISSION
       ===================================================== */

    const forms =
        document.querySelectorAll("form");


    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            /*
             * Do not disable delete buttons or buttons that
             * already have special behaviour.
             */

            const submitButtons =
                form.querySelectorAll(
                    'button[type="submit"]'
                );


            submitButtons.forEach(function (button) {

                if (
                    button.classList.contains("btn-danger") ||
                    button.dataset.allowMultiple === "true"
                ) {
                    return;
                }


                setTimeout(function () {

                    button.disabled = true;

                    button.style.opacity = "0.7";

                }, 10);

            });

        });

    });


    /* =====================================================
       12. ACTIVE NAVIGATION
       ===================================================== */

    const currentPath =
        window.location.pathname;


    const navigationLinks =
        document.querySelectorAll(
            ".sidebar-nav a"
        );


    navigationLinks.forEach(function (link) {

        const linkPath =
            new URL(
                link.href,
                window.location.origin
            ).pathname;


        if (
            linkPath === currentPath &&
            currentPath !== "/"
        ) {

            link.classList.add("active");

        }

    });


    /* =====================================================
       13. NUMBER ANIMATION
       ===================================================== */

    const animatedNumbers =
        document.querySelectorAll(
            "[data-count]"
        );


    animatedNumbers.forEach(function (element) {

        const target =
            parseFloat(
                element.getAttribute("data-count")
            );


        if (isNaN(target)) {
            return;
        }


        animateNumber(
            element,
            target
        );

    });


    function animateNumber(element, target) {

        const duration = 700;

        const startTime =
            performance.now();


        function update(currentTime) {

            const elapsed =
                currentTime -
                startTime;


            const progress =
                Math.min(
                    elapsed / duration,
                    1
                );


            /*
             * Ease-out animation.
             */

            const eased =
                1 -
                Math.pow(
                    1 - progress,
                    3
                );


            const current =
                target * eased;


            element.textContent =
                Number.isInteger(target)
                    ? Math.round(current)
                    : current.toFixed(2);


            if (progress < 1) {

                requestAnimationFrame(update);

            }

        }


        requestAnimationFrame(update);

    }


    /* =====================================================
       14. SEARCH CUSTOMER - EMPTY INPUT
       ===================================================== */

    const customerSearchForms =
        document.querySelectorAll(
            'form[action*="customer_search"]'
        );


    customerSearchForms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const input =
                form.querySelector(
                    'input[name="search"]'
                );


            if (!input) {
                return;
            }


            if (input.value.trim() === "") {

                event.preventDefault();

                input.focus();

            }

        });

    });


    /* =====================================================
       15. TOOLTIP SUPPORT
       ===================================================== */

    const tooltipElements =
        document.querySelectorAll(
            "[data-tooltip]"
        );


    tooltipElements.forEach(function (element) {

        element.addEventListener(
            "mouseenter",
            function () {

                element.setAttribute(
                    "title",
                    element.getAttribute(
                        "data-tooltip"
                    )
                );

            }
        );

    });


    /* =====================================================
       16. SMOOTH INTERNAL LINKS
       ===================================================== */

    const internalLinks =
        document.querySelectorAll(
            'a[href^="#"]'
        );


    internalLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            const targetId =
                link.getAttribute("href");


            if (
                !targetId ||
                targetId === "#"
            ) {
                return;
            }


            const target =
                document.querySelector(targetId);


            if (!target) {
                return;
            }


            event.preventDefault();


            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        });

    });


    /* =====================================================
       17. CONSOLE INFORMATION
       ===================================================== */

    console.log(
        "ML-Based Wholesale Customer Segmentation Dashboard loaded successfully."
    );

});