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

  // Check initial notification badge on header bell
  checkNotificationBadge();
});

// =====================================================
// Notification Modal Functionality
// =====================================================
function openNotificationModal() {
  const overlay = document.getElementById('notificationModalOverlay');
  if (!overlay) return;

  overlay.classList.add('show');
  document.body.style.overflow = 'hidden';

  fetchNotifications();
}

function closeNotificationModal() {
  const overlay = document.getElementById('notificationModalOverlay');
  if (!overlay) return;

  overlay.classList.remove('show');
  document.body.style.overflow = '';
}

function handleNotificationOverlayClick(event) {
  if (event.target && event.target.id === 'notificationModalOverlay') {
    closeNotificationModal();
  }
}

// Close on Escape key
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    const overlay = document.getElementById('notificationModalOverlay');
    if (overlay && overlay.classList.contains('show')) {
      closeNotificationModal();
    }
  }
});

function checkNotificationBadge() {
  const bellDot = document.getElementById('notificationBadgeDot');
  if (!bellDot) return;

  fetch('/tasks/notifications/', {
    headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
  })
  .then(res => res.ok ? res.json() : null)
  .then(data => {
    if (data && data.count > 0) {
      bellDot.style.display = 'block';
    } else {
      bellDot.style.display = 'none';
    }
  })
  .catch(() => {});
}

async function fetchNotifications() {
  const loading = document.getElementById('notifLoading');
  const empty = document.getElementById('notifEmpty');
  const list = document.getElementById('notifTaskList');
  const countBadge = document.getElementById('notifCountBadge');

  if (loading) loading.style.display = 'block';
  if (empty) empty.style.display = 'none';
  if (list) list.style.display = 'none';

  try {
    const response = await fetch('/tasks/notifications/', {
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to load notifications: ${response.status}`);
    }

    const data = await response.json();
    renderNotifications(data);
  } catch (err) {
    console.error('Error fetching notifications:', err);
    if (loading) loading.style.display = 'none';
    if (empty) {
      empty.innerHTML = `
        <div class="notif-empty-icon" style="background:#FEE2E2;color:#DC2626;">
          <i class="bi bi-exclamation-triangle"></i>
        </div>
        <h5>Unable to load notifications</h5>
        <p>Please try again in a few moments.</p>
      `;
      empty.style.display = 'block';
    }
  }
}

function renderNotifications(data) {
  const loading = document.getElementById('notifLoading');
  const empty = document.getElementById('notifEmpty');
  const list = document.getElementById('notifTaskList');
  const countBadge = document.getElementById('notifCountBadge');
  const bellDot = document.getElementById('notificationBadgeDot');

  if (loading) loading.style.display = 'none';

  const total = data.count || 0;

  // Update header badge
  if (countBadge) {
    countBadge.textContent = total;
    countBadge.style.display = 'inline-flex';
  }

  // Update bell red dot
  if (bellDot) {
    bellDot.style.display = total > 0 ? 'block' : 'none';
  }

  if (total === 0 || !data.tasks || data.tasks.length === 0) {
    if (empty) {
      empty.innerHTML = `
        <div class="notif-empty-icon">
          <i class="bi bi-check2-circle"></i>
        </div>
        <h5>You're all caught up!</h5>
        <p>No pending tasks with due dates right now.</p>
      `;
      empty.style.display = 'block';
    }
    if (list) list.style.display = 'none';
    return;
  }

  if (empty) empty.style.display = 'none';

  let html = '';
  data.tasks.forEach(task => {
    let dueStatusBadgeClass = 'badge-due-upcoming';
    let dueIcon = 'bi-clock';

    if (task.status_badge === 'overdue') {
      dueStatusBadgeClass = 'badge-due-overdue';
      dueIcon = 'bi-exclamation-circle';
    } else if (task.status_badge === 'due_today') {
      dueStatusBadgeClass = 'badge-due-today';
      dueIcon = 'bi-calendar-event';
    }

    const priorityClass = `badge-${escapeHtml(task.priority || 'medium')}`;

    html += `
      <div class="notif-task-card">
        <div class="notif-task-top">
          <div class="notif-task-title">${escapeHtml(task.title)}</div>
          <span class="badge-due-status ${dueStatusBadgeClass}">
            <i class="bi ${dueIcon}"></i> ${escapeHtml(task.status_label)}
          </span>
        </div>
        <div class="notif-task-meta">
          <span class="badge-priority ${priorityClass}">
            ${escapeHtml(task.priority_display || task.priority)}
          </span>
          <span class="notif-task-date">
            <i class="bi bi-calendar3"></i> Due: ${escapeHtml(task.due_date)}
          </span>
        </div>
      </div>
    `;
  });

  if (list) {
    list.innerHTML = html;
    list.style.display = 'flex';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}


