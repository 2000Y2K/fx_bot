import { useState, useEffect, useCallback } from "react";

// ─── CONFIG ────────────────────────────────────────────────────────────────
const API = (import.meta.env.VITE_API_BASE_URL || window.__API_BASE__ || "http://localhost:8000").replace(/\/$/, "");

const STATUS_COLORS = {
  pending:     { bg: "bg-zinc-700",       text: "text-zinc-300",    dot: "bg-zinc-400",    label: "PENDIENTE" },
  in_progress: { bg: "bg-amber-900/60",   text: "text-amber-300",   dot: "bg-amber-400",   label: "EN CURSO"  },
  done:        { bg: "bg-emerald-900/50", text: "text-emerald-300", dot: "bg-emerald-400", label: "LISTO"     },
  blocked:     { bg: "bg-red-900/50",     text: "text-red-300",     dot: "bg-red-400",     label: "BLOQUEADO" },
};

const api = {
  get:   (path) => fetch(`${API}${path}`).then(r => r.json()),
  post:  (path, body) => fetch(`${API}${path}`, { method:"POST",  headers:{"Content-Type":"application/json"}, body: JSON.stringify(body) }).then(r => r.json()),
  patch: (path, body) => fetch(`${API}${path}`, { method:"PATCH", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body) }).then(r => r.json()),
};

// ─── HOOKS ─────────────────────────────────────────────────────────────────
function useData(path) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);
  const reload = useCallback(() => {
    setLoading(true);
    api.get(path).then(setData).catch(setError).finally(() => setLoading(false));
  }, [path]);
  useEffect(() => { reload(); }, [reload]);
  return { data, loading, error, reload };
}

// ─── HELPERS ───────────────────────────────────────────────────────────────
function teamLabel(team, projects) {
  if (!team) return null;
  const proj = projects?.find(p => p.id === team.project_id);
  return proj ? `${team.name} · ${proj.name}` : team.name;
}

// ─── PRIMITIVES ────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const s = STATUS_COLORS[status] || STATUS_COLORS.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold tracking-widest ${s.bg} ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{background:"rgba(0,0,0,0.75)"}}>
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-700">
          <h3 className="text-sm font-bold tracking-widest text-amber-400 uppercase">{title}</h3>
          <button onClick={onClose} className="text-zinc-500 hover:text-white text-lg leading-none">×</button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div className="mb-4">
      <label className="block text-[10px] font-bold tracking-widest text-zinc-500 uppercase mb-1.5">{label}</label>
      {children}
    </div>
  );
}

function SectionHeader({ title, count, onAdd }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        <h2 className="text-xs font-bold tracking-widest text-zinc-400 uppercase">{title}</h2>
        {count != null && (
          <span className="text-[10px] bg-zinc-800 text-zinc-500 rounded px-1.5 py-0.5 font-mono">{count}</span>
        )}
      </div>
      <button onClick={onAdd} className="text-[10px] font-bold tracking-widest text-amber-400 hover:text-amber-300 uppercase transition-colors flex items-center gap-1">
        <span className="text-base leading-none">+</span> Nuevo
      </button>
    </div>
  );
}

function Empty({ text }) {
  return (
    <div className="text-center py-10 text-xs text-zinc-600 tracking-widest uppercase border border-dashed border-zinc-800 rounded-lg">
      {text}
    </div>
  );
}

const inputClass = "w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition-colors";
const btnPrimary = "px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black text-xs font-bold tracking-widest uppercase rounded transition-colors";
const btnGhost   = "px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-bold tracking-widest uppercase rounded transition-colors border border-zinc-700";

// ─── SECTIONS ──────────────────────────────────────────────────────────────

function ProjectsSection() {
  const { data: projects, loading, reload } = useData("/projects");
  const [modal, setModal] = useState(false);
  const [form, setForm]   = useState({ name: "", description: "" });

  async function handleCreate() {
    await api.post("/projects", form);
    setModal(false); setForm({ name: "", description: "" }); reload();
  }

  return (
    <div>
      <SectionHeader title="Proyectos" count={projects?.length} onAdd={() => setModal(true)} />
      {loading ? <Spinner /> : (
        <div className="grid gap-3">
          {projects?.map(p => (
            <div key={p.id} className="bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-4 flex items-center justify-between hover:border-zinc-600 transition-colors">
              <div>
                <div className="text-sm font-semibold text-white">{p.name}</div>
                {p.description && <div className="text-xs text-zinc-500 mt-0.5">{p.description}</div>}
              </div>
              <div className="text-[10px] text-zinc-600 font-mono">#{p.id}</div>
            </div>
          ))}
          {projects?.length === 0 && <Empty text="Sin proyectos aún" />}
        </div>
      )}
      {modal && (
        <Modal title="Nuevo Proyecto" onClose={() => setModal(false)}>
          <Field label="Nombre"><input className={inputClass} value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Serie documental, etc." /></Field>
          <Field label="Descripción"><textarea className={inputClass} rows={3} value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setModal(false)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleCreate} disabled={!form.name}>Crear</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

function TeamsSection() {
  const { data: teams, loading, reload } = useData("/teams");
  const { data: projects }               = useData("/projects");
  const [modal, setModal] = useState(false);
  const [form, setForm]   = useState({ name: "", project_id: "" });

  async function handleCreate() {
    await api.post("/teams", { ...form, project_id: parseInt(form.project_id) });
    setModal(false); setForm({ name: "", project_id: "" }); reload();
  }

  return (
    <div>
      <SectionHeader title="Equipos" count={teams?.length} onAdd={() => setModal(true)} />
      {loading ? <Spinner /> : (
        <div className="grid gap-3">
          {teams?.map(t => {
            const proj = projects?.find(p => p.id === t.project_id);
            return (
              <div key={t.id} className="bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-4 flex items-center justify-between hover:border-zinc-600 transition-colors">
                <div>
                  <div className="text-sm font-semibold text-white">{t.name}</div>
                  {proj && <div className="text-xs text-zinc-500 mt-0.5">📁 {proj.name}</div>}
                </div>
                <div className="text-[10px] text-zinc-600 font-mono">#{t.id}</div>
              </div>
            );
          })}
          {teams?.length === 0 && <Empty text="Sin equipos aún" />}
        </div>
      )}
      {modal && (
        <Modal title="Nuevo Equipo" onClose={() => setModal(false)}>
          <Field label="Nombre"><input className={inputClass} value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Edición, Sonido, FX…" /></Field>
          <Field label="Proyecto">
            <select className={inputClass} value={form.project_id} onChange={e => setForm({...form, project_id: e.target.value})}>
              <option value="">— Seleccionar —</option>
              {projects?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setModal(false)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleCreate} disabled={!form.name || !form.project_id}>Crear</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

function PersonsSection() {
  const { data: persons, loading, reload } = useData("/persons");
  const { data: teams }                    = useData("/teams");
  const { data: projects }                 = useData("/projects");
  const [modal, setModal]         = useState(false);
  const [editModal, setEditModal] = useState(null);
  const [form, setForm]     = useState({ name: "", whatsapp_number: "", telegram_id: "", team_id: "" });
  const [editForm, setEditForm] = useState({ name: "", whatsapp_number: "", telegram_id: "", team_id: "" });

  async function handleCreate() {
    await api.post("/persons", { ...form, team_id: parseInt(form.team_id) });
    setModal(false); setForm({ name: "", whatsapp_number: "", telegram_id: "", team_id: "" }); reload();
  }

  function openEdit(p) {
    setEditModal(p);
    setEditForm({
      name: p.name,
      whatsapp_number: p.whatsapp_number || "",
      telegram_id: p.telegram_id || "",
      team_id: String(p.team_id),
    });
  }

  async function handleEdit() {
    await api.patch(`/persons/${editModal.id}`, {
      ...editForm,
      team_id: editForm.team_id ? parseInt(editForm.team_id) : undefined,
    });
    setEditModal(null); reload();
  }

  return (
    <div>
      <SectionHeader title="Personas" count={persons?.length} onAdd={() => setModal(true)} />
      {loading ? <Spinner /> : (
        <div className="grid gap-3">
          {persons?.map(p => {
            const team = teams?.find(t => t.id === p.team_id);
            return (
              <div key={p.id} className="bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-4 flex items-center justify-between hover:border-zinc-600 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-xs font-bold text-amber-400">
                    {p.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">{p.name}</div>
                    <div className="text-xs text-zinc-500 flex items-center gap-2 flex-wrap">
                      {p.whatsapp_number && <span>{p.whatsapp_number}</span>}
                      {team && <span>· {teamLabel(team, projects)}</span>}
                      {p.telegram_id
                        ? <span className="text-emerald-500 font-mono">✓ TG:{p.telegram_id}</span>
                        : <span className="text-red-500/70">✗ sin Telegram</span>
                      }
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => openEdit(p)}
                  className="text-[10px] text-zinc-600 hover:text-amber-400 transition-colors ml-3 shrink-0 border border-zinc-700 hover:border-amber-500 rounded px-2 py-1"
                >
                  EDITAR
                </button>
              </div>
            );
          })}
          {persons?.length === 0 && <Empty text="Sin personas aún" />}
        </div>
      )}

      {editModal && (
        <Modal title={`Editar — ${editModal.name}`} onClose={() => setEditModal(null)}>
          <Field label="Nombre">
            <input className={inputClass} value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} />
          </Field>
          <Field label="WhatsApp">
            <input className={inputClass} value={editForm.whatsapp_number} onChange={e => setEditForm({...editForm, whatsapp_number: e.target.value})} placeholder="+5491155555555" />
          </Field>
          <Field label="Telegram ID">
            <input className={inputClass} value={editForm.telegram_id} onChange={e => setEditForm({...editForm, telegram_id: e.target.value})} placeholder="El usuario lo ve con /start" />
          </Field>
          <Field label="Equipo">
            <select className={inputClass} value={editForm.team_id} onChange={e => setEditForm({...editForm, team_id: e.target.value})}>
              <option value="">— Seleccionar —</option>
              {teams?.map(t => {
                const proj = projects?.find(p => p.id === t.project_id);
                return <option key={t.id} value={t.id}>{t.name}{proj ? ` · ${proj.name}` : ""}</option>;
              })}
            </select>
          </Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setEditModal(null)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleEdit} disabled={!editForm.name}>Guardar</button>
          </div>
        </Modal>
      )}

      {modal && (
        <Modal title="Nueva Persona" onClose={() => setModal(false)}>
          <Field label="Nombre"><input className={inputClass} value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Ana García" /></Field>
          <Field label="WhatsApp (con código de país)"><input className={inputClass} value={form.whatsapp_number} onChange={e => setForm({...form, whatsapp_number: e.target.value})} placeholder="+5491155555555" /></Field>
          <Field label="Telegram ID"><input className={inputClass} value={form.telegram_id} onChange={e => setForm({...form, telegram_id: e.target.value})} placeholder="Opcional — el usuario lo ve con /start" /></Field>
          <Field label="Equipo">
            <select className={inputClass} value={form.team_id} onChange={e => setForm({...form, team_id: e.target.value})}>
              <option value="">— Seleccionar —</option>
              {teams?.map(t => {
                const proj = projects?.find(p => p.id === t.project_id);
                return <option key={t.id} value={t.id}>{t.name}{proj ? ` · ${proj.name}` : ""}</option>;
              })}
            </select>
          </Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setModal(false)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleCreate} disabled={!form.name || !form.team_id}>Crear</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

function AssetsSection() {
  const { data: assets, loading, reload } = useData("/assets");
  const { data: projects }                = useData("/projects");
  const [modal, setModal]     = useState(false);
  const [editModal, setEditModal] = useState(null);
  const [form, setForm]       = useState({ name: "", project_id: "", drive_url: "", current_version: "", notes: "" });
  const [editForm, setEditForm] = useState({ drive_url: "", current_version: "", notes: "" });

  async function handleCreate() {
    await api.post("/assets", { ...form, project_id: parseInt(form.project_id) });
    setModal(false); setForm({ name:"", project_id:"", drive_url:"", current_version:"", notes:"" }); reload();
  }

  function openEdit(asset) {
    setEditModal(asset);
    setEditForm({ drive_url: asset.drive_url || "", current_version: asset.current_version || "", notes: asset.notes || "" });
  }

  async function handleEdit() {
    await api.patch(`/assets/${editModal.id}`, editForm);
    setEditModal(null); reload();
  }

  return (
    <div>
      <SectionHeader title="Assets" count={assets?.length} onAdd={() => setModal(true)} />
      {loading ? <Spinner /> : (
        <div className="grid gap-3">
          {assets?.map(a => {
            const proj = projects?.find(p => p.id === a.project_id);
            return (
              <div key={a.id} className="bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-4 hover:border-zinc-600 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-white">{a.name}</span>
                      {a.current_version && (
                        <span className="text-[10px] font-mono bg-amber-500/15 text-amber-400 px-1.5 py-0.5 rounded">{a.current_version}</span>
                      )}
                    </div>
                    <div className="text-xs text-zinc-500 mt-0.5">{proj?.name}</div>
                    {a.drive_url && (
                      <a href={a.drive_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-zinc-500 hover:text-amber-400 mt-1 transition-colors">
                        ↗ Drive
                      </a>
                    )}
                  </div>
                  <button onClick={() => openEdit(a)} className="text-[10px] text-zinc-600 hover:text-amber-400 transition-colors ml-3 shrink-0 border border-zinc-700 hover:border-amber-500 rounded px-2 py-1">
                    EDITAR
                  </button>
                </div>
              </div>
            );
          })}
          {assets?.length === 0 && <Empty text="Sin assets aún" />}
        </div>
      )}

      {modal && (
        <Modal title="Nuevo Asset" onClose={() => setModal(false)}>
          <Field label="Nombre"><input className={inputClass} value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="escena_04_comp.aep" /></Field>
          <Field label="Proyecto">
            <select className={inputClass} value={form.project_id} onChange={e => setForm({...form, project_id: e.target.value})}>
              <option value="">— Seleccionar —</option>
              {projects?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          <Field label="Link Drive"><input className={inputClass} value={form.drive_url} onChange={e => setForm({...form, drive_url: e.target.value})} placeholder="https://drive.google.com/..." /></Field>
          <Field label="Versión actual"><input className={inputClass} value={form.current_version} onChange={e => setForm({...form, current_version: e.target.value})} placeholder="v1, entrega_final, etc." /></Field>
          <Field label="Notas"><textarea className={inputClass} rows={2} value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setModal(false)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleCreate} disabled={!form.name || !form.project_id}>Crear</button>
          </div>
        </Modal>
      )}

      {editModal && (
        <Modal title={`Editar: ${editModal.name}`} onClose={() => setEditModal(null)}>
          <Field label="Link Drive"><input className={inputClass} value={editForm.drive_url} onChange={e => setEditForm({...editForm, drive_url: e.target.value})} /></Field>
          <Field label="Versión actual"><input className={inputClass} value={editForm.current_version} onChange={e => setEditForm({...editForm, current_version: e.target.value})} /></Field>
          <Field label="Notas"><textarea className={inputClass} rows={2} value={editForm.notes} onChange={e => setEditForm({...editForm, notes: e.target.value})} /></Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setEditModal(null)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleEdit}>Guardar</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── ASSIGNMENTS (fixed: no conditional hooks) ─────────────────────────────
function AssignmentsSection() {
  const { data: assets }  = useData("/assets");
  const { data: persons } = useData("/persons");
  const { data: teams }   = useData("/teams");
  const { data: projects } = useData("/projects");

  const [allAssignments, setAllAssignments] = useState([]);
  const [loadingAll, setLoadingAll]         = useState(false);
  const [modal, setModal]                   = useState(false);
  const [statusModal, setStatusModal]       = useState(null);
  const [form, setForm]       = useState({ asset_id: "", person_id: "", notes: "", created_by: "admin" });
  const [statusForm, setStatusForm] = useState({ status: "", changed_by: "admin", note: "" });
  const [filterTeam, setFilterTeam]     = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showDone, setShowDone]         = useState(true);

  const loadAllAssignments = useCallback(async (personList) => {
    if (!personList || personList.length === 0) return;
    setLoadingAll(true);
    try {
      const results = await Promise.all(
        personList.map(p =>
          api.get(`/persons/${p.id}/assignments?include_done=true`)
            .then(r => r.assignments || [])
            .catch(() => [])
        )
      );
      const flat = results.flat();
      const seen = new Set();
      setAllAssignments(flat.filter(a => {
        if (seen.has(a.id)) return false;
        seen.add(a.id);
        return true;
      }));
    } finally {
      setLoadingAll(false);
    }
  }, []);

  useEffect(() => {
    if (persons) loadAllAssignments(persons);
  }, [persons, loadAllAssignments]);

  async function handleCreate() {
    await api.post("/assignments", {
      ...form,
      asset_id: parseInt(form.asset_id),
      person_id: parseInt(form.person_id),
    });
    setModal(false);
    setForm({ asset_id: "", person_id: "", notes: "", created_by: "admin" });
    if (persons) loadAllAssignments(persons);
  }

  async function handleStatusChange() {
    await api.patch(`/assignments/${statusModal.id}/status`, statusForm);
    setStatusModal(null);
    if (persons) loadAllAssignments(persons);
  }

  const filtered = allAssignments.filter(a => {
    if (!showDone && a.status === "done") return false;
    if (filterTeam   && String(a.person?.team_id) !== filterTeam) return false;
    if (filterStatus && a.status !== filterStatus) return false;
    return true;
  });

  return (
    <div>
      <SectionHeader title="Asignaciones" count={filtered.length} onAdd={() => setModal(true)} />

      <div className="flex gap-2 mb-4 flex-wrap items-center">
        <select className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-amber-500"
          value={filterTeam} onChange={e => setFilterTeam(e.target.value)}>
          <option value="">Todos los equipos</option>
          {teams?.map(t => {
            const proj = projects?.find(p => p.id === t.project_id);
            return <option key={t.id} value={String(t.id)}>{t.name}{proj ? ` · ${proj.name}` : ""}</option>;
          })}
        </select>
        <select className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-amber-500"
          value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_COLORS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <button
          onClick={() => setShowDone(v => !v)}
          className={`px-3 py-1.5 text-[10px] font-bold tracking-widest uppercase rounded border transition-colors ${
            showDone
              ? "bg-emerald-900/40 border-emerald-700 text-emerald-400"
              : "bg-zinc-800 border-zinc-700 text-zinc-500"
          }`}
        >
          {showDone ? "✅ Listos visibles" : "✅ Listos ocultos"}
        </button>
      </div>

      {loadingAll ? <Spinner /> : (
        <div className="grid gap-3">
          {filtered.map(a => {
            const team = teams?.find(t => t.id === a.person?.team_id);
            return (
              <div key={a.id} className="bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-4 hover:border-zinc-600 transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <StatusBadge status={a.status} />
                      {a.asset?.current_version && (
                        <span className="text-[10px] font-mono bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded">{a.asset.current_version}</span>
                      )}
                    </div>
                    <div className="text-sm font-semibold text-white truncate">{a.asset?.name}</div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="w-4 h-4 rounded-full bg-zinc-700 flex items-center justify-center text-[8px] font-bold text-amber-400">
                        {a.person?.name?.charAt(0)}
                      </div>
                      <span className="text-xs text-zinc-400">{a.person?.name}</span>
                      {team && <span className="text-[10px] text-zinc-600">· {teamLabel(team, projects)}</span>}
                    </div>
                    {a.notes && <div className="text-xs text-zinc-600 mt-1 italic">"{a.notes}"</div>}
                  </div>
                  <button
                    onClick={() => { setStatusModal(a); setStatusForm({ status: a.status, changed_by: "admin", note: "" }); }}
                    className="text-[10px] text-zinc-600 hover:text-amber-400 transition-colors shrink-0 border border-zinc-700 hover:border-amber-500 rounded px-2 py-1"
                  >
                    ESTADO
                  </button>
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && <Empty text="Sin asignaciones" />}
        </div>
      )}

      {modal && (
        <Modal title="Nueva Asignación" onClose={() => setModal(false)}>
          <Field label="Asset">
            <select className={inputClass} value={form.asset_id} onChange={e => setForm({...form, asset_id: e.target.value})}>
              <option value="">— Seleccionar —</option>
              {assets?.map(a => <option key={a.id} value={a.id}>{a.name}{a.current_version ? ` (${a.current_version})` : ""}</option>)}
            </select>
          </Field>
          <Field label="Persona">
            <select className={inputClass} value={form.person_id} onChange={e => setForm({...form, person_id: e.target.value})}>
              <option value="">— Seleccionar —</option>
              {persons?.map(p => {
                const team = teams?.find(t => t.id === p.team_id);
                return <option key={p.id} value={p.id}>{p.name}{team ? ` — ${teamLabel(team, projects)}` : ""}</option>;
              })}
            </select>
          </Field>
          <Field label="Notas para el trabajador">
            <textarea className={inputClass} rows={2} value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          </Field>
          <Field label="Asignado por">
            <input className={inputClass} value={form.created_by} onChange={e => setForm({...form, created_by: e.target.value})} />
          </Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setModal(false)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleCreate} disabled={!form.asset_id || !form.person_id}>Asignar</button>
          </div>
        </Modal>
      )}

      {statusModal && (
        <Modal title={`Cambiar estado: ${statusModal.asset?.name}`} onClose={() => setStatusModal(null)}>
          <Field label="Nuevo estado">
            <select className={inputClass} value={statusForm.status} onChange={e => setStatusForm({...statusForm, status: e.target.value})}>
              {Object.entries(STATUS_COLORS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </Field>
          <Field label="Nota (opcional)">
            <input className={inputClass} value={statusForm.note} onChange={e => setStatusForm({...statusForm, note: e.target.value})} />
          </Field>
          <Field label="Cambiado por">
            <input className={inputClass} value={statusForm.changed_by} onChange={e => setStatusForm({...statusForm, changed_by: e.target.value})} />
          </Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setStatusModal(null)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleStatusChange}>Guardar</button>
          </div>
        </Modal>
      )}
    </div>
  );
}


// ─── HELP SECTION ──────────────────────────────────────────────────────────
function HelpSection() {
  const [tab, setTab] = useState("workers");
  return (
    <div>
      <SectionHeader title="Ayuda" />
      <div className="flex gap-0 border-b border-zinc-800 mb-6">
        {[["workers", "👷 Para trabajadores"], ["admins", "🛠 Para admins"]].map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)}
            className={`px-4 py-2 text-[11px] font-bold tracking-widest uppercase transition-colors border-b-2 ${
              tab === id ? "text-amber-400 border-amber-400" : "text-zinc-500 border-transparent hover:text-zinc-300"
            }`}>
            {label}
          </button>
        ))}
      </div>

      {tab === "workers" && (
        <div className="space-y-4 text-sm">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-xs font-bold tracking-widest text-amber-400 uppercase mb-3">Primeros pasos</h3>
            <ol className="space-y-2 text-zinc-300 list-decimal list-inside">
              <li>Buscá el bot en Telegram por su nombre.</li>
              <li>Mandále <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-amber-300">/start</code> — te va a mostrar tu <b>Telegram ID</b>.</li>
              <li>Pasale ese número a tu admin para que te registre en el sistema.</li>
              <li>Una vez registrado, podés escribirle al bot en lenguaje natural.</li>
            </ol>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-xs font-bold tracking-widest text-amber-400 uppercase mb-3">¿Qué puedo preguntarle?</h3>
            <div className="space-y-3">
              {[
                ["📋 Ver mis archivos", ["qué tengo asignado", "mis tareas", "qué me toca hacer"]],
                ["👥 Ver mi equipo", ["cómo está el equipo", "qué están haciendo todos", "asignaciones del equipo"]],
                ["🔍 Buscar un archivo", ["quién tiene el comp final", "cómo está la escena 4", "busco el modelo"]],
                ["🔶 Avisar que empecé", ["empecé con la escena 4", "arranqué el comp", "estoy trabajando en el audio"]],
                ["✅ Avisar que terminé", ["terminé la escena 4", "listo el comp", "entregué el modelo"]],
                ["🔴 Reportar un bloqueo", ["estoy bloqueado en la escena 4", "no puedo avanzar con el audio"]],
              ].map(([title, examples]) => (
                <div key={title}>
                  <div className="text-xs font-bold text-zinc-300 mb-1">{title}</div>
                  <div className="flex flex-wrap gap-1.5">
                    {examples.map(ex => (
                      <span key={ex} className="text-[11px] bg-zinc-800 text-zinc-400 px-2 py-1 rounded italic">"{ex}"</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-xs font-bold tracking-widest text-amber-400 uppercase mb-3">En grupos</h3>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Si el bot está en un grupo de Telegram, tenés que etiquetarlo para que responda:<br/>
              <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-amber-300 mt-1 inline-block">@nombre_del_bot qué tengo asignado?</code><br/><br/>
              También podés responder un mensaje del bot directamente y te va a escuchar sin necesidad de etiquetarlo.
            </p>
          </div>
        </div>
      )}

      {tab === "admins" && (
        <div className="space-y-4 text-sm">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-xs font-bold tracking-widest text-amber-400 uppercase mb-3">Flujo de setup inicial</h3>
            <ol className="space-y-2 text-zinc-300 list-decimal list-inside">
              <li>Creá un <b>Proyecto</b> en la pestaña Proyectos.</li>
              <li>Creá los <b>Equipos</b> que participan (Edición, Sonido, FX, etc.).</li>
              <li>Registrá a cada <b>Persona</b> con su nombre y equipo. El Telegram ID lo obtienen ellos con <code className="bg-zinc-800 px-1 rounded text-amber-300">/start</code>.</li>
              <li>Cargá los <b>Assets</b> con su link de Drive y versión actual.</li>
              <li>Creá <b>Asignaciones</b> para indicar quién trabaja qué.</li>
            </ol>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-xs font-bold tracking-widest text-amber-400 uppercase mb-3">Gestión de asignaciones</h3>
            <div className="space-y-2 text-xs text-zinc-400 leading-relaxed">
              <p>• Los estados son: <span className="text-zinc-300">PENDIENTE → EN CURSO → LISTO</span> (o BLOQUEADO en cualquier momento).</p>
              <p>• Los trabajadores cambian su propio estado desde el bot. Vos podés cambiarlo desde el panel con el botón <b>ESTADO</b>.</p>
              <p>• Las asignaciones completadas no desaparecen — usá el toggle <b>✅ Listos visibles/ocultos</b> para mostrarlas u ocultarlas.</p>
              <p>• Cada cambio de estado queda registrado en el log con quién lo hizo y cuándo.</p>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-xs font-bold tracking-widest text-amber-400 uppercase mb-3">Actualizar versiones</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Cuando sube una nueva versión de un asset, entrá a <b>Assets</b>, buscalo y hacé clic en <b>EDITAR</b>. 
              Actualizá el link de Drive y el campo de versión. Los trabajadores asignados verán el nuevo link la próxima vez que consulten al bot.
            </p>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-xs font-bold tracking-widest text-amber-400 uppercase mb-3">Registrar un trabajador</h3>
            <ol className="space-y-1 text-xs text-zinc-400 list-decimal list-inside">
              <li>El trabajador manda <code className="bg-zinc-800 px-1 rounded text-amber-300">/start</code> al bot y copia su Telegram ID.</li>
              <li>En la pestaña <b>Personas</b>, creá su perfil o editá uno existente.</li>
              <li>Pegá el Telegram ID en el campo correspondiente.</li>
              <li>Ya puede usar el bot.</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── MAIN APP ──────────────────────────────────────────────────────────────
const TABS = [
  { id: "assignments", label: "Asignaciones" },
  { id: "assets",      label: "Assets"       },
  { id: "persons",     label: "Personas"     },
  { id: "teams",       label: "Equipos"      },
  { id: "projects",    label: "Proyectos"    },
  { id: "help",        label: "Ayuda"        },
];

export default function App() {
  const [tab, setTab]           = useState("assignments");
  const [apiBase, setApiBase]   = useState(window.__API_BASE__ || "http://localhost:8000");
  const [showConfig, setShowConfig] = useState(false);

  return (
    <div className="min-h-screen bg-zinc-950 text-white" style={{fontFamily: "'DM Mono', 'Fira Code', monospace"}}>
      <header className="border-b border-zinc-800 px-6 py-3 flex items-center justify-between sticky top-0 bg-zinc-950/95 backdrop-blur z-40">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="text-xs font-bold tracking-[0.2em] text-white uppercase">Asset Manager</span>
          <span className="text-[10px] text-zinc-600 tracking-widest hidden sm:block">// Panel Admin</span>
        </div>
        <button onClick={() => setShowConfig(!showConfig)} className="text-[10px] text-zinc-600 hover:text-zinc-400 tracking-widest uppercase transition-colors">
          API: {apiBase.replace("http://", "").replace("https://", "")}
        </button>
      </header>

      {showConfig && (
        <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-3 flex items-center gap-3">
          <span className="text-[10px] text-zinc-500 uppercase tracking-widest shrink-0">Base URL</span>
          <input
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500 font-mono"
            value={apiBase}
            onChange={e => { setApiBase(e.target.value); window.__API_BASE__ = e.target.value; }}
          />
          <button className={btnPrimary} onClick={() => setShowConfig(false)}>OK</button>
        </div>
      )}

      <nav className="border-b border-zinc-800 px-6 flex gap-0 overflow-x-auto">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-3 text-[11px] font-bold tracking-widest uppercase transition-colors whitespace-nowrap border-b-2 ${
              tab === t.id ? "text-amber-400 border-amber-400" : "text-zinc-500 border-transparent hover:text-zinc-300"
            }`}>
            {t.label}
          </button>
        ))}
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {tab === "projects"    && <ProjectsSection />}
        {tab === "help"        && <HelpSection />}
        {tab === "teams"       && <TeamsSection />}
        {tab === "persons"     && <PersonsSection />}
        {tab === "assets"      && <AssetsSection />}
        {tab === "assignments" && <AssignmentsSection />}
      </main>
    </div>
  );
}