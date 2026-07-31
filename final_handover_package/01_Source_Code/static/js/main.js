document.addEventListener("DOMContentLoaded", () => {
    const showToast = (message) => {
        const toast = document.createElement("div");
        toast.className = "ui-toast";
        toast.setAttribute("role", "status");
        toast.textContent = message;
        document.body.appendChild(toast);
        window.setTimeout(() => toast.classList.add("is-visible"), 20);
        window.setTimeout(() => {
            toast.classList.remove("is-visible");
            window.setTimeout(() => toast.remove(), 200);
        }, 2800);
    };

    const applyTheme = (theme) => {
        document.documentElement.dataset.theme = theme;
        document.documentElement.setAttribute("data-bs-theme", theme);
        localStorage.setItem("library-theme", theme);
        document.querySelectorAll("[data-theme-icon]").forEach((icon) => {
            icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
        });
    };

    applyTheme(localStorage.getItem("library-theme") || "light");

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            applyTheme(nextTheme);
        });
    });

    document.querySelectorAll("[data-sidebar-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            document.body.classList.toggle("sidebar-open");
        });
    });

    document.querySelectorAll("[data-auto-submit]").forEach((element) => {
        element.addEventListener("change", () => element.form.submit());
    });

    document.querySelectorAll("[data-confirm]").forEach((element) => {
        element.addEventListener("click", (event) => {
            if (!window.confirm(element.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            form.classList.add("is-loading");
            form.querySelectorAll("button[type='submit']").forEach((button) => {
                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.innerHTML = "<span class='spinner-border spinner-border-sm me-2' aria-hidden='true'></span>Working...";
            });
        });
    });

    document.querySelectorAll("[data-table-search]").forEach((input) => {
        const table = document.querySelector(input.dataset.tableSearch);
        if (!table) {
            return;
        }
        const rows = Array.from(table.querySelectorAll("tbody tr"));
        input.addEventListener("input", () => {
            const term = input.value.trim().toLowerCase();
            rows.forEach((row) => {
                const isEmptyRow = row.querySelector(".empty-state");
                if (isEmptyRow) {
                    return;
                }
                row.classList.toggle("d-none", term && !row.textContent.toLowerCase().includes(term));
            });
        });
    });

    document.querySelectorAll("[data-global-search]").forEach((input) => {
        const shell = input.closest(".global-search");
        const results = document.querySelector("[data-global-search-results]");
        if (!shell || !results) {
            return;
        }
        const items = Array.from(results.querySelectorAll("[data-search-item]"));
        const empty = results.querySelector("[data-global-search-empty]");

        const filterResults = () => {
            const term = input.value.trim().toLowerCase();
            let visibleCount = 0;

            items.forEach((item) => {
                const text = (item.dataset.searchText || item.textContent).toLowerCase();
                const isVisible = !term || text.includes(term);
                item.classList.toggle("d-none", !isVisible);
                if (isVisible) {
                    visibleCount += 1;
                }
            });

            if (empty) {
                empty.classList.toggle("d-none", visibleCount !== 0);
            }
            shell.classList.toggle("is-open", document.activeElement === input || Boolean(term));
        };

        input.addEventListener("focus", filterResults);
        input.addEventListener("input", filterResults);
        input.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                input.value = "";
                shell.classList.remove("is-open");
            }
        });
        document.addEventListener("click", (event) => {
            if (!shell.contains(event.target)) {
                shell.classList.remove("is-open");
            }
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) {
            const input = document.querySelector("[data-global-search]");
            if (input) {
                event.preventDefault();
                input.focus();
            }
        }
    });

    const unreadCount = document.querySelectorAll("[data-notification-item].is-unread").length;
    document.querySelectorAll("[data-unread-counter]").forEach((counter) => {
        counter.textContent = unreadCount;
        counter.classList.toggle("d-none", unreadCount === 0);
    });

    const storedAvatar = localStorage.getItem("library-avatar-preview");
    if (storedAvatar) {
        document.querySelectorAll("[data-avatar-preview]").forEach((preview) => {
            preview.innerHTML = `<img src="${storedAvatar}" alt="">`;
        });
    }

    document.querySelectorAll("[data-avatar-input]").forEach((input) => {
        input.addEventListener("change", () => {
            const file = input.files && input.files[0];
            if (!file || !file.type.startsWith("image/")) {
                return;
            }
            const reader = new FileReader();
            reader.addEventListener("load", () => {
                localStorage.setItem("library-avatar-preview", reader.result);
                document.querySelectorAll("[data-avatar-preview]").forEach((preview) => {
                    preview.innerHTML = `<img src="${reader.result}" alt="">`;
                });
                showToast("Profile photo preview updated.");
            });
            reader.readAsDataURL(file);
        });
    });

    document.querySelectorAll("[data-ui-toast]").forEach((button) => {
        button.addEventListener("click", () => showToast(button.dataset.uiToast));
    });

    const tableText = (cell) => (cell ? cell.textContent.trim().replace(/\s+/g, " ") : "");

    const applyColumnFilters = (table) => {
        const filters = Array.from(table.querySelectorAll(".column-filter-row input"));
        const rows = Array.from(table.querySelectorAll("tbody tr"));

        rows.forEach((row) => {
            if (row.querySelector(".empty-state")) {
                return;
            }
            const isVisible = filters.every((filter) => {
                const term = filter.value.trim().toLowerCase();
                if (!term) {
                    return true;
                }
                const cell = row.children[Number(filter.dataset.columnIndex)];
                return tableText(cell).toLowerCase().includes(term);
            });
            row.classList.toggle("d-none", !isVisible);
        });
    };

    const ensureColumnFilters = (table) => {
        let filterRow = table.querySelector(".column-filter-row");
        if (filterRow) {
            return filterRow;
        }

        filterRow = document.createElement("tr");
        filterRow.className = "column-filter-row d-none";
        table.querySelectorAll("thead tr:first-child th").forEach((header, index) => {
            const cell = document.createElement("th");
            const input = document.createElement("input");
            input.className = "form-control form-control-sm";
            input.type = "search";
            input.placeholder = `Filter ${header.textContent.trim() || "column"}`;
            input.dataset.columnIndex = index;
            input.addEventListener("input", () => applyColumnFilters(table));
            cell.appendChild(input);
            filterRow.appendChild(cell);
        });
        table.querySelector("thead").appendChild(filterRow);
        return filterRow;
    };

    document.querySelectorAll("[data-enhanced-table]").forEach((table) => {
        table.querySelectorAll("thead tr:first-child th").forEach((header, index) => {
            if (header.classList.contains("text-end")) {
                return;
            }
            header.setAttribute("tabindex", "0");
            header.setAttribute("role", "button");
            header.setAttribute("aria-sort", "none");
            const sortTable = () => {
                const current = header.getAttribute("aria-sort");
                const direction = current === "ascending" ? "descending" : "ascending";
                const rows = Array.from(table.querySelectorAll("tbody tr")).filter(
                    (row) => !row.querySelector(".empty-state")
                );

                rows.sort((a, b) => {
                    const first = tableText(a.children[index]).toLowerCase();
                    const second = tableText(b.children[index]).toLowerCase();
                    const firstNumber = Number(first.replace(/[^0-9.-]/g, ""));
                    const secondNumber = Number(second.replace(/[^0-9.-]/g, ""));
                    const bothNumeric = !Number.isNaN(firstNumber) && !Number.isNaN(secondNumber);
                    const comparison = bothNumeric
                        ? firstNumber - secondNumber
                        : first.localeCompare(second);
                    return direction === "ascending" ? comparison : comparison * -1;
                });

                table.querySelectorAll("thead th").forEach((cell) => cell.setAttribute("aria-sort", "none"));
                header.setAttribute("aria-sort", direction);
                const body = table.querySelector("tbody");
                rows.forEach((row) => body.appendChild(row));
            };

            header.addEventListener("click", sortTable);
            header.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    sortTable();
                }
            });
        });
    });

    const getToolTable = (button) => {
        const group = button.closest("[data-table-tools]");
        return group ? document.querySelector(group.dataset.tableTools) : null;
    };

    document.querySelectorAll("[data-toggle-column-filters]").forEach((button) => {
        button.addEventListener("click", () => {
            const table = getToolTable(button);
            if (!table) {
                return;
            }
            ensureColumnFilters(table).classList.toggle("d-none");
        });
    });

    const exportTable = (table, format) => {
        const rows = Array.from(table.querySelectorAll("tr"))
            .filter((row) => !row.classList.contains("d-none") && !row.querySelector(".empty-state"))
            .map((row) => Array.from(row.children)
                .map((cell) => `"${tableText(cell).replace(/"/g, '""')}"`)
                .join(","))
            .join("\n");

        const extension = format === "excel" ? "xls" : "csv";
        const blob = new Blob([rows], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${table.id || "library-table"}.${extension}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    };

    document.querySelectorAll("[data-export-table]").forEach((button) => {
        button.addEventListener("click", () => {
            const table = getToolTable(button);
            if (!table) {
                return;
            }
            if (button.dataset.exportTable === "pdf") {
                window.print();
                return;
            }
            exportTable(table, button.dataset.exportTable);
        });
    });

    document.querySelectorAll("[data-print-table]").forEach((button) => {
        button.addEventListener("click", () => {
            window.print();
        });
    });

    document.querySelectorAll("[data-public-book-search]").forEach((input) => {
        const list = document.querySelector(input.dataset.publicBookSearch);
        if (!list) {
            return;
        }

        const cards = Array.from(list.querySelectorAll("[data-public-book-card]"));
        const emptyState = document.querySelector("[data-public-book-empty]");

        input.addEventListener("input", () => {
            const term = input.value.trim().toLowerCase();
            let visibleCount = 0;

            cards.forEach((card) => {
                const text = (card.dataset.searchText || card.textContent).toLowerCase();
                const isVisible = !term || text.includes(term);
                card.classList.toggle("d-none", !isVisible);
                if (isVisible) {
                    visibleCount += 1;
                }
            });

            if (emptyState) {
                emptyState.classList.toggle("d-none", visibleCount !== 0);
            }
        });
    });

    document.querySelectorAll("[data-print-page]").forEach((button) => {
        button.addEventListener("click", () => {
            window.print();
        });
    });
});
