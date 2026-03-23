import { useState, useEffect, useCallback } from "react";

// ─── CONFIG ────────────────────────────────────────────────────────────────
const API = (window.__API_BASE__ || "http://localhost:8000").replace(/\/$/, "");

const STATUS_COLORS = {
  pending:     { bg: "bg-zinc-700",   text: "text-zinc-300",   dot: "bg-zinc-400",   label: "PENDIENTE"  },
  in_progress: { bg: "bg-amber-900/60", text: "text-amber-300", dot: "bg-amber-400",  label: "EN CURSO"   },
  done:        { bg: "bg-emerald-900/50", text: "text-emerald-300", dot: "bg-emerald-400", label: "LISTO" },
  blocked:     { bg: "bg-red-900/50",  text: "text-red-300",    dot: "bg-red-400",    label: "BLOQUEADO"  },
};

const api = {
  get:   (path) => fetch(`${API}${path}`).then(r => r.json()),
  post:  (path, body) => fetch(`${API}${path}`, { method:"POST",  headers:{"Content-Type":"application/json"}, body: JSON.stringify(body) }).then(r => r.json()),
  patch: (path, body) => fetch(`${API}${path}`, { method:"PATCH", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body) }).then(r => r.json()),
};

// ─── HOOKS ─────────────────────────────────────────────────────────────────
function useData(path, deps = []) {
  const [data, setData]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const reload = useCallback(() => {
    setLoading(true);
    api.get(path).then(setData).catch(setError).finally(() => setLoading(false));
  }, [path]);
  useEffect(() => { reload(); }, [reload, ...deps]);
  return { data, loading, error, reload };
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

const inputClass = "w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 transition-colors";
const btnPrimary = "px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black text-xs font-bold tracking-widest uppercase rounded transition-colors";
const btnGhost   = "px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-bold tracking-widest uppercase rounded transition-colors border border-zinc-700";

// ─── SECTIONS ──────────────────────────────────────────────────────────────

// PROJECTS
function ProjectsSection() {
  const { data: projects, loading, reload } = useData("/projects");
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });

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
            <div key={p.id} className="bg-zinc-900 border border-zinc-800 rounded-lg px-5 py-4 flex items-center justify-between group hover:border-zinc-600 transition-colors">
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

// TEAMS
function TeamsSection() {
  const { data: teams, loading, reload } = useData("/teams");
  const { data: projects } = useData("/projects");
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ name: "", project_id: "" });

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
                  {proj && <div className="text-xs text-zinc-500 mt-0.5">{proj.name}</div>}
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

// PERSONS
function PersonsSection() {
  const { data: persons, loading, reload } = useData("/persons");
  const { data: teams } = useData("/teams");
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ name: "", whatsapp_number: "", team_id: "" });

  async function handleCreate() {
    await api.post("/persons", { ...form, team_id: parseInt(form.team_id) });
    setModal(false); setForm({ name: "", whatsapp_number: "", team_id: "" }); reload();
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
                    <div className="text-xs text-zinc-500">{p.whatsapp_number} {team && `· ${team.name}`}</div>
                  </div>
                </div>
                <div className="text-[10px] text-zinc-600 font-mono">#{p.id}</div>
              </div>
            );
          })}
          {persons?.length === 0 && <Empty text="Sin personas aún" />}
        </div>
      )}
      {modal && (
        <Modal title="Nueva Persona" onClose={() => setModal(false)}>
          <Field label="Nombre"><input className={inputClass} value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Ana García" /></Field>
          <Field label="WhatsApp (con código de país)"><input className={inputClass} value={form.whatsapp_number} onChange={e => setForm({...form, whatsapp_number: e.target.value})} placeholder="+5491155555555" /></Field>
          <Field label="Equipo">
            <select className={inputClass} value={form.team_id} onChange={e => setForm({...form, team_id: e.target.value})}>
              <option value="">— Seleccionar —</option>
              {teams?.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setModal(false)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleCreate} disabled={!form.name || !form.whatsapp_number || !form.team_id}>Crear</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ASSETS
function AssetsSection() {
  const { data: assets, loading, reload } = useData("/assets");
  const { data: projects } = useData("/projects");
  const [modal, setModal] = useState(false);
  const [editModal, setEditModal] = useState(null);
  const [form, setForm]     = useState({ name: "", project_id: "", drive_url: "", current_version: "", notes: "" });
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
                      <a href={a.drive_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-zinc-500 hover:text-amber-400 mt-1 transition-colors truncate max-w-xs">
                        <span>↗</span> Drive
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

// ASSIGNMENTS
function AssignmentsSection() {
  const { data: assignments, loading, reload } = useData("/assignments/team/0").data ? useData("/assignments/team/0") : { data: null, loading: false };
  const { data: assets }   = useData("/assets");
  const { data: persons }  = useData("/persons");
  const { data: teams }    = useData("/teams");
  const [allAssignments, setAllAssignments] = useState([]);
  const [loadingAll, setLoadingAll] = useState(true);
  const [modal, setModal]  = useState(false);
  const [statusModal, setStatusModal] = useState(null);
  const [form, setForm]    = useState({ asset_id: "", person_id: "", notes: "", created_by: "admin" });
  const [statusForm, setStatusForm] = useState({ status: "", changed_by: "admin", note: "" });
  const [filterTeam, setFilterTeam] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Load all assignments by loading each person's assignments
  useEffect(() => {
    if (!persons) return;
    async function loadAll() {
      setLoadingAll(true);
      try {
        const results = await Promise.all(
          persons.map(p => api.get(`/persons/${p.id}/assignments`).then(r => r.assignments || []).catch(() => []))
        );
        const flat = results.flat();
        // deduplicate by id
        const seen = new Set();
        const deduped = flat.filter(a => { if (seen.has(a.id)) return false; seen.add(a.id); return true; });
        setAllAssignments(deduped);
      } finally {
        setLoadingAll(false);
      }
    }
    loadAll();
  }, [persons]);

  async function handleCreate() {
    await api.post("/assignments", { ...form, asset_id: parseInt(form.asset_id), person_id: parseInt(form.person_id) });
    setModal(false); setForm({ asset_id:"", person_id:"", notes:"", created_by:"admin" });
    // reload
    if (persons) {
      const results = await Promise.all(
        persons.map(p => api.get(`/persons/${p.id}/assignments`).then(r => r.assignments || []).catch(() => []))
      );
      const flat = results.flat();
      const seen = new Set();
      setAllAssignments(flat.filter(a => { if (seen.has(a.id)) return false; seen.add(a.id); return true; }));
    }
  }

  async function handleStatusChange() {
    await api.patch(`/assignments/${statusModal.id}/status`, statusForm);
    setStatusModal(null);
    if (persons) {
      const results = await Promise.all(
        persons.map(p => api.get(`/persons/${p.id}/assignments`).then(r => r.assignments || []).catch(() => []))
      );
      const flat = results.flat();
      const seen = new Set();
      setAllAssignments(flat.filter(a => { if (seen.has(a.id)) return false; seen.add(a.id); return true; }));
    }
  }

  const filtered = allAssignments.filter(a => {
    if (filterTeam && a.person?.team_id !== parseInt(filterTeam)) return false;
    if (filterStatus && a.status !== filterStatus) return false;
    return true;
  });

  return (
    <div>
      <SectionHeader title="Asignaciones" count={allAssignments.length} onAdd={() => setModal(true)} />

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <select className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-amber-500"
          value={filterTeam} onChange={e => setFilterTeam(e.target.value)}>
          <option value="">Todos los equipos</option>
          {teams?.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-amber-500"
          value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_COLORS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
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
                      {team && <span className="text-[10px] text-zinc-600">· {team.name}</span>}
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
                return <option key={p.id} value={p.id}>{p.name}{team ? ` — ${team.name}` : ""}</option>;
              })}
            </select>
          </Field>
          <Field label="Notas para el trabajador"><textarea className={inputClass} rows={2} value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} /></Field>
          <Field label="Asignado por"><input className={inputClass} value={form.created_by} onChange={e => setForm({...form, created_by: e.target.value})} /></Field>
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
          <Field label="Nota (opcional)"><input className={inputClass} value={statusForm.note} onChange={e => setStatusForm({...statusForm, note: e.target.value})} /></Field>
          <Field label="Cambiado por"><input className={inputClass} value={statusForm.changed_by} onChange={e => setStatusForm({...statusForm, changed_by: e.target.value})} /></Field>
          <div className="flex gap-2 justify-end mt-2">
            <button className={btnGhost} onClick={() => setStatusModal(null)}>Cancelar</button>
            <button className={btnPrimary} onClick={handleStatusChange}>Guardar</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── SHARED COMPONENTS ─────────────────────────────────────────────────────
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

// ─── MAIN APP ──────────────────────────────────────────────────────────────
const TABS = [
  { id: "assignments", label: "Asignaciones" },
  { id: "assets",      label: "Assets"       },
  { id: "persons",     label: "Personas"     },
  { id: "teams",       label: "Equipos"      },
  { id: "projects",    label: "Proyectos"    },
];

export default function App() {
  const [tab, setTab] = useState("assignments");
  const [apiBase, setApiBase] = useState(window.__API_BASE__ || "http://localhost:8000");
  const [showConfig, setShowConfig] = useState(false);

  return (
    <div className="min-h-screen bg-zinc-950 text-white" style={{fontFamily: "'DM Mono', 'Fira Code', monospace"}}>
      {/* Top bar */}
      <header className="border-b border-zinc-800 px-6 py-3 flex items-center justify-between sticky top-0 bg-zinc-950/95 backdrop-blur z-40">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span className="text-xs font-bold tracking-[0.2em] text-white uppercase">Asset Manager</span>
          <span className="text-[10px] text-zinc-600 tracking-widest hidden sm:block">// Panel Admin</span>
        </div>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-[10px] text-zinc-600 hover:text-zinc-400 tracking-widest uppercase transition-colors"
        >
          API: {apiBase.replace("http://", "").replace("https://", "")}
        </button>
      </header>

      {/* API config bar */}
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

      {/* Tabs */}
      <nav className="border-b border-zinc-800 px-6 flex gap-0 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-3 text-[11px] font-bold tracking-widest uppercase transition-colors whitespace-nowrap border-b-2 ${
              tab === t.id
                ? "text-amber-400 border-amber-400"
                : "text-zinc-500 border-transparent hover:text-zinc-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        {tab === "projects"    && <ProjectsSection />}
        {tab === "teams"       && <TeamsSection />}
        {tab === "persons"     && <PersonsSection />}
        {tab === "assets"      && <AssetsSection />}
        {tab === "assignments" && <AssignmentsSection />}
      </main>
    </div>
  );
}