// Dashboard page logic for Kharchify.

const PAGE_SIZE = 10;

// State
let currentPage = 0;       // zero-based offset page
let totalExpenses = 0;
let editingExpenseId = null;
let appliedFilters = {};

// DOM refs
const greetingEl = document.getElementById("user-greeting");
const messageArea = document.getElementById("message-area");
const monthPicker = document.getElementById("month-picker");
const statTotal = document.getElementById("stat-total");
const statCount = document.getElementById("stat-count");
const summaryTbody = document.getElementById("summary-tbody");
const summaryEmpty = document.getElementById("summary-empty");
const summaryTable = document.getElementById("summary-table");
const expenseForm = document.getElementById("expense-form");
const editIdField = document.getElementById("edit-expense-id");
const fieldTitle = document.getElementById("field-title");
const fieldAmount = document.getElementById("field-amount");
const fieldCategory = document.getElementById("field-category");
const fieldDate = document.getElementById("field-date");
const fieldNote = document.getElementById("field-note");
const formSubmit = document.getElementById("form-submit");
const btnCancel = document.getElementById("btn-cancel-edit");
const formHeading = document.getElementById("form-heading");
const expenseTbody = document.getElementById("expense-tbody");
const listEmpty = document.getElementById("list-empty");
const pageInfo = document.getElementById("page-info");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const filterCategory = document.getElementById("filter-category");
const filterFrom = document.getElementById("filter-from");
const filterTo = document.getElementById("filter-to");

// ─── Init ──────────────────────────────────────────────────────────────────

if (!getToken()) {
    window.location.href = "/";
}

async function init() {
    // Set date defaults
    const today = new Date().toISOString().slice(0, 10);
    fieldDate.max = today;
    fieldDate.value = today;

    const currentMonth = today.slice(0, 7);
    monthPicker.value = currentMonth;

    try {
        const user = await apiRequest("GET", "/api/auth/me");
        greetingEl.textContent = "Hello, " + user.username;
    } catch (err) {
        showMessage(err.message, true);
        return;
    }

    await loadCategories();
    await loadSummary();
    await loadExpenses();
}

// ─── Messages ──────────────────────────────────────────────────────────────

function showMessage(text, isError) {
    messageArea.textContent = text;
    messageArea.className = "message-area " + (isError ? "message-error" : "message-success");
    // Auto-clear success messages after a few seconds
    if (!isError) {
        setTimeout(() => {
            if (messageArea.textContent === text) {
                messageArea.textContent = "";
                messageArea.className = "message-area";
            }
        }, 4000);
    }
}

function clearMessage() {
    messageArea.textContent = "";
    messageArea.className = "message-area";
}

// ─── Logout ────────────────────────────────────────────────────────────────

document.getElementById("btn-logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "/";
});

// ─── Categories ────────────────────────────────────────────────────────────

async function loadCategories() {
    try {
        const categories = await apiRequest("GET", "/api/categories");
        // Populate form category select
        fieldCategory.innerHTML = "";
        categories.forEach(cat => {
            const opt = document.createElement("option");
            opt.value = cat.id;
            opt.textContent = cat.name;
            fieldCategory.appendChild(opt);
        });

        // Populate filter category select
        filterCategory.innerHTML = "";
        const allOpt = document.createElement("option");
        allOpt.value = "";
        allOpt.textContent = "All";
        filterCategory.appendChild(allOpt);
        categories.forEach(cat => {
            const opt = document.createElement("option");
            opt.value = cat.id;
            opt.textContent = cat.name;
            filterCategory.appendChild(opt);
        });
    } catch (err) {
        showMessage("Could not load categories: " + err.message, true);
    }
}

// ─── Monthly Summary ───────────────────────────────────────────────────────

async function loadSummary() {
    const month = monthPicker.value;
    try {
        const data = await apiRequest("GET", "/api/summary?month=" + month);
        statTotal.textContent = "Rs. " + data.total_spent.toFixed(2);
        statCount.textContent = data.expense_count;

        summaryTbody.innerHTML = "";
        if (data.by_category.length === 0) {
            summaryTable.style.display = "none";
            summaryEmpty.style.display = "";
        } else {
            summaryTable.style.display = "";
            summaryEmpty.style.display = "none";
            data.by_category.forEach(row => {
                const tr = document.createElement("tr");

                const tdName = document.createElement("td");
                tdName.textContent = row.category_name;

                const tdCount = document.createElement("td");
                tdCount.className = "amount-cell";
                tdCount.textContent = row.count;

                const tdTotal = document.createElement("td");
                tdTotal.className = "amount-cell";
                tdTotal.textContent = "Rs. " + row.total.toFixed(2);

                tr.appendChild(tdName);
                tr.appendChild(tdCount);
                tr.appendChild(tdTotal);
                summaryTbody.appendChild(tr);
            });
        }
    } catch (err) {
        showMessage("Could not load summary: " + err.message, true);
    }
}

monthPicker.addEventListener("change", loadSummary);

// ─── Expense List ──────────────────────────────────────────────────────────

async function loadExpenses() {
    const offset = currentPage * PAGE_SIZE;
    const params = new URLSearchParams({ limit: PAGE_SIZE, offset });

    if (appliedFilters.categoryId) params.set("category_id", appliedFilters.categoryId);
    if (appliedFilters.from) params.set("start_date", appliedFilters.from);
    if (appliedFilters.to) params.set("end_date", appliedFilters.to);

    try {
        const data = await apiRequest("GET", "/api/expenses?" + params.toString());
        totalExpenses = data.total;
        renderExpenses(data.items);
        renderPagination();
    } catch (err) {
        showMessage("Could not load expenses: " + err.message, true);
    }
}

function renderExpenses(items) {
    expenseTbody.innerHTML = "";

    if (items.length === 0) {
        listEmpty.style.display = "";
    } else {
        listEmpty.style.display = "none";
    }

    items.forEach(exp => {
        const tr = document.createElement("tr");

        const tdDate = document.createElement("td");
        tdDate.textContent = exp.expense_date;

        const tdTitle = document.createElement("td");
        tdTitle.textContent = exp.title;

        const tdCat = document.createElement("td");
        tdCat.textContent = exp.category_name;

        const tdAmount = document.createElement("td");
        tdAmount.className = "amount-cell";
        tdAmount.textContent = "Rs. " + exp.amount.toFixed(2);

        const tdActions = document.createElement("td");
        tdActions.className = "actions-cell";

        const btnEdit = document.createElement("button");
        btnEdit.className = "btn btn-secondary btn-sm";
        btnEdit.textContent = "Edit";
        btnEdit.addEventListener("click", () => startEdit(exp));

        const btnDelete = document.createElement("button");
        btnDelete.className = "btn btn-danger btn-sm";
        btnDelete.textContent = "Delete";
        btnDelete.addEventListener("click", () => deleteExpense(exp.id));

        tdActions.appendChild(btnEdit);
        tdActions.appendChild(btnDelete);

        tr.appendChild(tdDate);
        tr.appendChild(tdTitle);
        tr.appendChild(tdCat);
        tr.appendChild(tdAmount);
        tr.appendChild(tdActions);
        expenseTbody.appendChild(tr);
    });
}

function renderPagination() {
    const totalPages = Math.max(1, Math.ceil(totalExpenses / PAGE_SIZE));
    pageInfo.textContent = "Page " + (currentPage + 1) + " of " + totalPages;
    btnPrev.disabled = currentPage === 0;
    btnNext.disabled = currentPage >= totalPages - 1;
}

btnPrev.addEventListener("click", () => {
    if (currentPage > 0) {
        currentPage--;
        loadExpenses();
    }
});

btnNext.addEventListener("click", () => {
    const totalPages = Math.ceil(totalExpenses / PAGE_SIZE);
    if (currentPage < totalPages - 1) {
        currentPage++;
        loadExpenses();
    }
});

// ─── Filters ───────────────────────────────────────────────────────────────

document.getElementById("btn-apply-filters").addEventListener("click", () => {
    const from = filterFrom.value;
    const to = filterTo.value;

    if (from && to && from > to) {
        showMessage("'From' date cannot be after 'To' date.", true);
        return;
    }

    clearMessage();
    appliedFilters = {
        categoryId: filterCategory.value || null,
        from: from || null,
        to: to || null,
    };
    currentPage = 0;
    loadExpenses();
});

document.getElementById("btn-clear-filters").addEventListener("click", () => {
    filterCategory.value = "";
    filterFrom.value = "";
    filterTo.value = "";
    appliedFilters = {};
    currentPage = 0;
    clearMessage();
    loadExpenses();
});

// ─── Add / Edit Form ───────────────────────────────────────────────────────

function startEdit(exp) {
    editingExpenseId = exp.id;
    editIdField.value = exp.id;
    fieldTitle.value = exp.title;
    fieldAmount.value = exp.amount;
    fieldCategory.value = exp.category_id;
    fieldDate.value = exp.expense_date;
    fieldNote.value = exp.note || "";

    formHeading.textContent = "Edit Expense";
    formSubmit.textContent = "Save changes";
    btnCancel.style.display = "";

    // Scroll form into view
    expenseForm.scrollIntoView({ behavior: "smooth", block: "start" });
}

function resetForm() {
    editingExpenseId = null;
    editIdField.value = "";
    expenseForm.reset();
    const today = new Date().toISOString().slice(0, 10);
    fieldDate.value = today;

    formHeading.textContent = "Add Expense";
    formSubmit.textContent = "Add expense";
    btnCancel.style.display = "none";
    formSubmit.disabled = false;
}

btnCancel.addEventListener("click", () => {
    resetForm();
    clearMessage();
});

expenseForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessage();

    const title = fieldTitle.value.trim();
    const amount = parseFloat(fieldAmount.value);
    const categoryId = parseInt(fieldCategory.value, 10);
    const date = fieldDate.value;
    const note = fieldNote.value.trim() || null;

    // Basic client-side validation
    if (!title) {
        showMessage("Title is required.", true);
        return;
    }
    if (isNaN(amount) || amount <= 0) {
        showMessage("Amount must be greater than zero.", true);
        return;
    }
    if (!date) {
        showMessage("Date is required.", true);
        return;
    }
    const today = new Date().toISOString().slice(0, 10);
    if (date > today) {
        showMessage("Date cannot be in the future.", true);
        return;
    }

    const payload = {
        title,
        amount,
        category_id: categoryId,
        expense_date: date,
        note,
    };

    formSubmit.disabled = true;

    try {
        if (editingExpenseId) {
            await apiRequest("PUT", "/api/expenses/" + editingExpenseId, payload);
            showMessage("Expense updated.", false);
        } else {
            await apiRequest("POST", "/api/expenses", payload);
            showMessage("Expense added.", false);
        }
        resetForm();
        currentPage = 0;
        await loadExpenses();
        await loadSummary();
    } catch (err) {
        showMessage(err.message, true);
        formSubmit.disabled = false;
    }
});

// ─── Delete ────────────────────────────────────────────────────────────────

async function deleteExpense(expenseId) {
    if (!confirm("Delete this expense?")) {
        return;
    }
    clearMessage();
    try {
        await apiRequest("DELETE", "/api/expenses/" + expenseId);
        showMessage("Expense deleted.", false);
        // Stay on current page unless it no longer has any items
        const newTotal = totalExpenses - 1;
        const maxPage = Math.max(0, Math.ceil(newTotal / PAGE_SIZE) - 1);
        if (currentPage > maxPage) {
            currentPage = maxPage;
        }
        await loadExpenses();
        await loadSummary();
    } catch (err) {
        showMessage(err.message, true);
    }
}

// ─── Start ─────────────────────────────────────────────────────────────────

init();
