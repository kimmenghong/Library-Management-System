(function () {
    "use strict";

    const dataElement = document.getElementById("dashboard-chart-data");
    if (!dataElement) return;

    if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });

    if (!window.Chart) {
        document.querySelectorAll(".chart-unavailable").forEach((item) => {
            item.hidden = false;
        });
        return;
    }

    const charts = JSON.parse(dataElement.textContent);
    const palette = ["#16794b", "#2867a8", "#c43d4f", "#d9822b", "#7a58a5"];
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 350 },
        plugins: {
            legend: { display: false },
            tooltip: { intersect: false },
        },
    };

    new window.Chart(document.getElementById("monthlyBorrowChart"), {
        type: "line",
        data: {
            labels: charts.monthly.labels,
            datasets: [{
                label: "Loans",
                data: charts.monthly.values,
                borderColor: "#2867a8",
                backgroundColor: "rgba(40, 103, 168, 0.10)",
                borderWidth: 2,
                pointRadius: 3,
                tension: 0.25,
                fill: true,
            }],
        },
        options: {
            ...commonOptions,
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    });

    new window.Chart(document.getElementById("copyStatusChart"), {
        type: "doughnut",
        data: {
            labels: charts.copy_status.labels,
            datasets: [{ data: charts.copy_status.values, backgroundColor: palette, borderWidth: 0 }],
        },
        options: {
            ...commonOptions,
            cutout: "68%",
        },
    });

    new window.Chart(document.getElementById("categoryChart"), {
        type: "bar",
        data: {
            labels: charts.categories.labels,
            datasets: [{ data: charts.categories.values, backgroundColor: "#16794b", borderRadius: 3 }],
        },
        options: {
            ...commonOptions,
            indexAxis: "y",
            scales: {
                x: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#edf1f5" } },
                y: { grid: { display: false } },
            },
        },
    });
})();
