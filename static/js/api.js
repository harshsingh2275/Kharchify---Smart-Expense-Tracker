// Shared API helper for Kharchify frontend.

const TOKEN_KEY = "expense_tracker_token";

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
    constructor(message, status, errors = []) {
        super(message);
        this.status = status;
        this.errors = errors;
    }
}

async function apiRequest(method, path, body = null) {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) {
        headers["Authorization"] = "Bearer " + token;
    }

    const options = { method, headers };
    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    let response;
    try {
        response = await fetch(path, options);
    } catch {
        throw new ApiError("Cannot reach the server. Please try again.", 0);
    }

    // 204 No Content has no body
    if (response.status === 204) {
        return null;
    }

    let data;
    try {
        data = await response.json();
    } catch {
        throw new ApiError("Unexpected server response.", response.status);
    }

    if (!response.ok) {
        // 401 on any path except login clears the token and sends user back
        if (response.status === 401 && !path.endsWith("/api/auth/login")) {
            clearToken();
            window.location.href = "/";
            return;
        }

        if (response.status === 422 && data.errors) {
            const msg = data.errors.map(e => e.field + ": " + e.message).join(", ");
            throw new ApiError(msg, 422, data.errors);
        }

        throw new ApiError(data.detail || "An error occurred.", response.status);
    }

    return data;
}
