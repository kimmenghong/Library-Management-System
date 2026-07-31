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

    const categoryStyles = {
        Adventure: ["#0369a1", "#f59e0b"],
        Biography: ["#374151", "#b45309"],
        Comedy: ["#f97316", "#ec4899"],
        "Computer Science": ["#1d4ed8", "#0f766e"],
        "Children's Literature": ["#ec4899", "#22c55e"],
        Drama: ["#7c2d12", "#be185d"],
        Fantasy: ["#581c87", "#047857"],
        Fiction: ["#1e40af", "#7c3aed"],
        Finance: ["#065f46", "#0ea5e9"],
        History: ["#713f12", "#334155"],
        Horror: ["#111827", "#7f1d1d"],
        Memoir: ["#4b5563", "#2563eb"],
        Mystery: ["#312e81", "#0f172a"],
        Productivity: ["#0f766e", "#2563eb"],
        Romance: ["#be185d", "#fb7185"],
        "Science Fiction": ["#172554", "#7c3aed"],
        "Self-Help": ["#0f766e", "#84cc16"],
    };

    const escapeSvgText = (value) =>
        String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");

    const wrapCoverTitle = (title) => {
        const words = title.split(/\s+/);
        const lines = [];
        let current = "";

        words.forEach((word) => {
            const next = current ? `${current} ${word}` : word;
            if (next.length > 16 && current) {
                lines.push(current);
                current = word;
            } else {
                current = next;
            }
        });
        if (current) {
            lines.push(current);
        }
        return lines.slice(0, 4);
    };

    const buildCoverSvg = (book, index) => {
        const [first, second] = categoryStyles[book.category] || ["#334155", "#0f766e"];
        const titleLines = wrapCoverTitle(book.title);
        const titleMarkup = titleLines
            .map(
                (line, lineIndex) =>
                    `<text x="34" y="${310 + lineIndex * 38}" fill="#fff" font-family="Arial, sans-serif" font-size="30" font-weight="800">${escapeSvgText(line)}</text>`
            )
            .join("");
        const category = escapeSvgText(book.category);
        const number = String(index + 1).padStart(2, "0");
        const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 500" role="img" aria-label="${escapeSvgText(book.title)} cover">
                <defs>
                    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
                        <stop stop-color="${first}"/>
                        <stop offset="1" stop-color="${second}"/>
                    </linearGradient>
                    <radialGradient id="r" cx="68%" cy="18%" r="60%">
                        <stop stop-color="rgba(255,255,255,.34)"/>
                        <stop offset=".55" stop-color="rgba(255,255,255,.08)"/>
                        <stop offset="1" stop-color="rgba(255,255,255,0)"/>
                    </radialGradient>
                </defs>
                <rect width="360" height="500" rx="28" fill="url(#g)"/>
                <rect x="24" y="28" width="312" height="444" rx="22" fill="rgba(255,255,255,.1)" stroke="rgba(255,255,255,.28)"/>
                <circle cx="270" cy="88" r="86" fill="url(#r)"/>
                <path d="M92 176c42-38 84-54 126-48 34 5 58 25 72 60-40-22-80-23-120-4-32 15-58 38-78 70z" fill="none" stroke="rgba(255,255,255,.86)" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M84 246h190M92 270h152M102 138h.1M268 220h.1" stroke="rgba(255,255,255,.76)" stroke-width="12" stroke-linecap="round"/>
                <text x="34" y="74" fill="rgba(255,255,255,.82)" font-family="Arial, sans-serif" font-size="18" font-weight="700" letter-spacing="1.8">${category}</text>
                <text x="286" y="74" fill="rgba(255,255,255,.82)" font-family="Arial, sans-serif" font-size="18" font-weight="800">${number}</text>
                ${titleMarkup}
                <text x="34" y="456" fill="rgba(255,255,255,.78)" font-family="Arial, sans-serif" font-size="16">${category}</text>
            </svg>`;
        return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
    };

    const renderBookRowCovers = () => {
        document.querySelectorAll("[data-book-cover-row]").forEach((row, index) => {
            const image = row.querySelector("[data-book-cover-image]");
            if (!image) {
                return;
            }
            if (image.getAttribute("src")) {
                return;
            }
            const title = row.dataset.bookTitle || "Library Book";
            const category = row.dataset.bookCategory || "Library";
            image.src = buildCoverSvg({ title, category }, index);
            image.alt = `${title} cover`;
        });
    };

    const renderBookFormPreview = () => {
        const preview = document.querySelector("[data-book-form-preview]");
        if (!preview) {
            return;
        }

        const titleInput = document.querySelector("#id_title");
        const categorySelect = document.querySelector("#id_category");
        const image = preview.querySelector("[data-book-form-cover]");
        const titleText = preview.querySelector("[data-book-form-title]");
        const categoryText = preview.querySelector("[data-book-form-category]");

        const selectedCategoryText = () => {
            const selected = categorySelect && categorySelect.selectedOptions
                ? categorySelect.selectedOptions[0]
                : null;
            const value = selected ? selected.textContent.trim() : "";
            return value || "Library";
        };

        const updatePreview = () => {
            const title = titleInput && titleInput.value.trim()
                ? titleInput.value.trim()
                : "New Library Book";
            const category = selectedCategoryText();

            if (image) {
                image.src = buildCoverSvg({ title, category }, 0);
                image.alt = `${title} cover preview`;
            }
            if (titleText) {
                titleText.textContent = title;
            }
            if (categoryText) {
                categoryText.textContent = `${category} cover style`;
            }
        };

        if (titleInput) {
            titleInput.addEventListener("input", updatePreview);
        }
        if (categorySelect) {
            categorySelect.addEventListener("change", updatePreview);
        }
        updatePreview();
    };

    renderBookRowCovers();
    renderBookFormPreview();

    document.querySelectorAll("[data-print-page]").forEach((button) => {
        button.addEventListener("click", () => {
            window.print();
        });
    });
});
