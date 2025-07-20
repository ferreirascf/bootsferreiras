document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');

  const modalBloquear = document.getElementById('modalBloquear');
  const fecharBloquear = document.getElementById('fechar-bloquear');
  const inputHoraBloqueio = document.getElementById('inputHoraBloqueio');
  const btnBloquear = document.getElementById('btnBloquear');

  const modalCancelar = document.getElementById('modalCancelar');
  const fecharCancelar = document.getElementById('fechar-cancelar');
  const btnCancelarAgendamento = document.getElementById('btnCancelarAgendamento');
  const btnFecharCancelar = document.getElementById('btnFechar');
  const infoAgendamento = document.getElementById('infoAgendamento');

  let dataSelecionadaParaBloquear = null;
  let agendamentoSelecionado = null;

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'pt-br',
    selectable: true,
    editable: false,
    events: '/agendamentos',

    dateClick: function(info) {
      dataSelecionadaParaBloquear = info.dateStr;
      inputHoraBloqueio.value = '';
      modalBloquear.style.display = 'block';
    },

    eventClick: function(info) {
  if(info.event.backgroundColor === 'green') {
    agendamentoSelecionado = info.event;
    const title = agendamentoSelecionado.title;
    const email = agendamentoSelecionado.extendedProps.email || 'Sem email';
    const telefone = agendamentoSelecionado.extendedProps.telefone || 'Sem telefone';
    const servico = agendamentoSelecionado.extendedProps.servico || 'Serviço não informado';
    
    infoAgendamento.innerHTML = `
      Nome: ${title}<br>
      Email: ${email}<br>
      Telefone: ${telefone}<br>
      Horário: ${agendamentoSelecionado.startStr.substring(0,16).replace('T', ' ')}<br>
      Serviço: ${servico}
    `;
    modalCancelar.style.display = 'block';
  }
    }
  });

  calendar.render();

  fecharBloquear.onclick = () => {
    modalBloquear.style.display = 'none';
  };
  fecharCancelar.onclick = () => {
    modalCancelar.style.display = 'none';
  };
  btnFecharCancelar.onclick = () => {
    modalCancelar.style.display = 'none';
  };

  btnBloquear.onclick = () => {
    const hora = inputHoraBloqueio.value.trim();

    if(!hora || !/^\d{2}:\d{2}$/.test(hora)) {
      alert('Digite um horário válido no formato HH:MM');
      return;
    }

    const horarioCompleto = `${dataSelecionadaParaBloquear} ${hora}`;

    fetch('/bloquear', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ horario: horarioCompleto })
    })
    .then(res => res.json())
    .then(data => {
      alert(data.mensagem);
      modalBloquear.style.display = 'none';
      calendar.refetchEvents();
    })
    .catch(() => alert("Erro ao bloquear horário."));
  };

  btnCancelarAgendamento.onclick = () => {
    if(!agendamentoSelecionado) return;
    fetch(`/cancelar/${agendamentoSelecionado.id}`, {
      method: 'DELETE',
    })
    .then(res => res.json())
    .then(data => {
      alert(data.mensagem);
      modalCancelar.style.display = 'none';
      agendamentoSelecionado = null;
      calendar.refetchEvents();
    })
    .catch(() => alert("Erro ao cancelar agendamento."));
  };

  window.onclick = function(event) {
    if(event.target == modalBloquear) modalBloquear.style.display = 'none';
    if(event.target == modalCancelar) modalCancelar.style.display = 'none';
  };
});