// Employee Workspace JavaScript Controller for Nanova Infotech

let token = localStorage.getItem("incubation_token");
let role = localStorage.getItem("incubation_role");
let currentUserEmail = localStorage.getItem("incubation_email");
let currentUserName = localStorage.getItem("incubation_name");

let myTeamData = null;
let userChatMode = "admin"; // "admin" (1-on-1 Admin Chat) or "group" (Company Group Chat)
let userChatPollInterval = null;

// Auth Verification
if (!token) {
    alert("Please sign in to access Nanova workspace.");
    window.location.href = "/";
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("user-display-name").innerText = currentUserName || "Employee";
    document.getElementById("user-display-email").innerText = currentUserEmail || "employee@nanovainfotech.com";

    // Set default date picker to today
    const today = new Date().toISOString().split("T")[0];
    const dateInput = document.getElementById("att-date");
    if (dateInput) dateInput.value = today;

    // Load initial data
    loadMyTeam();
    loadTeamAttendanceHistory();
    loadAnnouncement();
});

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

// User Tab Switcher
function switchUserTab(tabName) {
    document.querySelectorAll("main > section").forEach(sec => sec.classList.add("hidden"));
    document.querySelectorAll("button[id^='utab-']").forEach(btn => {
        btn.classList.remove("bg-blue-700", "text-white", "shadow-md");
        btn.classList.add("bg-slate-100", "text-slate-600");
    });

    const activeSec = document.getElementById(`ucontent-${tabName}`);
    const activeBtn = document.getElementById(`utab-${tabName}`);

    if (activeSec) activeSec.classList.remove("hidden");
    if (activeBtn) {
        activeBtn.classList.remove("bg-slate-100", "text-slate-600");
        activeBtn.classList.add("bg-blue-700", "text-white", "shadow-md");
    }

    if (tabName === "chat") {
        fetchUserChatMessages();
        startUserChatPolling();
    } else {
        stopUserChatPolling();
    }
}

// 1. Fetch Global Announcement
async function loadAnnouncement() {
    try {
        const res = await fetch("/api/admin/stats", { headers: getAuthHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        document.getElementById("user-announcement-text").innerText = data.announcement;
    } catch (err) {
        console.error(err);
    }
}

// 2. Fetch My Team Details & Members
async function loadMyTeam() {
    try {
        const res = await fetch("/api/team/my-team", { headers: getAuthHeaders() });
        if (!res.ok) {
            if (res.status === 404) {
                document.getElementById("user-team-display").innerText = "Nanova Employee";
                document.getElementById("u-team-name-card").innerText = "Nanova General Team";
                document.getElementById("u-team-desc-card").innerText = "Official Employee Workspace for Nanova Infotech.";
                return;
            }
            throw new Error("Failed to load team data.");
        }

        myTeamData = await res.json();

        // Populate Header & Card
        document.getElementById("user-team-display").innerText = myTeamData.name;
        document.getElementById("u-team-name-card").innerText = myTeamData.name;
        document.getElementById("u-team-idea-card").innerText = myTeamData.idea_title || "Project Role";
        document.getElementById("u-team-desc-card").innerText = myTeamData.description || "Nanova Infotech Department";
        document.getElementById("u-team-domain-tag").innerText = `Sector: ${myTeamData.domain || "Engineering"}`;
        document.getElementById("u-team-status-badge").innerText = myTeamData.status;
        document.getElementById("u-team-members-count").innerText = myTeamData.members_count;

        // Render Members Roster
        renderTeamMembers(myTeamData.members);

    } catch (err) {
        console.error(err);
    }
}

function renderTeamMembers(members) {
    const grid = document.getElementById("u-team-members-grid");
    if (!grid) return;

    if (!members || members.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-6 text-center text-slate-500 text-xs">No team members added yet.</div>`;
        return;
    }

    grid.innerHTML = "";
    members.forEach(m => {
        const card = document.createElement("div");
        card.className = "p-4 rounded-xl bg-blue-50/70 border border-blue-100 flex items-center justify-between";
        card.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-blue-700 text-white font-bold flex items-center justify-center text-xs shadow-sm">
                    ${escapeHtml(m.name.charAt(0).toUpperCase())}
                </div>
                <div>
                    <h4 class="font-bold text-xs text-slate-900">${escapeHtml(m.name)}</h4>
                    <span class="text-[10px] text-blue-700 font-bold">${escapeHtml(m.role_in_team)}</span>
                    ${m.email ? `<p class="text-[10px] text-slate-500">${escapeHtml(m.email)}</p>` : ''}
                </div>
            </div>
            <button type="button" onclick="removeUserTeamMember(${m.id})" class="text-slate-400 hover:text-red-600 text-xs p-1" title="Remove Member">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        `;
        grid.appendChild(card);
    });
}

// Add & Remove Team Members
function openUserAddMemberModal() {
    document.getElementById("modal-user-add-member").classList.remove("hidden");
}

function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

async function handleUserAddMemberSubmit(e) {
    e.preventDefault();
    const name = document.getElementById("u-member-name").value.trim();
    const role_in_team = document.getElementById("u-member-role").value.trim();
    const email = document.getElementById("u-member-email").value.trim();
    const phone = document.getElementById("u-member-phone").value.trim();

    try {
        const res = await fetch("/api/team/members", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ name, role_in_team, email, phone })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to add team member.");

        closeModal("modal-user-add-member");
        loadMyTeam();
        showToast(`Member "${name}" added to team!`);
    } catch (err) {
        showToast(err.message, true);
    }
}

async function removeUserTeamMember(memberId) {
    if (!confirm("Are you sure you want to remove this member from your team?")) return;
    try {
        const res = await fetch(`/api/team/members/${memberId}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });

        if (!res.ok) throw new Error("Failed to remove member.");
        loadMyTeam();
        showToast("Team member removed.");
    } catch (err) {
        showToast(err.message, true);
    }
}

// 3. Daily Attendance Submission
async function handleAttendanceSubmit(e) {
    e.preventDefault();
    const date = document.getElementById("att-date").value;
    const status = document.getElementById("att-status").value;
    const work_summary = document.getElementById("att-summary").value.trim();

    const btn = document.getElementById("btn-att-submit");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting...`;

    try {
        const res = await fetch("/api/team/attendance", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ date, status, work_summary })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Attendance submission failed.");

        showToast("Daily Attendance Submitted Successfully!");
        document.getElementById("att-summary").value = "";
        loadTeamAttendanceHistory();

    } catch (err) {
        showToast(err.message, true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Submit Attendance</span>`;
    }
}

async function loadTeamAttendanceHistory() {
    const tbody = document.getElementById("u-att-history-tbody");
    if (!tbody) return;

    try {
        const res = await fetch("/api/team/attendance", { headers: getAuthHeaders() });
        if (!res.ok) return;
        const records = await res.json();

        if (records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="py-6 text-center text-slate-500">No attendance history records submitted yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        records.forEach(r => {
            const row = document.createElement("tr");
            row.className = "hover:bg-blue-50/50 transition-colors border-b border-slate-100";
            row.innerHTML = `
                <td class="py-3 px-4 font-bold text-slate-900">${escapeHtml(r.date)}</td>
                <td class="py-3 px-4">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-blue-100 text-blue-800 border border-blue-200">
                        ${escapeHtml(r.status)}
                    </span>
                </td>
                <td class="py-3 px-4 text-slate-700 max-w-sm truncate">${escapeHtml(r.work_summary || "-")}</td>
                <td class="py-3 px-4 text-slate-500 text-xs">${escapeHtml(r.submitted_by_name || "Employee")}</td>
            `;
            tbody.appendChild(row);
        });

    } catch (err) {
        console.error(err);
    }
}

// 4. Messaging Mode Switcher (Admin Private Chat vs Group Chat)
function setEmployeeChatMode(mode) {
    userChatMode = mode;
    const btnAdmin = document.getElementById("u-chat-mode-admin");
    const btnGroup = document.getElementById("u-chat-mode-group");
    const titleEl = document.getElementById("u-chat-title");
    const descEl = document.getElementById("u-chat-desc");

    if (mode === "group") {
        if (btnGroup) btnGroup.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-700 text-white shadow-sm";
        if (btnAdmin) btnAdmin.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200";
        if (titleEl) titleEl.innerText = "🏢 Company Group Chat";
        if (descEl) descEl.innerText = "Realtime Discussion Channel for All Nanova Employees";
    } else {
        if (btnAdmin) btnAdmin.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-700 text-white shadow-sm";
        if (btnGroup) btnGroup.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200";
        if (titleEl) titleEl.innerText = "🔒 Private Message Master Admin (Kalai)";
        if (descEl) descEl.innerText = "Direct 1-on-1 Private Message Channel with kalaimathavan007@gmail.com";
    }

    fetchUserChatMessages();
}

async function fetchUserChatMessages() {
    const windowEl = document.getElementById("u-chat-window");
    if (!windowEl) return;

    let endpoint = "/api/messages/group";
    if (userChatMode === "admin") {
        if (!myTeamData || !myTeamData.id) return;
        endpoint = `/api/messages/team/${myTeamData.id}`;
    }

    try {
        const res = await fetch(endpoint, { headers: getAuthHeaders() });
        if (!res.ok) return;
        const messages = await res.json();

        if (messages.length === 0) {
            windowEl.innerHTML = `<div class="h-full flex flex-col items-center justify-center text-slate-400 text-xs">No messages yet. Type a message to start conversation!</div>`;
            return;
        }

        windowEl.innerHTML = "";
        messages.forEach(m => {
            const isMe = (m.sender_name === currentUserName || m.sender_id === String(localStorage.getItem("incubation_user_id")));
            const bubbleBg = isMe
                ? "bg-blue-700 text-white rounded-br-none ml-auto shadow-md"
                : "bg-slate-100 text-slate-800 rounded-bl-none mr-auto border border-slate-200 shadow-sm";
            const senderTag = isMe ? "You" : escapeHtml(m.sender_name);

            const msgDiv = document.createElement("div");
            msgDiv.className = `max-w-[80%] p-3 rounded-2xl text-xs ${bubbleBg}`;
            msgDiv.innerHTML = `
                <div class="font-extrabold text-[10px] ${isMe ? 'text-blue-100' : 'text-blue-800'} mb-0.5">${senderTag}</div>
                <div class="leading-relaxed font-medium text-xs">${escapeHtml(m.content)}</div>
                <div class="text-[9px] opacity-70 text-right mt-1">${new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            `;
            windowEl.appendChild(msgDiv);
        });

        windowEl.scrollTop = windowEl.scrollHeight;

    } catch (err) {
        console.error(err);
    }
}

async function sendUserChatMessage(e) {
    e.preventDefault();

    const input = document.getElementById("u-chat-input");
    const content = input.value.trim();
    if (!content) return;

    let endpoint = "/api/messages/group";
    if (userChatMode === "admin") {
        if (!myTeamData || !myTeamData.id) {
            showToast("Cannot send private message: Please assign department team.", true);
            return;
        }
        endpoint = `/api/messages/team/${myTeamData.id}`;
    }

    try {
        const res = await fetch(endpoint, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ content })
        });

        if (!res.ok) throw new Error("Failed to send message.");
        input.value = "";
        fetchUserChatMessages();
    } catch (err) {
        showToast(err.message, true);
    }
}

function startUserChatPolling() {
    stopUserChatPolling();
    userChatPollInterval = setInterval(fetchUserChatMessages, 3500);
}

function stopUserChatPolling() {
    if (userChatPollInterval) clearInterval(userChatPollInterval);
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
