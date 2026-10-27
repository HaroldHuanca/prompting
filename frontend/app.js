/**
 * Controlador de Frontend: Prompt Engineering Research Lab
 * Gestiona: Ingesta de Problemas (LeetCode), Ejecución Experimental y Matriz Comparativa.
 */

// ==============================================================================
// ESTADO GLOBAL DE LA APLICACIÓN
// ==============================================================================
const state = {
  problems: [],
  selectedProblemId: null,
  selectedTechnique: "ZERO_SHOT",
  activeTab: "ingesta",
  currentExecution: null,
  matrixData: []
};

// ==============================================================================
// INICIALIZACIÓN
// ==============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  await loadProblems();
  if (state.problems.length > 0) {
    selectProblemForEditing(state.problems[0].problema_id);
    populateExperimentProblemSelect();
    await updatePromptPreview();
  }
  await loadComparativeMatrix();
  await loadTechniqueSummaries();
  await loadDeterminismAudit();
});

// ==============================================================================
// NAVEGACIÓN ENTRE TABS
// ==============================================================================
function switchTab(tabId) {
  state.activeTab = tabId;

  // Actualizar botones de navegación
  document.querySelectorAll(".nav-tab-btn").forEach(btn => btn.classList.remove("active"));
  const activeBtn = document.getElementById(`tab-btn-${tabId}`);
  if (activeBtn) activeBtn.classList.add("active");

  // Actualizar paneles visibles
  document.querySelectorAll(".view-panel").forEach(panel => panel.classList.remove("active"));
  const activePanel = document.getElementById(`view-${tabId}`);
  if (activePanel) activePanel.classList.add("active");

  if (tabId === "ejecucion") {
    populateExperimentProblemSelect();
    updatePromptPreview();
  } else if (tabId === "resultados") {
    loadComparativeMatrix();
    loadTechniqueSummaries();
    loadDeterminismAudit();
  }
}

// ==============================================================================
// INTERFAZ 1: INGESTA Y GESTIÓN DE PROBLEMAS (LEETCODE)
// ==============================================================================
async function loadProblems() {
  try {
    const res = await fetch("/api/problemas");
    if (!res.ok) throw new Error("Error al consultar problemas");
    state.problems = await res.json();
    renderProblemList(state.problems);
    document.getElementById("problemas-count").textContent = state.problems.length;
  } catch (err) {
    showToast(`Error al cargar problemas: ${err.message}`, "error");
  }
}

function renderProblemList(items) {
  const container = document.getElementById("lista-problemas");
  container.innerHTML = "";

  if (items.length === 0) {
    container.innerHTML = `<div style="padding: 1rem; color: var(--text-muted); text-align: center;">No hay problemas registrados</div>`;
    return;
  }

  items.forEach(p => {
    const div = document.createElement("div");
    div.className = `problem-card-item ${p.problema_id === state.selectedProblemId ? "selected" : ""}`;
    div.id = `problem-item-${p.problema_id}`;
    div.onclick = () => selectProblemForEditing(p.problema_id);

    const diffClass = p.dificultad === "Fácil" ? "badge-facil" : (p.dificultad === "Media" ? "badge-media" : "badge-dificil");

    div.innerHTML = `
      <div class="item-top">
        <span class="item-code">${escapeHtml(p.codigo)}</span>
        <span class="badge-pill ${diffClass}">${escapeHtml(p.dificultad)}</span>
      </div>
      <div class="item-title">${escapeHtml(p.titulo)}</div>
      <div class="item-meta">
        <span>⭐ Few-Shot: ${p.cantidad_ejemplos_few_shot || 0}</span>
        <span>•</span>
        <span>🧪 Pruebas: ${(p.pruebas_funcionales || []).length}</span>
      </div>
    `;
    container.appendChild(div);
  });
}

function filterProblemList() {
  const q = document.getElementById("filtro-problemas-busqueda").value.toLowerCase().trim();
  const filtered = state.problems.filter(p => 
    p.codigo.toLowerCase().includes(q) || 
    p.titulo.toLowerCase().includes(q) ||
    (p.categoria_algoritmica || "").toLowerCase().includes(q)
  );
  renderProblemList(filtered);
}

function selectProblemForEditing(id) {
  state.selectedProblemId = id;
  const p = state.problems.find(x => x.problema_id === id);
  if (!p) return;

  // Resaltar item seleccionado
  document.querySelectorAll(".problem-card-item").forEach(el => el.classList.remove("selected"));
  const item = document.getElementById(`problem-item-${id}`);
  if (item) item.classList.add("selected");

  // Llenar campos principales
  document.getElementById("form-problema-id").value = p.problema_id;
  document.getElementById("form-codigo").value = p.codigo;
  document.getElementById("form-titulo").value = p.titulo;
  document.getElementById("form-dificultad").value = p.dificultad;
  document.getElementById("form-categoria").value = p.categoria_algoritmica || "";
  document.getElementById("form-plataforma").value = p.plataforma_origen || "LeetCode";
  document.getElementById("form-url").value = p.url_referencia || "";
  document.getElementById("form-enunciado").value = p.enunciado || "";
  document.getElementById("form-restricciones").value = p.restricciones || "";
  document.getElementById("form-solucion-ref").value = p.solucion_referencia || "";

  // Renderizar ejemplos oficiales del enunciado
  const enunciadoContainer = document.getElementById("enunciado-examples-container");
  enunciadoContainer.innerHTML = "";
  (p.ejemplos_enunciado || []).forEach(ej => addEnunciadoExampleRow(ej));

  // Renderizar demostraciones Few-Shot
  const fewShotContainer = document.getElementById("few-shot-examples-container");
  fewShotContainer.innerHTML = "";
  (p.ejemplos_few_shot || []).forEach(fs => addFewShotExampleRow(fs));

  // Renderizar casos de prueba Pytest
  const testContainer = document.getElementById("test-cases-container");
  testContainer.innerHTML = "";
  (p.pruebas_funcionales || []).forEach(tc => addTestCaseRow(tc));
}

function resetProblemForm() {
  state.selectedProblemId = null;
  document.getElementById("form-problema-id").value = "";
  document.getElementById("form-problema").reset();
  document.getElementById("enunciado-examples-container").innerHTML = "";
  document.getElementById("few-shot-examples-container").innerHTML = "";
  document.getElementById("test-cases-container").innerHTML = "";
  
  // Agregar al menos 1 fila vacía en cada sección
  addEnunciadoExampleRow();
  addFewShotExampleRow();
  addTestCaseRow();

  document.querySelectorAll(".problem-card-item").forEach(el => el.classList.remove("selected"));
  showToast("Formulario limpio para registrar nuevo problema", "info");
}

// Generadores de filas dinámicas
function addEnunciadoExampleRow(data = {}) {
  const container = document.getElementById("enunciado-examples-container");
  const idx = container.children.length + 1;
  const row = document.createElement("div");
  row.className = "dynamic-row-card";
  row.innerHTML = `
    <button type="button" class="row-delete-btn" onclick="this.parentElement.remove()" title="Eliminar fila">&times;</button>
    <div class="form-row grid-2" style="margin-bottom: 0.5rem;">
      <div class="form-group" style="margin-bottom: 0;">
        <label>Entrada (Input) Ejemplo ${idx}</label>
        <input type="text" class="form-control ej-enunciado-entrada" placeholder="nums = [2,7,11,15], target = 9" value="${escapeHtml(data.entrada || '')}">
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label>Salida (Output)</label>
        <input type="text" class="form-control ej-enunciado-salida" placeholder="[0,1]" value="${escapeHtml(data.salida || '')}">
      </div>
    </div>
    <div class="form-group" style="margin-bottom: 0;">
      <label>Explicación (Opcional)</label>
      <input type="text" class="form-control ej-enunciado-explicacion" placeholder="nums[0] + nums[1] == 9, retornamos [0, 1]." value="${escapeHtml(data.explicacion || '')}">
    </div>
  `;
  container.appendChild(row);
}

function addFewShotExampleRow(data = {}) {
  const container = document.getElementById("few-shot-examples-container");
  const idx = container.children.length + 1;
  const row = document.createElement("div");
  row.className = "dynamic-row-card few-shot-row";
  row.innerHTML = `
    <button type="button" class="row-delete-btn" onclick="this.parentElement.remove()" title="Eliminar demostración Few-Shot">&times;</button>
    <div class="form-row grid-3" style="margin-bottom: 0.5rem;">
      <div class="form-group" style="margin-bottom: 0;">
        <label>Descripción / Estrategia Demostrada</label>
        <input type="text" class="form-control fs-desc" placeholder="Demostración con Hash Map O(1)" value="${escapeHtml(data.descripcion || '')}">
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label>Entrada Demostración ${idx}</label>
        <input type="text" class="form-control fs-entrada" placeholder="nums = [3,2,4], target = 6" value="${escapeHtml(data.entrada || '')}">
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label>Salida Esperada</label>
        <input type="text" class="form-control fs-salida" placeholder="[1,2]" value="${escapeHtml(data.salida || '')}">
      </div>
    </div>
    <div class="form-row grid-2">
      <div class="form-group" style="margin-bottom: 0;">
        <label>Razonamiento Explicativo</label>
        <textarea class="form-control fs-explicacion" rows="2" placeholder="Explicación del paso lógico para el Few-Shot prompt...">${escapeHtml(data.explicacion || '')}</textarea>
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label>Código Ilustrativo de la Demostración (Opcional)</label>
        <textarea class="form-control code-font fs-codigo" rows="2" placeholder="def helper(): ...">${escapeHtml(data.codigo_ilustrativo || '')}</textarea>
      </div>
    </div>
  `;
  container.appendChild(row);
}

function addTestCaseRow(data = {}) {
  const container = document.getElementById("test-cases-container");
  const idx = container.children.length + 1;
  const row = document.createElement("div");
  row.className = "dynamic-row-card";
  row.innerHTML = `
    <button type="button" class="row-delete-btn" onclick="this.parentElement.remove()" title="Eliminar caso de prueba">&times;</button>
    <div class="form-row grid-3">
      <div class="form-group" style="margin-bottom: 0;">
        <label>Identificador Prueba ${idx}</label>
        <input type="text" class="form-control tc-nombre" placeholder="test_caso_base" value="${escapeHtml(data.nombre || `test_caso_${idx}`)}">
      </div>
      <div class="form-group span-2" style="margin-bottom: 0;">
        <label>Aserción Pytest (Código ejecutable)</label>
        <input type="text" class="form-control code-font tc-codigo" placeholder="assert Solution().twoSum([2, 7, 11, 15], 9) in [[0, 1], [1, 0]]" value="${escapeHtml(data.codigo || '')}">
      </div>
    </div>
  `;
  container.appendChild(row);
}

// ==============================================================================
// IMPORTACIÓN DINÁMICA DESDE ARCHIVO JSON
// ==============================================================================
function handleJsonFileImport(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      let data = JSON.parse(e.target.result);
      if (Array.isArray(data)) {
        if (data.length === 0) throw new Error("El archivo JSON contiene una lista vacía.");
        data = data[0];
      }

      if (!data.codigo || !data.titulo) {
        throw new Error("El JSON debe contener al menos los campos 'codigo' y 'titulo'.");
      }

      const existente = state.problems.find(p => p.codigo === data.codigo);
      if (existente) {
        document.getElementById("form-problema-id").value = existente.problema_id;
        state.selectedProblemId = existente.problema_id;
        showToast(`Problema existente [${data.codigo}] detectado. Modo actualización habilitado.`, "info");
      } else {
        document.getElementById("form-problema-id").value = "";
        state.selectedProblemId = null;
        showToast(`Nuevo problema [${data.codigo}] cargado en el formulario.`, "success");
      }

      document.getElementById("form-codigo").value = data.codigo || "";
      document.getElementById("form-titulo").value = data.titulo || "";
      document.getElementById("form-dificultad").value = data.dificultad || "Media";
      document.getElementById("form-categoria").value = data.categoria_algoritmica || "";
      document.getElementById("form-plataforma").value = data.plataforma_origen || "LeetCode";
      document.getElementById("form-url").value = data.url_referencia || "";
      document.getElementById("form-enunciado").value = data.enunciado || "";
      document.getElementById("form-restricciones").value = data.restricciones || "";
      document.getElementById("form-solucion-ref").value = data.solucion_referencia || "";

      // Ejemplos de enunciado
      const enunciadoContainer = document.getElementById("enunciado-examples-container");
      enunciadoContainer.innerHTML = "";
      if (Array.isArray(data.ejemplos_enunciado) && data.ejemplos_enunciado.length > 0) {
        data.ejemplos_enunciado.forEach(ej => addEnunciadoExampleRow(ej));
      } else {
        addEnunciadoExampleRow();
      }

      // Demostraciones Few-Shot
      const fewShotContainer = document.getElementById("few-shot-examples-container");
      fewShotContainer.innerHTML = "";
      if (Array.isArray(data.ejemplos_few_shot) && data.ejemplos_few_shot.length > 0) {
        data.ejemplos_few_shot.forEach(fs => addFewShotExampleRow(fs));
      } else {
        addFewShotExampleRow();
      }

      // Casos de prueba Pytest
      const testContainer = document.getElementById("test-cases-container");
      testContainer.innerHTML = "";
      if (Array.isArray(data.pruebas_funcionales) && data.pruebas_funcionales.length > 0) {
        data.pruebas_funcionales.forEach(tc => addTestCaseRow(tc));
      } else {
        addTestCaseRow();
      }

      showToast(`Problema "${data.titulo}" cargado desde JSON. Presione 'Guardar Problema' para persistir.`, "success");
    } catch (err) {
      showToast(`Error al leer archivo JSON: ${err.message}`, "error");
    } finally {
      event.target.value = "";
    }
  };

  reader.onerror = function() {
    showToast("Error de lectura al abrir el archivo local.", "error");
    event.target.value = "";
  };

  reader.readAsText(file, "UTF-8");
}

async function saveProblem(event) {
  event.preventDefault();
  const idVal = document.getElementById("form-problema-id").value;
  const isUpdate = Boolean(idVal);

  // Recopilar ejemplos de enunciado
  const ejemplosEnunciado = [];
  document.querySelectorAll("#enunciado-examples-container .dynamic-row-card").forEach(card => {
    const ent = card.querySelector(".ej-enunciado-entrada")?.value.trim();
    const sal = card.querySelector(".ej-enunciado-salida")?.value.trim();
    const exp = card.querySelector(".ej-enunciado-explicacion")?.value.trim();
    if (ent || sal) {
      ejemplosEnunciado.push({ entrada: ent, salida: sal, explicacion: exp });
    }
  });

  // Recopilar demostraciones Few-Shot
  const ejemplosFewShot = [];
  document.querySelectorAll("#few-shot-examples-container .dynamic-row-card").forEach((card, i) => {
    const desc = card.querySelector(".fs-desc")?.value.trim();
    const ent = card.querySelector(".fs-entrada")?.value.trim();
    const sal = card.querySelector(".fs-salida")?.value.trim();
    const exp = card.querySelector(".fs-explicacion")?.value.trim();
    const cod = card.querySelector(".fs-codigo")?.value.trim();
    if (ent || sal || desc) {
      ejemplosFewShot.push({
        id: i + 1,
        descripcion: desc || `Demostración ${i + 1}`,
        entrada: ent,
        salida: sal,
        explicacion: exp,
        codigo_ilustrativo: cod
      });
    }
  });

  // Recopilar casos de prueba Pytest
  const pruebasFuncionales = [];
  document.querySelectorAll("#test-cases-container .dynamic-row-card").forEach((card, i) => {
    const nom = card.querySelector(".tc-nombre")?.value.trim() || `test_${i + 1}`;
    const cod = card.querySelector(".tc-codigo")?.value.trim();
    if (cod) {
      pruebasFuncionales.push({ nombre: nom, codigo: cod });
    }
  });

  const payload = {
    codigo: document.getElementById("form-codigo").value.trim(),
    titulo: document.getElementById("form-titulo").value.trim(),
    plataforma_origen: document.getElementById("form-plataforma").value,
    url_referencia: document.getElementById("form-url").value.trim() || null,
    dificultad: document.getElementById("form-dificultad").value,
    categoria_algoritmica: document.getElementById("form-categoria").value.trim() || null,
    enunciado: document.getElementById("form-enunciado").value.trim(),
    restricciones: document.getElementById("form-restricciones").value.trim() || null,
    solucion_referencia: document.getElementById("form-solucion-ref").value.trim() || null,
    ejemplos_enunciado: ejemplosEnunciado,
    ejemplos_few_shot: ejemplosFewShot,
    pruebas_funcionales: pruebasFuncionales,
    etiquetas: ["leetcode", document.getElementById("form-dificultad").value.toLowerCase()]
  };

  const btnSave = document.getElementById("btn-guardar-problema");
  btnSave.disabled = true;
  btnSave.textContent = "Guardando...";

  try {
    const url = isUpdate ? `/api/problemas/${idVal}` : "/api/problemas";
    const method = isUpdate ? "PUT" : "POST";
    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Error al guardar problema");
    }

    const saved = await res.json();
    showToast(`Problema ${saved.codigo} guardado exitosamente`, "success");
    await loadProblems();
    selectProblemForEditing(saved.problema_id);
    populateExperimentProblemSelect();
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    btnSave.disabled = false;
    btnSave.innerHTML = `<span>💾</span> Guardar Problema`;
  }
}

// ==============================================================================
// INTERFAZ 2: PANEL DE EJECUCIÓN EXPERIMENTAL Y CONFIGURACIÓN
// ==============================================================================
function populateExperimentProblemSelect() {
  const sel = document.getElementById("select-problema-experimento");
  const matrixSel = document.getElementById("filter-matrix-problema");
  
  sel.innerHTML = "";
  matrixSel.innerHTML = `<option value="">Todos los problemas</option>`;

  state.problems.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.problema_id;
    opt.textContent = `[${p.codigo}] ${p.titulo} (${p.dificultad})`;
    if (p.problema_id === state.selectedProblemId) opt.selected = true;
    sel.appendChild(opt);

    const optM = document.createElement("option");
    optM.value = p.problema_id;
    optM.textContent = `[${p.codigo}] ${p.titulo}`;
    matrixSel.appendChild(optM);
  });
}

function selectTechnique(techCode) {
  state.selectedTechnique = techCode;
  document.querySelectorAll("#technique-selector-group .tech-pill").forEach(pill => {
    pill.classList.toggle("active", pill.dataset.tech === techCode);
  });
  updatePromptPreview();
}

async function onProblemOrTechniqueChange() {
  const sel = document.getElementById("select-problema-experimento");
  state.selectedProblemId = parseInt(sel.value, 10);
  await updatePromptPreview();
}

async function updatePromptPreview() {
  const sel = document.getElementById("select-problema-experimento");
  if (!sel || !sel.value) return;

  const probId = parseInt(sel.value, 10);
  try {
    const res = await fetch("/api/prompts/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        problema_id: probId,
        tecnica_codigo: state.selectedTechnique
      })
    });
    if (!res.ok) return;

    const data = await res.json();
    document.getElementById("viewer-prompt-text").textContent = data.prompt;
    document.getElementById("prompt-char-count").textContent = `${data.prompt.length} caracteres`;
  } catch (err) {
    console.error("Error al previsualizar prompt:", err);
  }
}

async function runExperiment() {
  const sel = document.getElementById("select-problema-experimento");
  if (!sel || !sel.value) {
    showToast("Seleccione un problema para evaluar", "error");
    return;
  }

  const probId = parseInt(sel.value, 10);
  const rep = parseInt(document.getElementById("input-repeticion").value, 10) || 1;
  const btnRun = document.getElementById("btn-lanzar-experimento");
  const btnText = document.getElementById("btn-run-text");

  btnRun.disabled = true;
  btnText.textContent = "Ejecutando Pipeline...";
  showToast("Iniciando inferencia T=0.0 y evaluación automatizada...", "info");

  try {
    const res = await fetch("/api/ejecutar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        problema_id: probId,
        tecnica_codigo: state.selectedTechnique,
        numero_repeticion: rep
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error en la ejecución experimental");
    }

    const execData = await res.json();
    state.currentExecution = execData;
    renderExecutionResult(execData);
    showToast(`Ejecución #${execData.ejecucion_id} completada con éxito`, "success");

    // Refrescar matriz de resultados
    loadComparativeMatrix();
    loadTechniqueSummaries();
    loadDeterminismAudit();
  } catch (err) {
    showToast(`Fallo en ejecución: ${err.message}`, "error");
  } finally {
    btnRun.disabled = false;
    btnText.textContent = "Ejecutar Experimento";
  }
}

function renderExecutionResult(data) {
  // Paneles de visualización
  document.getElementById("viewer-prompt-text").textContent = data.prompt_enviado || "";
  document.getElementById("prompt-char-count").textContent = `${(data.prompt_enviado || "").length} caracteres`;

  document.getElementById("viewer-llm-response").textContent = data.respuesta_completa || "";
  document.getElementById("llm-latency-badge").textContent = `Latencia: ${data.duracion_generacion_ms || 0} ms`;

  document.getElementById("viewer-clean-code").textContent = data.codigo_generado || "";
  document.getElementById("sha-hash-badge").textContent = `SHA-256: ${(data.hash_codigo_sha256 || "").slice(0, 16)}...`;
  document.getElementById("sha-hash-badge").title = `Hash SHA-256 completo:\n${data.hash_codigo_sha256}`;

  // Banner de métricas consolidadas
  const banner = document.getElementById("execution-metrics-banner");
  banner.style.display = "grid";

  const pct = data.porcentaje_pruebas_aprobadas;
  document.getElementById("metric-cur-passed").textContent = pct !== null ? `${pct}%` : "N/D";
  document.getElementById("metric-cur-passed-detail").textContent = `${data.pruebas_aprobadas} / ${data.pruebas_totales} Pruebas Pytest`;

  document.getElementById("metric-cur-mi").textContent = data.maintainability_index !== null ? data.maintainability_index : "N/D";
  document.getElementById("metric-cur-cc").textContent = data.complejidad_ciclomatica_max !== null ? data.complejidad_ciclomatica_max : "N/D";
  document.getElementById("metric-cur-time").textContent = data.tiempo_mediano_ms !== null ? `${data.tiempo_mediano_ms} ms` : "N/D";
  document.getElementById("metric-cur-memory").textContent = data.memoria_mediana_kb !== null ? `${data.memoria_mediana_kb} KB` : "N/D";

  // Tablas detalladas
  const detailsBox = document.getElementById("execution-detailed-results");
  detailsBox.style.display = "block";

  // Aserciones Pytest
  document.getElementById("count-pytest-tab").textContent = (data.pruebas_detalle || []).length;
  const tbodyPytest = document.getElementById("tbody-pytest-details");
  tbodyPytest.innerHTML = "";
  (data.pruebas_detalle || []).forEach(p => {
    const tr = document.createElement("tr");
    const stClass = p.estado === "aprobada" ? "badge-aprobada" : (p.estado === "fallida" ? "badge-fallida" : "badge-error");
    tr.innerHTML = `
      <td><code>${escapeHtml(p.identificador_prueba)}</code></td>
      <td><span class="${stClass}">● ${escapeHtml(p.estado.toUpperCase())}</span></td>
      <td>${p.duracion_ms !== null ? `${p.duracion_ms} ms` : "N/D"}</td>
      <td style="color: var(--text-muted); font-size: 0.75rem;">${escapeHtml(p.mensaje_error || "Sin errores")}</td>
    `;
    tbodyPytest.appendChild(tr);
  });

  // Desglose Radon
  document.getElementById("count-radon-tab").textContent = (data.complejidad_detalle || []).length;
  const tbodyRadon = document.getElementById("tbody-radon-details");
  tbodyRadon.innerHTML = "";
  (data.complejidad_detalle || []).forEach(f => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${escapeHtml(f.nombre_funcion)}</code></td>
      <td>${escapeHtml(f.nombre_clase || "Módulo global")}</td>
      <td>Líneas ${f.linea_inicio || 1} - ${f.linea_fin || 1}</td>
      <td><strong>${f.complejidad_ciclomatica}</strong></td>
    `;
    tbodyRadon.appendChild(tr);
  });

  // Desglose Benchmark
  const tbodyBench = document.getElementById("tbody-benchmark-details");
  tbodyBench.innerHTML = "";
  (data.benchmark_detalle || []).forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>#${c.numero_corrida}</td>
      <td><span class="badge-pill ${c.tipo_corrida === 'calentamiento' ? 'badge-media' : 'badge-facil'}">${escapeHtml(c.tipo_corrida)}</span></td>
      <td><code>${escapeHtml(c.conjunto_entrada || 'caso_base')}</code></td>
      <td>${c.tiempo_ejecucion_ms !== null ? `${c.tiempo_ejecucion_ms} ms` : "N/D"}</td>
      <td>${c.memoria_pico_bytes !== null ? `${c.memoria_pico_bytes.toLocaleString()} bytes` : "--"}</td>
      <td>${c.timeout ? "TIMEOUT" : "OK (0)"}</td>
    `;
    tbodyBench.appendChild(tr);
  });
}

function switchDetailTab(tabName) {
  document.querySelectorAll(".sub-tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".detail-tab-content").forEach(c => c.classList.remove("active"));
  
  event.target.classList.add("active");
  const target = document.getElementById(`detail-tab-${tabName}`);
  if (target) target.classList.add("active");
}

// ==============================================================================
// INTERFAZ 3: MATRIZ COMPARATIVA Y RESULTADOS
// ==============================================================================
async function loadComparativeMatrix() {
  const probId = document.getElementById("filter-matrix-problema")?.value || "";
  const tec = document.getElementById("filter-matrix-tecnica")?.value || "";
  const dif = document.getElementById("filter-matrix-dificultad")?.value || "";

  const params = new URLSearchParams();
  if (probId) params.append("problema_id", probId);
  if (tec) params.append("tecnica_codigo", tec);
  if (dif) params.append("dificultad", dif);

  try {
    const res = await fetch(`/api/metricas/matriz?${params.toString()}`);
    if (!res.ok) throw new Error("Error al consultar matriz comparativa");
    state.matrixData = await res.json();
    renderComparativeMatrix(state.matrixData);
  } catch (err) {
    showToast(`Error al cargar matriz: ${err.message}`, "error");
  }
}

function renderComparativeMatrix(rows) {
  const tbody = document.getElementById("tbody-comparative-matrix");
  tbody.innerHTML = "";

  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="14" style="text-align: center; color: var(--text-muted); padding: 2rem;">No hay registros experimentales que coincidan con los filtros</td></tr>`;
    return;
  }

  rows.forEach(r => {
    const tr = document.createElement("tr");
    const diffBadge = r.dificultad === "Fácil" ? "badge-facil" : (r.dificultad === "Media" ? "badge-media" : "badge-dificil");
    
    let techBadge = "badge-tech-zero";
    if (r.tecnica_codigo === "FEW_SHOT") techBadge = "badge-tech-few";
    if (r.tecnica_codigo === "CHAIN_OF_THOUGHT") techBadge = "badge-tech-cot";
    if (r.tecnica_codigo === "ROLE_PROMPTING") techBadge = "badge-tech-role";

    const passPct = r.porcentaje_pruebas_aprobadas !== null ? `${r.porcentaje_pruebas_aprobadas}%` : `<span style="color:var(--accent-rose)">N/D</span>`;
    const miVal = r.maintainability_index !== null ? r.maintainability_index : "N/D";
    const ccVal = r.complejidad_ciclomatica_max !== null ? r.complejidad_ciclomatica_max : "N/D";
    const tAvg = r.tiempo_promedio_ms !== null ? `${r.tiempo_promedio_ms}` : "N/D";
    const tMed = r.tiempo_mediano_ms !== null ? `${r.tiempo_mediano_ms}` : "N/D";
    const memKb = r.memoria_mediana_kb !== null ? `${r.memoria_mediana_kb}` : "N/D";
    const hashShort = (r.hash_codigo_sha256 || "").slice(0, 10);

    tr.innerHTML = `
      <td><strong>#${r.ejecucion_id}</strong></td>
      <td><code>${escapeHtml(r.problema_codigo)}</code> - ${escapeHtml(r.problema_titulo)}</td>
      <td><span class="badge-pill ${diffBadge}">${escapeHtml(r.dificultad)}</span></td>
      <td><span class="badge-pill ${techBadge}">${escapeHtml(r.tecnica_nombre)}</span></td>
      <td>${r.numero_repeticion}</td>
      <td><strong>${passPct}</strong></td>
      <td>${miVal}</td>
      <td>${ccVal}</td>
      <td>${r.sloc || "N/D"}</td>
      <td>${tAvg}</td>
      <td><strong>${tMed}</strong></td>
      <td>${memKb}</td>
      <td><code title="${r.hash_codigo_sha256}">${hashShort}...</code></td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="inspectExecution(${r.ejecucion_id})">Ver</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadTechniqueSummaries() {
  try {
    const res = await fetch("/api/metricas/resumen-tecnicas");
    if (!res.ok) return;
    const summaries = await res.json();
    const container = document.getElementById("summary-technique-cards");
    container.innerHTML = "";

    const cardClasses = {
      "ZERO_SHOT": "card-zero",
      "FEW_SHOT": "card-few",
      "CHAIN_OF_THOUGHT": "card-cot",
      "ROLE_PROMPTING": "card-role"
    };

    summaries.forEach(s => {
      const cls = cardClasses[s.tecnica_codigo] || "card-zero";
      const div = document.createElement("div");
      div.className = `tech-summary-card ${cls}`;
      div.innerHTML = `
        <div class="summary-card-title">${escapeHtml(s.tecnica_nombre)} (${s.total_ejecuciones} Corridas)</div>
        <div class="summary-metrics-list">
          <div class="summary-row">
            <span class="summary-row-label">% Pruebas Aprobadas:</span>
            <span class="summary-row-val">${s.promedio_pruebas_aprobadas !== null ? s.promedio_pruebas_aprobadas + '%' : 'N/D'}</span>
          </div>
          <div class="summary-row">
            <span class="summary-row-label">Maintainability Index:</span>
            <span class="summary-row-val">${s.promedio_maintainability_index !== null ? s.promedio_maintainability_index : 'N/D'}</span>
          </div>
          <div class="summary-row">
            <span class="summary-row-label">Complejidad Ciclomática:</span>
            <span class="summary-row-val">${s.promedio_complejidad_ciclomatica !== null ? s.promedio_complejidad_ciclomatica : 'N/D'}</span>
          </div>
          <div class="summary-row">
            <span class="summary-row-label">Tiempo Mediano:</span>
            <span class="summary-row-val">${s.promedio_tiempo_mediano_ms !== null ? s.promedio_tiempo_mediano_ms + ' ms' : 'N/D'}</span>
          </div>
          <div class="summary-row">
            <span class="summary-row-label">Memoria Mediana:</span>
            <span class="summary-row-val">${s.promedio_memoria_kb !== null ? s.promedio_memoria_kb + ' KB' : 'N/D'}</span>
          </div>
        </div>
      `;
      container.appendChild(div);
    });
  } catch (err) {
    console.error("Error al cargar resúmenes por técnica:", err);
  }
}

async function loadDeterminismAudit() {
  try {
    const res = await fetch("/api/metricas/determinismo");
    if (!res.ok) return;
    const audit = await res.json();
    const textEl = document.getElementById("determinism-summary-text");

    if (audit.length === 0) {
      textEl.innerHTML = "Sin corridas registradas aún. Ejecute experimentos con varias repeticiones para verificar la invariancia de hashes SHA-256.";
      return;
    }

    const verified = audit.filter(a => a.estado_determinismo.includes("Verificado")).length;
    textEl.innerHTML = `Auditando <strong>${audit.length}</strong> combinaciones (Problema &bull; Técnica). 
      Se ha verificado determinismo reproducible en <strong>${verified}</strong> grupos con réplicas múltiples (Hashes SHA-256 idénticos bajo T=0.0).`;
  } catch (err) {
    console.error("Error al auditar determinismo:", err);
  }
}

function exportData(format) {
  const probId = document.getElementById("filter-matrix-problema")?.value || "";
  const tec = document.getElementById("filter-matrix-tecnica")?.value || "";
  const dif = document.getElementById("filter-matrix-dificultad")?.value || "";

  const params = new URLSearchParams();
  if (probId) params.append("problema_id", probId);
  if (tec) params.append("tecnica_codigo", tec);
  if (dif) params.append("dificultad", dif);

  const url = `/api/export/${format}?${params.toString()}`;
  window.open(url, "_blank");
  showToast(`Descarga de dataset ${format.toUpperCase()} iniciada`, "success");
}

async function inspectExecution(id) {
  try {
    const res = await fetch(`/api/ejecuciones/${id}`);
    if (!res.ok) throw new Error("Error al obtener detalle de la ejecución");
    const data = await res.json();

    document.getElementById("modal-title").textContent = `Detalle de Corrida #${data.ejecucion_id} - [${data.problema_codigo}] ${data.tecnica_nombre}`;
    
    const body = document.getElementById("modal-content");
    body.innerHTML = `
      <div style="margin-bottom: 1rem; display: flex; gap: 1rem; flex-wrap: wrap;">
        <span class="badge-pill badge-facil">Repetición #${data.numero_repeticion}</span>
        <span class="badge-pill badge-media">Latencia: ${data.duracion_generacion_ms || 0} ms</span>
        <span class="badge-pill badge-tech-zero">Hash SHA-256: ${data.hash_codigo_sha256}</span>
      </div>
      <div style="margin-bottom: 1rem;">
        <h4 style="margin-bottom: 0.5rem; font-size: 0.9rem;">Código Python Extraído y Evaluado:</h4>
        <pre class="code-font" style="background:#060913; padding: 1rem; border-radius: 8px; overflow-x:auto; color:#38bdf8;">${escapeHtml(data.codigo_generado || 'Sin código')}</pre>
      </div>
      <div>
        <h4 style="margin-bottom: 0.5rem; font-size: 0.9rem;">Respuesta Completa del LLM:</h4>
        <pre class="code-font" style="background:#060913; padding: 1rem; border-radius: 8px; overflow-x:auto; max-height: 250px; color:#cbd5e1;">${escapeHtml(data.respuesta_completa || '')}</pre>
      </div>
    `;

    document.getElementById("detail-modal").classList.add("active");
  } catch (err) {
    showToast(`Error al cargar inspección: ${err.message}`, "error");
  }
}

function closeModal(event) {
  if (event && event.target.closest(".modal-container")) return;
  document.getElementById("detail-modal").classList.remove("active");
}

// ==============================================================================
// UTILIDADES Y NOTIFICACIONES
// ==============================================================================
function copyViewerContent(elementId) {
  const text = document.getElementById(elementId)?.textContent || "";
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    showToast("Contenido copiado al portapapeles", "success");
  }).catch(() => {
    showToast("No se pudo copiar automáticamente", "error");
  });
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  const icon = type === "success" ? "✅" : (type === "error" ? "❌" : "ℹ️");
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
