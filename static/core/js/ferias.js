// Purpose of this file:
// This script is connect with: 
//    
    
    let employees = [
      {
        id:1, name:'Bernardo Vieira', periods:[{id:11, start:'2025-11-01',end:'2026-01-01', daysRight:30, taken:4}], uses:[{id:101,start:'2025-11-07',end:'2025-11-11',days:4,type:'Recesso',notes:'2 faltas descontadas'}]
      },
      {id:2, name:'Joana Silva', periods:[], uses:[]},
      {id:3, name:'Carlos Souza', periods:[{id:31,start:'2024-08-01',end:'2025-08-01', daysRight:30, taken:10}], uses:[{id:301,start:'2025-01-20',end:'2025-01-30',days:10,type:'Férias',notes:'Pagamento parcial'}]}
    ];

    const employeesGrid = document.getElementById('employeesGrid');
    const searchInput = document.getElementById('searchInput');
    const modalBack = document.getElementById('modalBack');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    const modalSave = document.getElementById('modalSave');
    const modalCancel = document.getElementById('modalCancel');

    // utilities
    function uid(){return Math.floor(Math.random()*1000000)}

    function formatDate(d){ if(!d) return '-'; return new Date(d+'T00:00:00').toLocaleDateString('pt-BR') }

    // render
    function renderGrid(filter=''){
      employeesGrid.innerHTML='';
      const list = employees.filter(e=> e.name.toLowerCase().includes(filter.toLowerCase()));
      if(list.length===0){ employeesGrid.innerHTML = '<div class="empty">Nenhum funcionário encontrado.</div>'; return }

      list.forEach(emp => {
        const card = document.createElement('div'); card.className='employee';
        card.innerHTML = `
          <div class="employee-head">
            <div class="avatar">${emp.name.split(' ').map(s=>s[0]).slice(0,2).join('')}</div>
            <div class="emp-info">
              <div class="emp-name">${emp.name}</div>
              <div class="small">Períodos: ${emp.periods.length} • Férias registradas: ${emp.uses.length}</div>
            </div>
            <div style="text-align:right">
              <div class="small">Saldo total</div>
              <div style="font-weight:700">${calculateTotalSaldo(emp)} dias</div>
            </div>
          </div>

          <div class="tabs" style="margin-top:12px">
            <div class="tab active" data-tab="periods">Períodos Aquisitivos</div>
            <div class="tab" data-tab="uses">Férias Gozadas</div>
            <div style="flex:1"></div>
            <button class="btn btn-primary" data-action="add-period">+ Novo Período</button>
            <button class="btn btn-primary" style="margin-left:6px" data-action="add-use">+ Novo Uso</button>
          </div>

          <div class="content">
            <div class="col panel" data-panel="periods">
              ${emp.periods.length===0? '<div class="empty">Nenhum período aquisitivo registrado.</div>' : `
                <table>
                  <thead><tr><th>Período</th><th>Dias direito</th><th>Tirados</th><th>Saldo</th><th>Ações</th></tr></thead>
                  <tbody>
                    ${emp.periods.map(p=>`<tr>
                      <td>${formatDate(p.start)} → ${formatDate(p.end)}</td>
                      <td>${p.daysRight}</td>
                      <td>${p.taken||0}</td>
                      <td>${(p.daysRight - (p.taken||0))}</td>
                      <td><div class="actions-row"><button class="btn btn-ghost" data-action="edit-period" data-emp="${emp.id}" data-id="${p.id}">Editar</button><button class="btn btn-ghost" data-action="delete-period" data-emp="${emp.id}" data-id="${p.id}">Excluir</button></div></td>
                    </tr>`).join('')}
                  </tbody>
                </table>`}
            </div>
            <div class="col panel" data-panel="uses" style="display:none">
              ${emp.uses.length===0? '<div class="empty">Sem períodos de férias cadastrados.</div>' : `
                <table>
                  <thead><tr><th>Período</th><th>Dias</th><th>Tipo</th><th>Observações</th><th>Ações</th></tr></thead>
                  <tbody>
                    ${emp.uses.map(u=>`<tr>
                      <td>${formatDate(u.start)} → ${formatDate(u.end)}</td>
                      <td>${u.days}</td>
                      <td>${u.type||'-'}</td>
                      <td>${u.notes||'-'}</td>
                      <td><div class="actions-row"><button class="btn btn-ghost" data-action="edit-use" data-emp="${emp.id}" data-id="${u.id}">Editar</button><button class="btn btn-ghost" data-action="delete-use" data-emp="${emp.id}" data-id="${u.id}">Excluir</button></div></td>
                    </tr>`).join('')}
                  </tbody>
                </table>`}
            </div>
          </div>
        `;

        // events for this card
        card.querySelectorAll('.tab').forEach(t=> t.addEventListener('click', (ev)=>{
          card.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
          t.classList.add('active');
          const tab = t.getAttribute('data-tab');
          card.querySelectorAll('[data-panel]').forEach(p=> p.style.display = p.getAttribute('data-panel')===tab? 'block' : 'none');
        }));

        card.querySelectorAll('[data-action]').forEach(btn=> btn.addEventListener('click', (ev)=>{
          const action = btn.getAttribute('data-action');
          const empId = btn.getAttribute('data-emp') || emp.id;
          const itemId = btn.getAttribute('data-id');
          handleAction(action, empId, itemId);
        }));

        employeesGrid.appendChild(card);
      });
    }

    function calculateTotalSaldo(emp){
      let saldo = 0;
      emp.periods.forEach(p => { saldo += (p.daysRight - (p.taken||0)) });
      return saldo;
    }

    // actions
    function handleAction(action, empId, itemId){
      const emp = employees.find(e=> e.id==empId);
      if(!emp) return;
      if(action==='add-period' || action==='add-period-global'){
        openPeriodForm(emp);
      } else if(action==='add-use' || action==='add-use-global'){
        openUseForm(emp);
      } else if(action==='edit-period'){
        const p = emp.periods.find(x=> x.id==itemId); openPeriodForm(emp,p);
      } else if(action==='delete-period'){
        if(confirm('Excluir período aquisitivo?')){ emp.periods = emp.periods.filter(x=> x.id!=itemId); renderGrid(searchInput.value) }
      } else if(action==='edit-use'){
        const u = emp.uses.find(x=> x.id==itemId); openUseForm(emp,u);
      } else if(action==='delete-use'){
        if(confirm('Excluir registro de férias?')){ emp.uses = emp.uses.filter(x=> x.id!=itemId); renderGrid(searchInput.value) }
      }
    }

    // modal helpers
    function openModal(title, bodyHtml, onSave){
      modalTitle.textContent = title; modalBody.innerHTML = bodyHtml; modalBack.style.display = 'flex';
      function saveHandler(){ onSave(); closeModal(); }
      modalSave.onclick = saveHandler; modalCancel.onclick = closeModal;
    }
    function closeModal(){ modalBack.style.display='none'; modalBody.innerHTML=''; modalSave.onclick=null }

    // forms
    function openPeriodForm(emp, period){
      const p = period || {start:'',end:'',daysRight:30,taken:0};
      const html = `
        <div>
          <div class="form-row"><div style="flex:1"><label>Início</label><input id="f_start" type="date" value="${p.start||''}"></div><div style="width:12px"></div><div style="flex:1"><label>Fim</label><input id="f_end" type="date" value="${p.end||''}"></div></div>
          <div class="form-row"><div style="flex:1"><label>Dias de direito</label><input id="f_days" type="number" min="0" value="${p.daysRight||30}"></div><div style="flex:1"><label>Tirados (bruto)</label><input id="f_taken" type="number" min="0" value="${p.taken||0}"></div></div>
          <div><label>Observação (opcional)</label><textarea id="f_notes"></textarea></div>
          <div class="help">Ao salvar, o período será exibido na lista do funcionário. Use "Registrar Uso" para marcar dias efetivamente gozados.</div>
        </div>`;

      openModal(`Período Aquisitivo - ${emp.name}`, html, ()=>{
        const start = document.getElementById('f_start').value;
        const end = document.getElementById('f_end').value;
        const daysRight = Number(document.getElementById('f_days').value||0);
        const taken = Number(document.getElementById('f_taken').value||0);
        if(!start || !end){ alert('Preencha datas de início e fim.'); return }
        if(period){ // edit
          period.start=start; period.end=end; period.daysRight=daysRight; period.taken=taken;
        } else {
          emp.periods.push({id:uid(), start, end, daysRight, taken});
        }
        renderGrid(searchInput.value);
      });
    }

    function openUseForm(emp, use){
      const u = use || {start:'',end:'',days:1,type:'Férias',notes:''};
      // simple suggestion: choose which period this use will consume
      const options = emp.periods.map(p=> `<option value="${p.id}">${formatDate(p.start)} → ${formatDate(p.end)} (saldo: ${p.daysRight - (p.taken||0)})</option>`).join('') || '<option value="">(nenhum período disponível)</option>';
      const html = `
        <div>
          <div class="form-row"><div style="flex:1"><label>Período aquisitivo</label><select id="u_period">${options}</select></div></div>
          <div class="form-row"><div style="flex:1"><label>Início</label><input id="u_start" type="date" value="${u.start||''}"></div><div style="flex:1"><label>Fim</label><input id="u_end" type="date" value="${u.end||''}"></div></div>
          <div class="form-row"><div style="flex:1"><label>Dias</label><input id="u_days" type="number" min="1" value="${u.days||1}"></div><div style="flex:1"><label>Tipo</label><select id="u_type"><option ${u.type==='Férias'?'selected':''}>Férias</option><option ${u.type==='Recesso'?'selected':''}>Recesso</option><option ${u.type==='Licença'?'selected':''}>Licença</option></select></div></div>
          <div><label>Observações</label><textarea id="u_notes">${u.notes||''}</textarea></div>
          <div class="help">Selecione o período aquisitivo que será consumido. O sistema atualiza o saldo (sobrescreve dados demo).</div>
        </div>`;

      openModal(`Registrar Uso - ${emp.name}`, html, ()=>{
        const start = document.getElementById('u_start').value;
        const end = document.getElementById('u_end').value;
        const days = Number(document.getElementById('u_days').value||0);
        const type = document.getElementById('u_type').value;
        const notes = document.getElementById('u_notes').value;
        const periodId = document.getElementById('u_period').value;
        if(!start || !end){ alert('Preencha datas de início e fim.'); return }
        if(days<=0){ alert('Insira dias válidos.'); return }
        // update period taken
        if(periodId){ const p = emp.periods.find(x=> x.id==periodId); if(p){ p.taken = (p.taken||0) + days } }
        if(use){ use.start=start; use.end=end; use.days=days; use.type=type; use.notes=notes; }
        else emp.uses.push({id:uid(),start,end,days,type,notes});
        renderGrid(searchInput.value);
      });
    }

    // global buttons (top)
    document.getElementById('addGlobalPeriod').addEventListener('click', ()=>{
      // if search is filtering to single employee, open for that one; else open modal to pick employee
      const q = searchInput.value.trim(); const matches = employees.filter(e=> e.name.toLowerCase().includes(q.toLowerCase()));
      if(matches.length===1) openPeriodForm(matches[0]);
      else pickEmployeeFor('period');
    });
    document.getElementById('addGlobalUse').addEventListener('click', ()=>{
      const q = searchInput.value.trim(); const matches = employees.filter(e=> e.name.toLowerCase().includes(q.toLowerCase()));
      if(matches.length===1) openUseForm(matches[0]);
      else pickEmployeeFor('use');
    });

    function pickEmployeeFor(type){
      const html = `<div><label>Selecione o funcionário</label><select id="pickEmp">${employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join('')}</select></div>`;
      openModal(type==='period'? 'Registrar Período - Escolher funcionário' : 'Registrar Uso - Escolher funcionário', html, ()=>{
        const id = document.getElementById('pickEmp').value; const emp = employees.find(e=> e.id==id);
        if(type==='period') openPeriodForm(emp); else openUseForm(emp);
      });
    }

    // search
    searchInput.addEventListener('input', ()=> renderGrid(searchInput.value));

    // reset demo
    document.getElementById('resetDemo').addEventListener('click', ()=>{ if(confirm('Resetar dados demo?')){ employees = [
      {id:1, name:'Bernardo Vieira', periods:[{id:11, start:'2025-11-01',end:'2026-01-01', daysRight:30, taken:4}], uses:[{id:101,start:'2025-11-07',end:'2025-11-11',days:4,type:'Recesso',notes:'2 faltas descontadas'}]},
      {id:2, name:'Joana Silva', periods:[], uses:[]},
      {id:3, name:'Carlos Souza', periods:[{id:31,start:'2024-08-01',end:'2025-08-01', daysRight:30, taken:10}], uses:[{id:301,start:'2025-01-20',end:'2025-01-30',days:10,type:'Férias',notes:'Pagamento parcial'}]}
    ]; renderGrid(''); } });

    // init
    renderGrid('');
