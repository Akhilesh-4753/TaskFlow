/**
 * TaskFlow — Task Management & Modals JavaScript
 */

let deleteTaskId = null;

// Multi-fallback CSRF token retriever
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && meta.content && meta.content.length > 10) return meta.content;
  const input = document.querySelector('[name=csrfmiddlewaretoken]');
  if (input && input.value && input.value.length > 10) return input.value;
  if (typeof getCookie === 'function') {
    const c = getCookie('csrftoken');
    if (c) return c;
  }
  return '';
}

// Character counter listeners
document.addEventListener('DOMContentLoaded', () => {
  const createTitle = document.getElementById('create_title');
  const createTitleCount = document.getElementById('create_title_count');
  if (createTitle && createTitleCount) {
    createTitle.addEventListener('input', () => {
      createTitleCount.textContent = createTitle.value.length;
    });
  }

  const createDesc = document.getElementById('create_description');
  const createDescCount = document.getElementById('create_desc_count');
  if (createDesc && createDescCount) {
    createDesc.addEventListener('input', () => {
      createDescCount.textContent = createDesc.value.length;
    });
  }

  const editTitle = document.getElementById('edit_title');
  const editTitleCount = document.getElementById('edit_title_count');
  if (editTitle && editTitleCount) {
    editTitle.addEventListener('input', () => {
      editTitleCount.textContent = editTitle.value.length;
    });
  }

  const editDesc = document.getElementById('edit_description');
  const editDescCount = document.getElementById('edit_desc_count');
  if (editDesc && editDescCount) {
    editDesc.addEventListener('input', () => {
      editDescCount.textContent = editDesc.value.length;
    });
  }

  // Close modals on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCreateModal();
      closeEditModal();
      closeDeleteModal();
    }
  });

  // Close modals on overlay backdrop click
  ['createTaskModal', 'editTaskModal', 'deleteTaskModal'].forEach(modalId => {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          if (modalId === 'createTaskModal') closeCreateModal();
          if (modalId === 'editTaskModal') closeEditModal();
          if (modalId === 'deleteTaskModal') closeDeleteModal();
        }
      });
    }
  });

  // Attach Create Task AJAX form submit
  const createForm = document.getElementById('createTaskForm');
  if (createForm) {
    createForm.addEventListener('submit', handleCreateTaskSubmit);
  }

  // Attach Edit Task AJAX form submit
  const editForm = document.getElementById('editTaskForm');
  if (editForm) {
    editForm.addEventListener('submit', handleEditTaskSubmit);
  }

  // Initialize Select-All checkbox state on page load
  updateSelectAllCheckboxState();
});

// Modal Open / Close functions
function openCreateModal() {
  const modal = document.getElementById('createTaskModal');
  if (modal) {
    modal.classList.add('show');
    const titleInput = document.getElementById('create_title');
    if (titleInput) {
      titleInput.focus();
    }
  }
}

function closeCreateModal() {
  const modal = document.getElementById('createTaskModal');
  if (modal) {
    modal.classList.remove('show');
    const form = document.getElementById('createTaskForm');
    if (form) form.reset();
    const errorBox = document.getElementById('createTaskError');
    if (errorBox) {
      errorBox.style.display = 'none';
      errorBox.textContent = '';
    }
    const titleCount = document.getElementById('create_title_count');
    if (titleCount) titleCount.textContent = '0';
    const descCount = document.getElementById('create_desc_count');
    if (descCount) descCount.textContent = '0';
  }
}

function openEditModal(taskId) {
  const modal = document.getElementById('editTaskModal');
  if (!modal) return;

  // Fetch current task details via AJAX
  fetch(`/tasks/${taskId}/edit/`, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success && data.task) {
      const t = data.task;
      document.getElementById('edit_task_id').value = t.id;
      const titleInput = document.getElementById('edit_title');
      titleInput.value = t.title;
      document.getElementById('edit_title_count').textContent = t.title.length;

      const descInput = document.getElementById('edit_description');
      descInput.value = t.description || '';
      document.getElementById('edit_desc_count').textContent = (t.description || '').length;

      document.getElementById('edit_priority').value = t.priority;
      document.getElementById('edit_due_date').value = t.due_date || '';
      document.getElementById('edit_completed').checked = t.completed;

      modal.classList.add('show');
      titleInput.focus();
    } else {
      alert('Could not load task details.');
    }
  })
  .catch(err => {
    console.error('Error loading task:', err);
    alert('Failed to load task.');
  });
}

function closeEditModal() {
  const modal = document.getElementById('editTaskModal');
  if (modal) {
    modal.classList.remove('show');
    const errorBox = document.getElementById('editTaskError');
    if (errorBox) {
      errorBox.style.display = 'none';
      errorBox.textContent = '';
    }
  }
}

function openDeleteModal(taskId, taskTitle) {
  deleteTaskId = taskId;
  const modal = document.getElementById('deleteTaskModal');
  const titleElem = document.getElementById('deleteTaskTitle');
  if (titleElem) {
    titleElem.textContent = taskTitle || 'Selected Task';
  }
  if (modal) {
    modal.classList.add('show');
  }
}

function closeDeleteModal() {
  deleteTaskId = null;
  const modal = document.getElementById('deleteTaskModal');
  if (modal) {
    modal.classList.remove('show');
  }
}

// Confirm Task Deletion via AJAX
function confirmDelete() {
  if (!deleteTaskId) return;

  const btn = document.getElementById('confirmDeleteBtn');
  if (btn) btn.disabled = true;

  fetch(`/tasks/${deleteTaskId}/delete/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      closeDeleteModal();
      window.location.reload();
    } else {
      alert(data.message || 'Failed to delete task.');
      if (btn) btn.disabled = false;
    }
  })
  .catch(err => {
    console.error('Delete error:', err);
    alert('An error occurred while deleting task.');
    if (btn) btn.disabled = false;
  });
}

// =====================================================
// Task UI Helpers & State Updates
// =====================================================
function updateTaskRowUI(taskId, isCompleted) {
  const row = document.getElementById(`task-row-${taskId}`);
  if (!row) return;

  // Update row checkbox
  const cb = row.querySelector('.row-task-checkbox') || row.querySelector('.task-checkbox');
  if (cb) {
    cb.checked = isCompleted;
    cb.title = isCompleted ? 'Mark as Pending' : 'Mark as Completed';
  }

  // Update title strikethrough
  const titleSpan = row.querySelector('.task-title-cell span');
  if (titleSpan) {
    if (isCompleted) {
      titleSpan.style.textDecoration = 'line-through';
      titleSpan.style.color = 'var(--text-muted)';
    } else {
      titleSpan.style.textDecoration = 'none';
      titleSpan.style.color = '';
    }
  }

  // Update status badge
  const badge = document.getElementById(`task-status-badge-${taskId}`) || row.querySelector('.badge-status');
  if (badge) {
    if (isCompleted) {
      badge.className = 'badge-status badge-completed';
      badge.textContent = 'Completed';
      badge.title = 'Click to toggle status: Completed';
    } else {
      badge.className = 'badge-status badge-pending';
      badge.textContent = 'Pending';
      badge.title = 'Click to toggle status: Pending';
    }
  }
}

function updateSelectAllCheckboxState() {
  const master = document.getElementById('selectAllTasks');
  const rowCheckboxes = document.querySelectorAll('.task-table tbody .row-task-checkbox');
  if (!master || rowCheckboxes.length === 0) return;

  const total = rowCheckboxes.length;
  const checkedCount = Array.from(rowCheckboxes).filter(cb => cb.checked).length;

  master.checked = checkedCount === total && total > 0;
  master.indeterminate = checkedCount > 0 && checkedCount < total;
}

// Toggle single task completion status immediately in UI and Database
function toggleTask(taskId, element) {
  if (!taskId) return;

  const row = document.getElementById(`task-row-${taskId}`);
  const cb = row ? (row.querySelector('.row-task-checkbox') || row.querySelector('.task-checkbox')) : null;

  // Determine target completed state
  let isCompleted;
  if (element && element.type === 'checkbox') {
    isCompleted = element.checked;
  } else if (cb) {
    isCompleted = !cb.checked;
  } else {
    isCompleted = true;
  }

  // Immediate UI update for instant feedback
  updateTaskRowUI(taskId, isCompleted);
  updateSelectAllCheckboxState();

  // Send AJAX request to update status in the database
  const csrf = getCsrfToken();
  fetch(`/tasks/${taskId}/toggle/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrf,
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ completed: isCompleted })
  })
  .then(res => {
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
    return res.json();
  })
  .then(data => {
    if (data.success) {
      // Sync with returned state from database
      updateTaskRowUI(taskId, data.completed);
      updateSelectAllCheckboxState();
      console.log(`[TaskFlow DB] Task ${taskId} status updated in DB: completed=${data.completed}`);
    } else {
      // Revert if database update failed
      updateTaskRowUI(taskId, !isCompleted);
      updateSelectAllCheckboxState();
      alert(data.message || 'Failed to update task status in database.');
    }
  })
  .catch(err => {
    console.error('Toggle DB error:', err);
    updateTaskRowUI(taskId, !isCompleted);
    updateSelectAllCheckboxState();
    alert(`Error updating task status in database: ${err.message}`);
  });
}

// Handle Task Creation Submission
function handleCreateTaskSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById('createSubmitBtn');
  const errorBox = document.getElementById('createTaskError');
  const titleInput = document.getElementById('create_title');

  if (!titleInput.value.trim()) {
    if (errorBox) {
      errorBox.textContent = 'Please enter a task title.';
      errorBox.style.display = 'block';
    }
    titleInput.focus();
    return;
  }

  if (submitBtn) submitBtn.disabled = true;

  const formData = new FormData(form);

  fetch('/tasks/create/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      closeCreateModal();
      window.location.reload();
    } else {
      if (submitBtn) submitBtn.disabled = false;
      if (errorBox) {
        let msg = 'Failed to create task.';
        if (data.errors) {
          msg = Object.values(data.errors).flat().join(' ');
        }
        errorBox.textContent = msg;
        errorBox.style.display = 'block';
      }
    }
  })
  .catch(err => {
    console.error('Create error:', err);
    if (submitBtn) submitBtn.disabled = false;
    if (errorBox) {
      errorBox.textContent = 'An unexpected error occurred.';
      errorBox.style.display = 'block';
    }
  });
}

// Handle Task Edit Submission
function handleEditTaskSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const taskId = document.getElementById('edit_task_id').value;
  const submitBtn = document.getElementById('editSubmitBtn');
  const errorBox = document.getElementById('editTaskError');

  if (submitBtn) submitBtn.disabled = true;

  const formData = new FormData(form);

  fetch(`/tasks/${taskId}/edit/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: formData
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      closeEditModal();
      window.location.reload();
    } else {
      if (submitBtn) submitBtn.disabled = false;
      if (errorBox) {
        let msg = 'Failed to update task.';
        if (data.errors) {
          msg = Object.values(data.errors).flat().join(' ');
        }
        errorBox.textContent = msg;
        errorBox.style.display = 'block';
      }
    }
  })
  .catch(err => {
    console.error('Edit error:', err);
    if (submitBtn) submitBtn.disabled = false;
    if (errorBox) {
      errorBox.textContent = 'An unexpected error occurred.';
      errorBox.style.display = 'block';
    }
  });
}

// AI Task Description Suggestion
function suggestDescription() {
  const titleInput = document.getElementById('create_title');
  const descInput = document.getElementById('create_description');
  const btn = document.getElementById('aiSuggestBtn');

  const title = titleInput.value.trim();
  if (!title) {
    alert('Please enter a task title first so the AI can generate a relevant description.');
    titleInput.focus();
    return;
  }

  const originalHtml = btn.innerHTML;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Generating...';
  btn.disabled = true;

  fetch('/assistant/suggest/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ title: title })
  })
  .then(res => res.json())
  .then(data => {
    btn.innerHTML = originalHtml;
    btn.disabled = false;

    if (data.success) {
      descInput.value = data.description;
      const descCount = document.getElementById('create_desc_count');
      if (descCount) descCount.textContent = data.description.length;
      descInput.focus();
    } else {
      alert(data.error || 'Failed to generate AI suggestion.');
    }
  })
  .catch(err => {
    console.error('AI suggest error:', err);
    btn.innerHTML = originalHtml;
    btn.disabled = false;
    alert('AI suggestion service is currently unavailable.');
  });
}

function suggestDescriptionForEdit() {
  const titleInput = document.getElementById('edit_title');
  const descInput = document.getElementById('edit_description');

  const title = titleInput.value.trim();
  if (!title) {
    alert('Please enter a task title first.');
    titleInput.focus();
    return;
  }

  fetch('/assistant/suggest/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ title: title })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      descInput.value = data.description;
      const descCount = document.getElementById('edit_desc_count');
      if (descCount) descCount.textContent = data.description.length;
      descInput.focus();
    } else {
      alert(data.error || 'Failed to generate AI suggestion.');
    }
  })
  .catch(err => {
    console.error('AI suggest error:', err);
    alert('AI suggestion service is currently unavailable.');
  });
}

// =====================================================
// Table Checkbox Select-All Functionality
// =====================================================
function toggleSelectAll(master) {
  if (!master) {
    master = document.getElementById('selectAllTasks');
  }
  if (!master) return;

  const isCompleted = master.checked;
  const rowCheckboxes = document.querySelectorAll('.task-table tbody .row-task-checkbox');
  if (rowCheckboxes.length === 0) return;

  const taskIds = [];
  rowCheckboxes.forEach(cb => {
    cb.checked = isCompleted;
    const taskId = cb.getAttribute('data-task-id') || cb.value;
    if (taskId) {
      taskIds.push(parseInt(taskId, 10));
      updateTaskRowUI(taskId, isCompleted);
    }
  });

  master.indeterminate = false;

  // Send bulk status update to the database via AJAX
  const csrf = getCsrfToken();
  fetch('/tasks/bulk-toggle/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrf,
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      task_ids: taskIds,
      completed: isCompleted
    })
  })
  .then(res => {
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
    return res.json();
  })
  .then(data => {
    if (data.success) {
      console.log(`[TaskFlow DB] ${data.updated_count} tasks updated in DB: status=${data.status_text}`);
    } else {
      alert(data.message || 'Failed to update some tasks in database.');
      updateSelectAllCheckboxState();
    }
  })
  .catch(err => {
    console.error('Bulk toggle DB error:', err);
    alert(`Error updating tasks in database: ${err.message}`);
    updateSelectAllCheckboxState();
  });
}

function handleRowCheckboxChange() {
  updateSelectAllCheckboxState();
}


