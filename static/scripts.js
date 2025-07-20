document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const modal = document.getElementById('modal');
    const fecharModal = document.getElementById('fechar-modal');
    const dataSelecionadaSpan = document.getElementById('data-selecionada');
    const horariosDiv = document.getElementById('horarios');
    const btnAgendar = document.getElementById('btnAgendar');

    const clienteInput = document.getElementById('cliente');
    const emailInput = document.getElementById('email');
    const telefoneInput = document.getElementById('telefone');
    const servicoInput = document.getElementById('servico');

    const horariosPadrao = ["14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"];
    let horarioSelecionado = null;
    let dataSelecionada = null;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        selectable: true,
        hiddenDays: [0, 6],
        dateClick: function(info) {
            dataSelecionada = info.dateStr;
            console.log('Data selecionada:', dataSelecionada);
            dataSelecionadaSpan.textContent = dataSelecionada;
            abrirModal();
            carregarHorarios(dataSelecionada);
        }
    });

    calendar.render();

    function abrirModal() {
        horarioSelecionado = null;
        btnAgendar.disabled = true;
        modal.style.display = 'block';
        horariosDiv.innerHTML = '';
    }

    function fecharModalFunc() {
        modal.style.display = 'none';
        clienteInput.value = '';
        emailInput.value = '';
        telefoneInput.value = '';
        horariosDiv.innerHTML = '';
        horarioSelecionado = null;
        servicoInput.value = '';
        btnAgendar.disabled = true;
    }

    fecharModal.onclick = () => {
        fecharModalFunc();
    };

    window.onclick = (event) => {
        if(event.target == modal) {
            fecharModalFunc();
        }
    };

    function carregarHorarios(data) {
        fetch(`/horarios/${data}`)
            .then(res => res.json())
            .then(horariosOcupados => {
                horariosDiv.innerHTML = '';
                horariosPadrao.forEach(horario => {
                    if (!horariosOcupados.includes(horario)) {
                        const btn = document.createElement('button');
                        btn.textContent = horario;
                        btn.className = 'horario-btn';
                        btn.onclick = () => {
                            document.querySelectorAll('.horario-btn').forEach(b => b.classList.remove('selected'));
                            btn.classList.add('selected');
                            horarioSelecionado = horario;
                            console.log('Horário selecionado:', horarioSelecionado);
                            btnAgendar.disabled = false;
                        };
                        horariosDiv.appendChild(btn);
                    }
                });

                if (horariosDiv.innerHTML === '') {
                    horariosDiv.innerHTML = '<p>Não há horários disponíveis para essa data.</p>';
                }
            })
            .catch(() => {
                horariosDiv.innerHTML = '<p>Erro ao carregar horários.</p>';
            });
    }

    btnAgendar.onclick = () => {
        const cliente = clienteInput.value.trim();
        const email = emailInput.value.trim();
        const telefone = telefoneInput.value.trim();
        const servico = servicoInput.value.trim();

        if (!cliente || !email || !telefone || !dataSelecionada || !horarioSelecionado) {
            alert("Preencha nome, email, telefone, selecione data e horário.");
            return;
        }

        btnAgendar.disabled = true;

        fetch('/agendar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                nome: cliente,
                email: email,
                telefone: telefone,
                servico_id: servico,
                horario: `${dataSelecionada} ${horarioSelecionado}`
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.mensagem === "Agendado com sucesso!") {
                mostrarModalParabens();
                fecharModalFunc();
                calendar.refetchEvents();
            } else {
                alert(data.mensagem);
                btnAgendar.disabled = false;
            }
        })
        .catch(() => {
            alert("Erro ao agendar. Tente novamente.");
            btnAgendar.disabled = false;
        });
    };

    function mostrarModalParabens() {
        const modalParabens = document.createElement('div');
        modalParabens.id = 'modalParabens';
        modalParabens.style.position = 'fixed';
        modalParabens.style.top = '0';
        modalParabens.style.left = '0';
        modalParabens.style.width = '100%';
        modalParabens.style.height = '100%';
        modalParabens.style.backgroundColor = 'rgba(0,0,0,0.7)';
        modalParabens.style.display = 'flex';
        modalParabens.style.justifyContent = 'center';
        modalParabens.style.alignItems = 'center';
        modalParabens.style.zIndex = '1000';

        const conteudo = document.createElement('div');
        conteudo.style.backgroundColor = 'white';
        conteudo.style.padding = '30px';
        conteudo.style.borderRadius = '12px';
        conteudo.style.textAlign = 'center';
        conteudo.style.maxWidth = '320px';
        conteudo.style.boxShadow = '0 0 15px rgba(0,0,0,0.3)';
        conteudo.innerHTML = `
            <h2>Parabéns!</h2>
            <p>Seu agendamento foi concluído com sucesso.</p>
            <button id="btnFecharParabens" style="
                margin-top: 20px;
                padding: 10px 20px;
                font-size: 16px;
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            ">Fechar</button>
        `;

        modalParabens.appendChild(conteudo);
        document.body.appendChild(modalParabens);

        document.getElementById('btnFecharParabens').onclick = () => {
            document.body.removeChild(modalParabens);
        };
    }
});