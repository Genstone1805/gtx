// API Configuration
const API_BASE_URL = "http://92.113.29.160:8000";

// Token management
const TokenManager = {
  getAccessToken: () => localStorage.getItem("access_token"),
  getRefreshToken: () => localStorage.getItem("refresh_token"),
  setTokens: (access, refresh) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  },
  clearTokens: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
  },
  getUser: () => {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  },
  setUser: (user) => {
    localStorage.setItem("user", JSON.stringify(user));
  },
};

// API helper functions
const api = {
  // Make authenticated request
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = options.headers || {};

    // Add auth token if available
    const token = TokenManager.getAccessToken();
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // Don't set Content-Type for FormData (browser will set it with boundary)
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
    }

    const config = {
      ...options,
      headers,
    };

    try {
      let response = await fetch(url, config);

      // If unauthorized, try to refresh token
      if (response.status === 401 && TokenManager.getRefreshToken()) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          headers["Authorization"] = `Bearer ${TokenManager.getAccessToken()}`;
          response = await fetch(url, { ...config, headers });
        }
      }

      return response;
    } catch (error) {
      console.error("API request failed:", error);
      throw error;
    }
  },

  // Refresh access token
  async refreshToken() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/account/token/refresh/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: TokenManager.getRefreshToken() }),
        },
      );

      if (response.ok) {
        const data = await response.json();
        TokenManager.setTokens(data.access, TokenManager.getRefreshToken());
        return true;
      } else {
        TokenManager.clearTokens();
        return false;
      }
    } catch (error) {
      TokenManager.clearTokens();
      return false;
    }
  },

  // Auth endpoints
  async signup(email, password, fullName = "") {
    return this.request("/api/account/signup/", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  },

  async verifyEmail(email, code) {
    return this.request("/api/account/signup/verify/", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    });
  },

  async resendCode(email) {
    return this.request("/api/account/signup/resend-code/", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  async login(email, password) {
    return this.request("/api/account/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async requestPasswordReset(email) {
    return this.request("/api/account/password/reset/", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  async verifyPasswordReset(email, code, newPassword) {
    return this.request("/api/account/password/reset/verify/", {
      method: "POST",
      body: JSON.stringify({ email, code, new_password: newPassword }),
    });
  },

  // Profile endpoints
  async getCurrentUser() {
    return this.request("/api/account/me/");
  },

  async getUserById(userId) {
    return this.request(`/api/account/user/${userId}/`);
  },

  async uploadProfilePicture(file) {
    const formData = new FormData();
    formData.append("dp", file);
    return this.request("/api/account/profile/picture/upload/", {
      method: "POST",
      body: formData,
    });
  },

  async updateProfilePicture(file) {
    const formData = new FormData();
    formData.append("dp", file);
    return this.request("/api/account/profile/picture/update/", {
      method: "POST",
      body: formData,
    });
  },

  // Transaction PIN endpoints
  async createTransactionPin(pin, confirmPin) {
    return this.request("/api/account/pin/create/", {
      method: "POST",
      body: JSON.stringify({ pin, confirm_pin: confirmPin }),
    });
  },

  async updateTransactionPin(oldPin, newPin, confirmNewPin) {
    return this.request("/api/account/pin/update/", {
      method: "POST",
      body: JSON.stringify({
        old_pin: oldPin,
        new_pin: newPin,
        confirm_new_pin: confirmNewPin,
      }),
    });
  },

  // Level credentials endpoints
  async submitLevel2Credentials(nin, ninImage) {
    const formData = new FormData();
    formData.append("nin", nin);
    formData.append("nin_image", ninImage);
    return this.request("/api/account/credentials/level2/", {
      method: "POST",
      body: formData,
    });
  },

  async submitLevel3Credentials(data) {
    const formData = new FormData();
    formData.append("house_address_1", data.houseAddress1);
    formData.append("house_address_2", data.houseAddress2 || "");
    formData.append("nearest_bus_stop", data.nearestBusStop);
    formData.append("city", data.city);
    formData.append("state", data.state);
    formData.append("country", data.country);
    formData.append("proof_of_address_image", data.proofOfAddressImage);
    formData.append("face_verification_image", data.faceVerificationImage);
    return this.request("/api/account/credentials/level3/", {
      method: "POST",
      body: formData,
    });
  },

  // Admin endpoints
  async getPendingLevel2Credentials() {
    return this.request("/api/admin/pending/level2/");
  },

  async getPendingLevel3Credentials() {
    return this.request("/api/admin/pending/level3/");
  },

  async approveLevel2Credential(credentialId, action) {
    return this.request(`/api/admin/approve/level2/${credentialId}/`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
  },

  async approveLevel3Credential(credentialId, action) {
    return this.request(`/api/admin/approve/level3/${credentialId}/`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
  },
};

// UI Helper functions
const UI = {
  showAlert(container, message, type = "error") {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    // Remove existing alerts
    const existingAlerts = container.querySelectorAll(".alert");
    existingAlerts.forEach((alert) => alert.remove());

    container.insertBefore(alertDiv, container.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => alertDiv.remove(), 5000);
  },

  showLoader(button) {
    button.disabled = true;
    button.dataset.originalText = button.textContent;
    button.innerHTML = '<span class="loader"></span> Loading...';
  },

  hideLoader(button) {
    button.disabled = false;
    button.textContent = button.dataset.originalText || "Submit";
  },

  formatCurrency(amount) {
    return new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
    }).format(amount);
  },

  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString("en-NG", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },
};

// Check if user is logged in
function requireAuth() {
  if (!TokenManager.getAccessToken()) {
    window.location.href = "auth/login";
    return false;
  }
  return true;
}

// Check if user is admin
async function requireAdmin() {
  if (!requireAuth()) return false;

  try {
    const response = await api.getCurrentUser();
    if (response.ok) {
      const user = await response.json();
      if (!user.is_staff) {
        window.location.href = "profile/dashboard";
        return false;
      }
      return true;
    }
  } catch (error) {
    console.error("Admin check failed:", error);
  }
  return false;
}

// Logout function
function logout() {
  TokenManager.clearTokens();
  window.location.href = "auth/login";
}
