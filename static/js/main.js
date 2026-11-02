/**
 * TaskFlow — Main JavaScript File
 */

// Helper to get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Mobile sidebar controls
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar) {
    sidebar.classList.toggle('open');
    if (overlay) {
      overlay.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
    }
  }
}

function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar) {
    sidebar.classList.remove('open');
  }
  if (overlay) {
    overlay.style.display = 'none';
  }
}

// Auto-hide toast messages
document.addEventListener('DOMContentLoaded', () => {
  const toasts = document.querySelectorAll('.toast-msg');
  toasts.forEach(toast => {
    setTimeout(() => {
      toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  });
});

