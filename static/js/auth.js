// Auth page logic for index.html

// If already logged in, go straight to the dashboard.
if (getToken()) {
    window.location.href = "/dashboard";
}

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const btnShowLogin = document.getElementById("btn-show-login");
const btnShowRegister = document.getElementById("btn-show-register");
const messageArea = document.getElementById("message-area");
const loginSubmit = document.getElementById("login-submit");
const registerSubmit = document.getElementById("register-submit");

function showMessage(text, isError) {
    messageArea.textContent = text;
    messageArea.className = "message-area " + (isError ? "message-error" : "message-success");
}

function clearMessage() {
    messageArea.textContent = "";
    messageArea.className = "message-area";
}

function showLogin() {
    loginForm.style.display = "";
    registerForm.style.display = "none";
    btnShowLogin.classList.add("active");
    btnShowLogin.setAttribute("aria-selected", "true");
    btnShowRegister.classList.remove("active");
    btnShowRegister.setAttribute("aria-selected", "false");
    clearMessage();
}

function showRegister() {
    loginForm.style.display = "none";
    registerForm.style.display = "";
    btnShowLogin.classList.remove("active");
    btnShowLogin.setAttribute("aria-selected", "false");
    btnShowRegister.classList.add("active");
    btnShowRegister.setAttribute("aria-selected", "true");
    clearMessage();
}

btnShowLogin.addEventListener("click", showLogin);
btnShowRegister.addEventListener("click", showRegister);

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessage();
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;

    if (!username || !password) {
        showMessage("Please enter your username and password.", true);
        return;
    }

    loginSubmit.disabled = true;
    loginSubmit.textContent = "Logging in...";
    try {
        const data = await apiRequest("POST", "/api/auth/login", { username, password });
        setToken(data.access_token);
        window.location.href = "/dashboard";
    } catch (err) {
        showMessage(err.message, true);
    } finally {
        loginSubmit.disabled = false;
        loginSubmit.textContent = "Login";
    }
});

registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessage();
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-password").value;
    const confirm = document.getElementById("reg-confirm").value;

    if (!username || !password) {
        showMessage("Please fill in all fields.", true);
        return;
    }

    if (password !== confirm) {
        showMessage("Passwords do not match.", true);
        return;
    }

    registerSubmit.disabled = true;
    registerSubmit.textContent = "Creating account...";
    try {
        await apiRequest("POST", "/api/auth/register", { username, password });
        showLogin();
        showMessage("Account created. You can now log in.", false);
    } catch (err) {
        showMessage(err.message, true);
    } finally {
        registerSubmit.disabled = false;
        registerSubmit.textContent = "Create account";
    }
});
