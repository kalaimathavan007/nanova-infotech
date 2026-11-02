// Admin Dashboard JavaScript Controller for Nanova Infotech

let token = localStorage.getItem("incubation_token");
let role = localStorage.getItem("incubation_role");
let currentAdminEmail = localStorage.getItem("incubation_email");
let currentAdminName = localStorage.getItem("incubation_name");

let allTeams = [];
let allAttendanceRecords = [];
let activeChatTeamId = "group"; // Default to Company Group Chat
let chatPollInterval = null;

// Auth Verification
if (!token || role !== "admin") {
    alert("Access Denied: Master Admin authorization required.");
    window.location.href = "/";
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("admin-user-name").innerText = currentAdminName || "Master Admin";
    document.getElementById("admin-user-email").innerText = currentAdminEmail || "kalaimathavan007@gmail.com";

    // Initial Data Fetching
    loadAdminStats();
    loadTeamsList();
    loadAttendanceRecords();
    loadAdminSettings();
});

function toggleOtherDomain(selectId, containerId) {
    const select = document.getElementById(selectId);
    const container = document.getElementById(containerId);
    if (!select || !container) return;
    if (select.value === "Other") {
        container.classList.remove("hidden");
    } else {
        container.classList.add("hidden");
    }
}

// Toast notification helper
function showToast(msg, isError = false) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `px-4 py-3 rounded-xl text-xs font-bold shadow-xl border flex items-center gap-2 animate-fade-in ${
        isError
        ? "bg-red-50 text-red-700 border-red-300"
        : "bg-blue-50 text-blue-800 border-blue-300"
    }`;
    toast.innerHTML = `
        <i class="fa-solid ${isError ? 'fa-circle-exclamation text-red-500' : 'fa-circle-check text-blue-600'}"></i>
        <span>${escapeHtml(msg)}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3500);
}

function getAuthHeaders() {
    return {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };
}

function logout() {
    localStorage.clear();
    window.location.href = "/";
}

// Tab Switching
function switchTab(tabName) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.remove("bg-blue-700", "text-white", "shadow-md");
        btn.classList.add("bg-slate-100", "text-slate-600");
    });

    const activeContent = document.getElementById(`tab-content-${tabName}`);
    const activeBtn = document.getElementById(`nav-${tabName}`);

    if (activeContent) activeContent.classList.remove("hidden");
    if (activeBtn) {
        activeBtn.classList.remove("bg-slate-100", "text-slate-600");
        activeBtn.classList.add("bg-blue-700", "text-white", "shadow-md");
    }

    if (tabName === "chat") {
        renderChatTeamsList();
        fetchChatMessages();
        startChatPolling();
    } else {
        stopChatPolling();
    }
}

// 1. Load Admin Stats & Announcement
async function loadAdminStats() {
    try {
        const res = await fetch("/api/admin/stats", { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Failed to fetch admin stats.");
        const data = await res.json();

        document.getElementById("stat-teams").innerText = data.total_teams;
        document.getElementById("stat-users").innerText = data.total_users;
        document.getElementById("stat-members").innerText = data.total_members;
        document.getElementById("stat-attendance").innerText = data.today_attendance_count;
        document.getElementById("announcement-display").innerText = data.announcement;

    } catch (err) {
        console.error("Error loading stats:", err);
    }
}

// 2. Load Teams List
async function loadTeamsList() {
    const container = document.getElementById("teams-grid-container");
    if (container) container.innerHTML = `<div class="col-span-full py-8 text-center text-slate-500 text-xs"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Loading teams...</div>`;

    try {
        const res = await fetch("/api/admin/teams", { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Failed to load teams.");
        allTeams = await res.json();

        updateTeamSelectOptions();
        renderChatTeamsList();
        renderTeamsGrid(allTeams);

    } catch (err) {
        console.error(err);
        if (container) container.innerHTML = `<div class="col-span-full py-8 text-center text-red-500 text-xs">Error loading teams.</div>`;
    }
}

function renderTeamsGrid(teams) {
    const container = document.getElementById("teams-grid-container");
    if (!container) return;

    if (teams.length === 0) {
        container.innerHTML = `<div class="col-span-full py-12 text-center text-slate-500 text-xs">No department teams created yet. Click "Add Team" above.</div>`;
        return;
    }

    container.innerHTML = "";
    teams.forEach(t => {
        const membersList = t.members.map(m => `
            <div class="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-blue-50/60 border border-blue-100 text-xs">
                <div>
                    <span class="font-bold text-slate-800">${escapeHtml(m.name)}</span>
                    <span class="text-[10px] text-blue-600 font-semibold ml-1">(${escapeHtml(m.role_in_team)})</span>
                </div>
                <button type="button" onclick="removeTeamMember('${m.id}')" class="text-slate-400 hover:text-red-600 text-xs px-1" title="Remove Member">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
        `).join("");

        const card = document.createElement("div");
        card.className = "bg-white p-4 sm:p-5 flex flex-col justify-between border-t-4 border-t-blue-700 rounded-2xl shadow-md border border-slate-200 hover:shadow-lg transition-all";
        card.innerHTML = `
            <div>
                <div class="flex justify-between items-start mb-2">
                    <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">${escapeHtml(t.domain || "Engineering")}</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 font-semibold">${escapeHtml(t.status)}</span>
                </div>

                <div class="flex justify-between items-center">
                    <h3 class="text-base sm:text-lg font-extrabold text-slate-900 mb-1">${escapeHtml(t.name)}</h3>
                    <button type="button" onclick="openEditTeamModal('${t.id}')" class="text-xs text-blue-700 hover:text-blue-900 p-1" title="Edit Details">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                </div>

                <p class="text-xs font-semibold text-blue-800 mb-2"><i class="fa-solid fa-briefcase text-blue-600 mr-1"></i>${escapeHtml(t.idea_title || "N/A")}</p>
                <p class="text-xs text-slate-600 mb-4 line-clamp-2">${escapeHtml(t.description || "No description provided.")}</p>

                <!-- Members Section -->
                <div class="mt-4 pt-3 border-t border-slate-100">
                    <div class="flex justify-between items-center mb-2">
                        <span class="text-xs font-bold text-slate-800">Team Roster (${t.members_count})</span>
                        <button type="button" onclick="openAddMemberModal('${t.id}')" class="text-[11px] text-blue-700 hover:text-blue-900 font-bold flex items-center gap-1">
                            <i class="fa-solid fa-user-plus"></i> Add
                        </button>
                    </div>
                    <div class="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                        ${membersList || '<p class="text-[11px] text-slate-400 italic">No members added yet.</p>'}
                    </div>
                </div>
            </div>

            <div class="mt-5 pt-3 border-t border-slate-100 flex justify-between items-center text-xs">
                <button type="button" onclick="openChatWithTeam('${t.id}')" class="px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white border border-blue-200 transition-all flex items-center gap-1.5 font-bold">
                    <i class="fa-solid fa-comments"></i> Private Chat
                </button>
                <button type="button" onclick="deleteTeam('${t.id}')" class="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors" title="Delete Team">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

function filterTeamsList() {
    const query = document.getElementById("team-search-input").value.toLowerCase().trim();
    if (!query) {
        renderTeamsGrid(allTeams);
        return;
    }
    const filtered = allTeams.filter(t =>
        t.name.toLowerCase().includes(query) ||
        (t.domain && t.domain.toLowerCase().includes(query)) ||
        (t.idea_title && t.idea_title.toLowerCase().includes(query))
    );
    renderTeamsGrid(filtered);
}

// 3. Attendance Records
async function loadAttendanceRecords() {
    const tbody = document.getElementById("attendance-table-body");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-500"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Loading records...</td></tr>`;

    const filterDate = document.getElementById("attendance-filter-date").value;
    const filterTeam = document.getElementById("attendance-filter-team").value;

    let url = "/api/admin/attendance?";
    if (filterDate) url += `target_date=${filterDate}&`;
    if (filterTeam) url += `team_id=${filterTeam}&`;

    try {
        const res = await fetch(url, { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Failed to load attendance.");
        allAttendanceRecords = await res.json();

        if (allAttendanceRecords.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-slate-500">No attendance records found.</td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        allAttendanceRecords.forEach(r => {
            const row = document.createElement("tr");
            row.className = "hover:bg-blue-50/50 transition-colors border-b border-slate-100";
            row.innerHTML = `
                <td class="py-3 px-3 font-bold text-slate-900">${escapeHtml(r.date)}</td>
                <td class="py-3 px-3 font-bold text-blue-700">${escapeHtml(r.team_name || "N/A")}</td>
                <td class="py-3 px-3 font-medium text-slate-700">${escapeHtml(r.submitted_by_name || "Employee")}</td>
                <td class="py-3 px-3">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-blue-100 text-blue-800 border border-blue-200">
                        ${escapeHtml(r.status)}
                    </span>
                </td>
                <td class="py-3 px-3 text-slate-600 max-w-xs truncate">${escapeHtml(r.work_summary || "-")}</td>
                <td class="py-3 px-3 text-slate-400 text-[11px]">${new Date(r.submitted_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
            `;
            tbody.appendChild(row);
        });

    } catch (err) {
        console.error(err);
        tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-red-500">Error fetching attendance.</td></tr>`;
    }
}

function resetAttendanceFilters() {
    document.getElementById("attendance-filter-date").value = "";
    document.getElementById("attendance-filter-team").value = "";
    loadAttendanceRecords();
}

function exportAttendanceCSV() {
    if (!allAttendanceRecords || allAttendanceRecords.length === 0) {
        showToast("No attendance records to export.", true);
        return;
    }

    let csvContent = "data:text/csv;charset=utf-8,Date,Team Name,Submitted By,Status,Work Summary,Submitted At\n";
    allAttendanceRecords.forEach(r => {
        const row = [
            `"${r.date}"`,
            `"${r.team_name || ''}"`,
            `"${r.submitted_by_name || ''}"`,
            `"${r.status}"`,
            `"${(r.work_summary || '').replace(/"/g, '""')}"`,
            `"${r.submitted_at}"`
        ];
        csvContent += row.join(",") + "\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `nanova_attendance_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("Attendance CSV downloaded!");
}

async function exportDatabaseBackup() {
    try {
        const res = await fetch("/api/admin/database/export", { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Failed to export database backup.");
        const data = await res.json();

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute("href", dataStr);
        dlAnchor.setAttribute("download", `nanova_db_backup_${new Date().toISOString().split('T')[0]}.json`);
        document.body.appendChild(dlAnchor);
        dlAnchor.click();
        dlAnchor.remove();

        showToast("Database Backup exported successfully!");
    } catch (err) {
        showToast(err.message, true);
    }
}

function updateTeamSelectOptions() {
    const select = document.getElementById("attendance-filter-team");
    if (!select) return;
    select.innerHTML = `<option value="">All Teams</option>`;
    allTeams.forEach(t => {
        select.innerHTML += `<option value="${t.id}">${escapeHtml(t.name)}</option>`;
    });
}

// 4. Admin Settings Form
async function loadAdminSettings() {
    try {
        const res = await fetch("/api/admin/settings", { headers: getAuthHeaders() });
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("settings-name").value = data.incubation_name;
        document.getElementById("settings-admin-emails").value = data.allowed_admin_emails;
        document.getElementById("settings-announcement").value = data.announcement;

        document.getElementById("header-incubation-name").innerText = data.incubation_name;
    } catch (err) {
        console.error(err);
    }
}

async function saveAdminSettings(e) {
    e.preventDefault();
    const incubation_name = document.getElementById("settings-name").value.trim();
    const allowed_admin_emails = document.getElementById("settings-admin-emails").value.trim();
    const announcement = document.getElementById("settings-announcement").value.trim();

    try {
        const res = await fetch("/api/admin/settings", {
            method: "PUT",
            headers: getAuthHeaders(),
            body: JSON.stringify({ incubation_name, allowed_admin_emails, announcement })
        });

        if (!res.ok) throw new Error("Failed to save settings.");
        showToast("Admin Configuration saved successfully!");
        loadAdminSettings();
        loadAdminStats();
    } catch (err) {
        showToast(err.message, true);
    }
}

// Modals
function openCreateTeamModal() {
    document.getElementById("modal-create-team").classList.remove("hidden");
}

function openEditTeamModal(teamId) {
    const team = allTeams.find(t => String(t.id) === String(teamId));
    if (!team) return;

    document.getElementById("edit-team-id").value = team.id;
    document.getElementById("edit-team-name").value = team.name;
    document.getElementById("edit-team-idea").value = team.idea_title || "";
    document.getElementById("edit-team-domain").value = team.domain || "Engineering";
    document.getElementById("edit-team-status").value = team.status || "Active";
    document.getElementById("edit-team-desc").value = team.description || "";

    document.getElementById("modal-edit-team").classList.remove("hidden");
}

function openAddMemberModal(teamId) {
    document.getElementById("modal-member-team-id").value = teamId;
    document.getElementById("modal-add-member").classList.remove("hidden");
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add("hidden");
}

async function handleCreateTeamSubmit(e) {
    e.preventDefault();
    const name = document.getElementById("modal-team-name").value.trim();
    const idea_title = document.getElementById("modal-team-idea").value.trim();
    const domain = document.getElementById("modal-team-domain").value.trim();
    const description = document.getElementById("modal-team-desc").value.trim();

    try {
        const res = await fetch("/api/admin/teams", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ name, idea_title, domain, description })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to create team.");

        closeModal("modal-create-team");
        loadTeamsList();
        loadAdminStats();
        showToast(`Team "${name}" created successfully!`);
    } catch (err) {
        showToast(err.message, true);
    }
}

async function handleEditTeamSubmit(e) {
    e.preventDefault();
    const teamId = document.getElementById("edit-team-id").value;
    const name = document.getElementById("edit-team-name").value.trim();
    const idea_title = document.getElementById("edit-team-idea").value.trim();
    const domain = document.getElementById("edit-team-domain").value.trim();
    const status = document.getElementById("edit-team-status").value;
    const description = document.getElementById("edit-team-desc").value.trim();

    try {
        const res = await fetch(`/api/admin/teams/${teamId}`, {
            method: "PUT",
            headers: getAuthHeaders(),
            body: JSON.stringify({ name, idea_title, domain, status, description })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to update team.");

        closeModal("modal-edit-team");
        loadTeamsList();
        showToast(`Team updated successfully!`);
    } catch (err) {
        showToast(err.message, true);
    }
}

async function handleAddMemberSubmit(e) {
    e.preventDefault();
    const teamId = document.getElementById("modal-member-team-id").value;
    const name = document.getElementById("modal-member-name").value.trim();
    const role_in_team = document.getElementById("modal-member-role").value.trim();
    const email = document.getElementById("modal-member-email").value.trim();
    const phone = document.getElementById("modal-member-phone").value.trim();

    try {
        const res = await fetch(`/api/admin/teams/${teamId}/members`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ name, role_in_team, email, phone })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to add member.");

        closeModal("modal-add-member");
        loadTeamsList();
        loadAdminStats();
        showToast(`Member "${name}" added to team!`);
    } catch (err) {
        showToast(err.message, true);
    }
}

async function deleteTeam(teamId) {
    if (!confirm("Are you sure you want to delete this team? All members and attendance data will be removed.")) return;
    try {
        const res = await fetch(`/api/admin/teams/${teamId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error("Failed to delete team.");
        loadTeamsList();
        loadAdminStats();
        showToast("Team deleted successfully.");
    } catch (err) {
        showToast(err.message, true);
    }
}

async function removeTeamMember(memberId) {
    if (!confirm("Remove this team member?")) return;
    try {
        const res = await fetch(`/api/admin/members/${memberId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error("Failed to remove member.");
        loadTeamsList();
        loadAdminStats();
        showToast("Team member removed.");
    } catch (err) {
        showToast(err.message, true);
    }
}

// 5. Messaging Channels (Group Chat + 1-on-1 Employee Direct Messaging)
function renderChatTeamsList() {
    const list = document.getElementById("chat-teams-list");
    if (!list) return;

    list.innerHTML = "";

    // 1. Company Group Chat Option (Always Top)
    const isGroupActive = (activeChatTeamId === "group");
    const groupBtn = document.createElement("button");
    groupBtn.type = "button";
    groupBtn.className = `w-full text-left p-3.5 rounded-xl border flex items-center justify-between transition-all mb-2 ${
        isGroupActive
        ? "bg-blue-700 text-white border-blue-800 shadow-md"
        : "bg-blue-50/80 text-blue-900 border-blue-200 hover:bg-blue-100"
    }`;
    groupBtn.onclick = () => selectTeamChat("group", "🏢 Company Group Chat", "Broadcast & Team Discussion");
    groupBtn.innerHTML = `
        <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-blue-600 text-white font-bold flex items-center justify-center text-xs shadow-sm">
                <i class="fa-solid fa-users"></i>
            </div>
            <div>
                <div class="font-bold text-xs">Company Group Chat</div>
                <div class="text-[10px] opacity-80">All Employees & Admin</div>
            </div>
        </div>
        <i class="fa-solid fa-chevron-right text-xs opacity-60"></i>
    `;
    list.appendChild(groupBtn);

    // Divider
    const divider = document.createElement("div");
    divider.className = "text-[10px] font-extrabold uppercase text-slate-400 tracking-wider my-2.5 px-1";
    divider.innerText = "Employee Conversations";
    list.appendChild(divider);

    if (allTeams.length === 0) {
        const emptyDiv = document.createElement("div");
        emptyDiv.className = "p-3 text-center text-slate-400 text-xs italic";
        emptyDiv.innerText = "No employee conversations yet.";
        list.appendChild(emptyDiv);
        return;
    }

    // 2. Individual Employee/Team Conversations
    allTeams.forEach(t => {
        const isActive = (String(t.id) === String(activeChatTeamId));
        const activeClass = isActive ? "bg-blue-700 text-white border-blue-800 shadow-md" : "bg-white text-slate-800 border-slate-200 hover:bg-blue-50";
        const item = document.createElement("button");
        item.type = "button";
        item.className = `w-full text-left p-3 rounded-xl border flex items-center justify-between transition-all mb-1.5 ${activeClass}`;
        item.onclick = () => selectTeamChat(t.id, t.name, t.domain);
        item.innerHTML = `
            <div>
                <div class="font-bold text-xs">${escapeHtml(t.name)}</div>
                <div class="text-[10px] opacity-75">${escapeHtml(t.domain || "Team")}</div>
            </div>
            <i class="fa-solid fa-chevron-right text-xs opacity-50"></i>
        `;
        list.appendChild(item);
    });
}

function openChatWithTeam(teamId) {
    const team = allTeams.find(t => String(t.id) === String(teamId));
    if (team) {
        switchTab("chat");
        selectTeamChat(team.id, team.name, team.domain);
    }
}

function selectTeamChat(teamId, teamName, teamDomain) {
    activeChatTeamId = teamId;
    document.getElementById("chat-selected-team-name").innerText = teamName;
    document.getElementById("chat-selected-team-domain").innerText = (teamId === "group") ? "Company-Wide Realtime Discussion" : `Direct 1-on-1 Chat (${teamDomain || "Employee"})`;
    document.getElementById("chat-input-text").disabled = false;

    // Mobile View Toggle: Show Chat Box, Hide Sidebar
    if (window.innerWidth < 1024) {
        const sidebar = document.getElementById("chat-teams-sidebar");
        const box = document.getElementById("chat-box-panel");
        if (sidebar) sidebar.classList.add("hidden");
        if (box) box.classList.remove("hidden");
    }

    renderChatTeamsList();
    fetchChatMessages();
    startChatPolling();
}

function showMobileChatTeamsList() {
    const sidebar = document.getElementById("chat-teams-sidebar");
    const box = document.getElementById("chat-box-panel");
    if (sidebar) sidebar.classList.remove("hidden");
    if (box) box.classList.add("hidden");
}

async function fetchChatMessages() {
    if (!activeChatTeamId) return;
    const container = document.getElementById("chat-messages-container");

    const endpoint = (activeChatTeamId === "group") ? "/api/messages/group" : `/api/messages/team/${activeChatTeamId}`;

    try {
        const res = await fetch(endpoint, { headers: getAuthHeaders() });
        if (!res.ok) return;
        const messages = await res.json();

        if (messages.length === 0) {
            container.innerHTML = `<div class="h-full flex flex-col items-center justify-center text-slate-400 text-xs">No messages in this conversation yet. Send a message to start!</div>`;
            return;
        }

        container.innerHTML = "";
        messages.forEach(m => {
            const isMe = (m.sender_role === "admin");
            const bubbleBg = isMe
                ? "bg-blue-700 text-white rounded-br-none ml-auto shadow-md"
                : "bg-slate-100 text-slate-800 rounded-bl-none mr-auto border border-slate-200 shadow-sm";
            const senderTag = isMe ? "Master Admin (Kalai)" : escapeHtml(m.sender_name);

            const msgDiv = document.createElement("div");
            msgDiv.className = `max-w-[85%] sm:max-w-[80%] p-3 rounded-2xl text-xs ${bubbleBg}`;
            msgDiv.innerHTML = `
                <div class="font-extrabold text-[10px] ${isMe ? 'text-blue-100' : 'text-blue-800'} mb-0.5">${senderTag}</div>
                <div class="leading-relaxed font-medium text-xs">${escapeHtml(m.content)}</div>
                <div class="text-[9px] opacity-70 text-right mt-1">${new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            `;
            container.appendChild(msgDiv);
        });

        container.scrollTop = container.scrollHeight;

    } catch (err) {
        console.error(err);
    }
}

async function sendAdminChatMessage(e) {
    e.preventDefault();
    if (!activeChatTeamId) return;

    const input = document.getElementById("chat-input-text");
    const content = input.value.trim();
    if (!content) return;

    const endpoint = (activeChatTeamId === "group") ? "/api/messages/group" : `/api/messages/team/${activeChatTeamId}`;

    try {
        const res = await fetch(endpoint, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ content })
        });

        if (!res.ok) throw new Error("Failed to send message.");
        input.value = "";
        fetchChatMessages();
    } catch (err) {
        showToast(err.message, true);
    }
}

function startChatPolling() {
    stopChatPolling();
    chatPollInterval = setInterval(fetchChatMessages, 3500);
}

function stopChatPolling() {
    if (chatPollInterval) clearInterval(chatPollInterval);
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
