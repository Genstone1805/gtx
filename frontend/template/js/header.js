// Header Component - Dynamically generates navigation based on auth status and page type

const Header = {
  // Determine current page type based on URL
  getPageType() {
    const path = window.location.pathname;
    if (path.includes("/admin/")) return "admin";
    if (path.includes("/auth/")) return "auth";
    if (path.includes("/profile/") || path.includes("/credentials/"))
      return "user";
    return "public";
  },

  // Get current page name for active state
  getCurrentPage() {
    const path = window.location.pathname;
    const filename = path.split("/").pop().replace(".html", "");
    return filename || "index";
  },

  // Check if user is logged in
  isLoggedIn() {
    return !!localStorage.getItem("access_token");
  },

  // Check if user is admin (cached from last API call)
  isAdmin() {
    const user = localStorage.getItem("user");
    if (user) {
      try {
        return JSON.parse(user).is_staff === true;
      } catch (e) {
        return false;
      }
    }
    return false;
  },

  // Generate navigation links based on context
  getNavLinks() {
    const pageType = this.getPageType();
    const currentPage = this.getCurrentPage();
    const isLoggedIn = this.isLoggedIn();

    // Public/Auth pages - not logged in
    if (!isLoggedIn) {
      return [
        { href: "../index.html", label: "Home", id: "index" },
        { href: "../auth/login.html", label: "Login", id: "login" },
        { href: "../auth/signup.html", label: "Sign Up", id: "signup" },
      ];
    }

    // Admin pages
    if (pageType === "admin") {
      return [
        { href: "dashboard.html", label: "Dashboard", id: "dashboard" },
        {
          href: "pending-level2.html",
          label: "Level 2 Approvals",
          id: "pending-level2",
        },
        {
          href: "pending-level3.html",
          label: "Level 3 Approvals",
          id: "pending-level3",
        },
        {
          href: "../create-gift-store.html",
          label: "Gift Cards",
          id: "gift-cards",
        },
        {
          href: "../profile/dashboard.html",
          label: "My Profile",
          id: "my-profile",
        },
        { href: "#", label: "Logout", id: "logout", onclick: "logout()" },
      ];
    }

    // User pages (profile, credentials)
    const userLinks = [
      {
        href: "../profile/dashboard.html",
        label: "Dashboard",
        id: "dashboard",
      },
      {
        href: "../profile/transaction-pin.html",
        label: "Transaction PIN",
        id: "transaction-pin",
      },
      {
        href: "../profile/profile-picture.html",
        label: "Profile Picture",
        id: "profile-picture",
      },
      {
        href: "../credentials/level2.html",
        label: "Upgrade Account",
        id: "level2",
      },
    ];

    // Add admin link if user is admin
    if (this.isAdmin()) {
      userLinks.push({
        href: "../admin/dashboard.html",
        label: "Admin Panel",
        id: "admin",
      });
    }

    userLinks.push({
      href: "#",
      label: "Logout",
      id: "logout",
      onclick: "logout()",
    });

    return userLinks;
  },

  // Render the header
  render() {
    const currentPage = this.getCurrentPage();
    const links = this.getNavLinks();
    const isLoggedIn = this.isLoggedIn();

    const navLinksHtml = links
      .map((link) => {
        const isActive =
          link.id === currentPage ||
          (currentPage === "level3" && link.id === "level2"); // level3 is under upgrade
        const activeClass = isActive ? "active" : "";
        const onclick = link.onclick ? `onclick="${link.onclick}"` : "";
        return `<a href="${link.href}" class="${activeClass}" ${onclick}>${link.label}</a>`;
      })
      .join("");

    const headerHtml = `
            <nav class="nav" id="mainNav">
                <a href="${isLoggedIn ? "../profile/dashboard.html" : "../index.html"}" class="nav-brand">GTX</a>
                <button class="nav-toggle" onclick="Header.toggleMobile()">☰</button>
                <div class="nav-links" id="navLinks">
                    ${navLinksHtml}
                </div>
            </nav>
        `;

    // Insert header at the beginning of the container or body
    const container = document.querySelector(".container") || document.body;
    container.insertAdjacentHTML("afterbegin", headerHtml);
  },

  // Toggle mobile menu
  toggleMobile() {
    const navLinks = document.getElementById("navLinks");
    navLinks.classList.toggle("mobile-open");
  },

  // Close mobile menu when clicking outside
  initMobileClose() {
    document.addEventListener("click", (e) => {
      const navLinks = document.getElementById("navLinks");
      const navToggle = document.querySelector(".nav-toggle");
      if (
        navLinks &&
        navToggle &&
        !navLinks.contains(e.target) &&
        !navToggle.contains(e.target)
      ) {
        navLinks.classList.remove("mobile-open");
      }
    });
  },

  // Initialize header
  init() {
    // Wait for DOM to be ready
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => {
        this.render();
        this.initMobileClose();
      });
    } else {
      this.render();
      this.initMobileClose();
    }
  },
};

// Auto-initialize header
Header.init();
