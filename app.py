from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from flask_cors import CORS

load_dotenv()  # Se estiver usando .env, para carregar variáveis de ambiente

app = Flask(__name__)
CORS(app)
app.secret_key = 'uma_chave_secreta_aleatoria_aqui'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

USUARIOS = {
    'allegrasel@gmail.com': 'ALLEGRASEL.01'  
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def enviar_email_confirmacao(nome, email_destino, servico_nome, horario):
    remetente = os.getenv("EMAIL_REMETENTE")
    senha = os.getenv("SENHA_EMAIL")
    destinatario = email_destino
    assunto = "Confirmação de Agendamento - bootsferreiras"
    corpo = f"""
Olá {nome},

Seu agendamento foi confirmado com sucesso!
Aqui estão os detalhes do seu agendamento:

Serviço: {servico_nome}
Data e Horário: {horario.strftime('%d/%m/%Y %H:%M')}

Se você tiver alguma dúvida ou precisar alterar seu agendamento, por favor, entre em contato com a profissional (51) 995676306.

Agradecemos pela preferência! 💅
Caso precise de mais informações, não hesite em nos contatar.

Atenciosamente,
Equipe bootsferreiras
"""

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(msg)
            print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def enviar_email_cancelamento(nome, email_destino, servico_nome, horario):
    remetente = os.getenv("EMAIL_REMETENTE")
    senha = os.getenv("SENHA_EMAIL")
    destinatario = email_destino
    assunto = "Cancelamento de Agendamento - bootsferreiras"
    corpo = f"""
Olá {nome},

Esperamos que esteja bem.

Informamos que infelizmente o seu agendamento foi cancelado.

Sentimos muito pelo transtorno, mas devido a imprevistos, não poderemos atender no horário agendado.

Se desejar, você pode reagendar seu atendimento.

Serviço: {servico_nome}
Data e Horário: {horario.strftime('%d/%m/%Y %H:%M')}

Caso tenha dúvidas, entre em contato conosco.

Atenciosamente,
Equipe bootsferreiras
"""

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(msg)
            print("E-mail de cancelamento enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de cancelamento: {e}")

class Bloqueio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horario = db.Column(db.DateTime, nullable=False, unique=True)

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    duracao_minutos = db.Column(db.Integer, nullable=False)

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    horario = db.Column(db.DateTime, nullable=False, unique=True)
    inicio = db.Column(db.DateTime, nullable=False)
    fim = db.Column(db.DateTime, nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    servico = db.relationship('Servico')

class Cancelamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    horario = db.Column(db.DateTime, nullable=False)
    servico_id = db.Column(db.Integer, nullable=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        if email in USUARIOS and USUARIOS[email] == senha:
            session['usuario_logado'] = email
            return redirect(url_for('painel'))
        else:
            erro = 'Email ou senha incorretos.'
    return render_template('login.html', erro=erro)

@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    return redirect(url_for('login'))

@app.route('/')
def cliente():
    return render_template('cliente.html')

@app.route('/painel')
@login_required
def painel():
    return render_template('painel.html')

@app.route('/servicos')
def listar_servicos():
    servicos = Servico.query.all()
    return jsonify([{
        'id': s.id,
        'nome': s.nome,
        'preco': s.preco,
        'duracao_minutos': s.duracao_minutos
    } for s in servicos])

@app.route('/horarios/<data>', methods=['GET'])
def horarios_do_dia(data):
    try:
        data_limpa = data.strip().split('T')[0]
        data_dt = datetime.strptime(data_limpa, '%Y-%m-%d')
    except ValueError:
        return jsonify({"mensagem": "Formato de data inválido"}), 400

    proximo_dia = data_dt + timedelta(days=1)

    agendamentos = Agendamento.query.filter(
        Agendamento.horario >= data_dt,
        Agendamento.horario < proximo_dia
    ).all()

    bloqueios = Bloqueio.query.filter(
        Bloqueio.horario >= data_dt,
        Bloqueio.horario < proximo_dia
    ).all()

    horarios_ocupados = set()
    
    for a in agendamentos:
        atual = a.inicio
        while atual < a.fim:
            horarios_ocupados.add(atual.strftime('%H:%M'))
            atual += timedelta(minutes=30)

    for b in bloqueios:
        horarios_ocupados.add(b.horario.strftime('%H:%M'))

    return jsonify(sorted(list(horarios_ocupados)))

@app.route('/agendamentos_profissional')
@login_required
def agendamentos_profissional():
    agendamentos = Agendamento.query.order_by(Agendamento.horario).all()
    lista = []
    for ag in agendamentos:
        servico = Servico.query.get(ag.servico_id)
        nome_servico = servico.nome if servico else "Serviço desconhecido"
        texto = (
            f"ID: {ag.id}\n"
            f"Nome: {ag.nome}\n"
            f"Email: {ag.email}\n"
            f"Telefone: {ag.telefone}\n"
            f"Horário: {ag.horario.strftime('%Y-%m-%d %H:%M')}\n"
            f"Serviço: {nome_servico}"
        )
        lista.append(texto)
    return jsonify(lista)

@app.route('/cancelamentos_profissional')
@login_required
def cancelamentos_profissional():
    cancelamentos = Cancelamento.query.order_by(Cancelamento.horario).all()
    lista = []
    for c in cancelamentos:
        servico = Servico.query.get(c.servico_id)
        nome_servico = servico.nome if servico else "Serviço desconhecido"
        texto = (
            f"ID: {c.id}\n"
            f"Nome: {c.nome}\n"
            f"Email: {c.email}\n"
            f"Telefone: {c.telefone}\n"
            f"Horário: {c.horario.strftime('%Y-%m-%d %H:%M')}\n"
            f"Serviço: {nome_servico}"
        )
        lista.append(texto)
    return jsonify(lista)

@app.route('/cancelar/<int:id>', methods=['DELETE'])
@login_required
def cancelar(id):
    agendamento = Agendamento.query.get(id)
    if not agendamento:
        return jsonify({"mensagem": "Agendamento não encontrado."}), 404

    cancel = Cancelamento(
        nome=agendamento.nome,
        email=agendamento.email,
        telefone=agendamento.telefone,
        horario=agendamento.horario,
        servico_id=agendamento.servico_id
    )
    db.session.add(cancel)

    enviar_email_cancelamento(agendamento.nome, agendamento.email, agendamento.servico.nome, agendamento.horario)
    db.session.delete(agendamento)
    db.session.commit()
    return jsonify({"mensagem": "Agendamento cancelado com sucesso!"})

@app.route('/reagendar/<int:id_cancelamento>', methods=['POST'])
@login_required
def reagendar(id_cancelamento):
    cancel = Cancelamento.query.get(id_cancelamento)
    if not cancel:
        return jsonify({"mensagem": "Cancelamento não encontrado."}), 404

    servico = Servico.query.get(cancel.servico_id)
    if not servico:
        return jsonify({"mensagem": "Serviço do cancelamento não encontrado."}), 400

    fim = cancel.horario + timedelta(minutes=servico.duracao_minutos)

    conflito = Agendamento.query.filter(
        Agendamento.inicio < fim,
        Agendamento.fim > cancel.horario
    ).first()

    if conflito:
        return jsonify({"mensagem": "Horário já está ocupado."}), 400

    novo = Agendamento(
        nome=cancel.nome,
        email=cancel.email,
        telefone=cancel.telefone,
        horario=cancel.horario,
        inicio=cancel.horario,
        fim=fim,
        servico_id=cancel.servico_id
    )
    db.session.add(novo)
    db.session.delete(cancel)
    db.session.commit()

    enviar_email_confirmacao(novo.nome, novo.email, novo.servico.nome, novo.horario)
    return jsonify({"mensagem": "Agendamento reagendado com sucesso!"})

@app.route('/agendar', methods=['POST'])
def agendar():
    data = request.get_json()
    nome = data.get('nome')
    email = data.get('email')
    telefone = data.get('telefone')
    horario_str = data.get('horario')
    servico_id = int(data.get('servico_id'))
    servico = Servico.query.get(servico_id)

    if not servico:
        return jsonify({"mensagem": "Serviço não encontrado."}), 400

    try:
        horario_dt = datetime.strptime(horario_str, '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({"mensagem": "Data/horário inválido."}), 400

    if horario_dt < datetime.now():
        return jsonify({"mensagem": "Não é possível agendar para datas passadas."}), 400

    fim = horario_dt + timedelta(minutes=servico.duracao_minutos)

    if not nome or not email or not telefone or not horario_str:
        return jsonify({"mensagem": "Dados incompletos."}), 400

    conflitos = Agendamento.query.filter(
        Agendamento.inicio < fim,
        Agendamento.fim > horario_dt
    ).first()
    if conflitos:
        return jsonify({"mensagem": "Horário já está ocupado com outro agendamento."}), 400

    bloqueios = Bloqueio.query.filter(
        Bloqueio.horario >= horario_dt,
        Bloqueio.horario < fim
    ).first()
    if bloqueios:
        return jsonify({"mensagem": "Horário bloqueado."}), 400

    novo = Agendamento(
        nome=nome,
        email=email,
        telefone=telefone,
        horario=horario_dt,
        inicio=horario_dt,
        fim=fim,
        servico_id=servico_id
    )
    db.session.add(novo)
    db.session.commit()
    enviar_email_confirmacao(nome, email, servico.nome, horario_dt)
    return jsonify({"mensagem": "Agendado com sucesso!"})

@app.route('/bloquear', methods=['POST'])
@login_required
def bloquear():
    data = request.get_json()
    horario_str = data.get('horario')

    if not horario_str:
        return jsonify({"mensagem": "Dados incompletos."}), 400

    try:
        horario_dt = datetime.strptime(horario_str, '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({"mensagem": "Data/horário inválido."}), 400

    if Agendamento.query.filter_by(horario=horario_dt).first():
        return jsonify({"mensagem": "Não pode bloquear horário agendado."}), 400

    if Bloqueio.query.filter_by(horario=horario_dt).first():
        return jsonify({"mensagem": "Horário já está bloqueado."}), 400

    novo_bloqueio = Bloqueio(horario=horario_dt)
    db.session.add(novo_bloqueio)
    db.session.commit()
    return jsonify({"mensagem": "Horário bloqueado com sucesso!"})

@app.route('/agendamentos', methods=['GET'])
@login_required
def agendamentos():
    eventos = []

    ags = Agendamento.query.all()
    for ag in ags:
        eventos.append({
            "id": ag.id,
            "title": f"{ag.nome}",
            "start": ag.horario.strftime('%Y-%m-%dT%H:%M:%S'),
            "end": ag.fim.strftime('%Y-%m-%dT%H:%M:%S'),
            "color": "green",
            "extendedProps": {
                "email": ag.email,
                "telefone": ag.telefone,
                "servico": ag.servico.nome if ag.servico else "Serviço não informado"
            }
        })

    blqs = Bloqueio.query.all()
    for blq in blqs:
        eventos.append({
            "title": "Bloqueado",
            "start": blq.horario.strftime('%Y-%m-%dT%H:%M:%S'),
            "color": "red"
        })

    return jsonify(eventos)

@app.before_request
def criar_banco():
    db.create_all()

def popular_servicos():
    servicos = [
        {"nome": "Manicure", "preco": 30.0, "duracao_minutos": 60},
        {"nome": "Pedicure", "preco": 35.0, "duracao_minutos": 60},
        {"nome": "Unha em Gel", "preco": 50.0, "duracao_minutos": 90},
        {"nome": "Alongamento", "preco": 50.0, "duracao_minutos": 120},
        {"nome": "Blindagem", "preco": 80.0, "duracao_minutos": 120},
        {"nome": "Spa para pés", "preco": 100.0, "duracao_minutos": 120},
        {"nome": "Blindagem de construção", "preco": 120.0, "duracao_minutos": 120}
    ]

    for s in servicos:
        existe = Servico.query.filter_by(nome=s["nome"]).first()
        if not existe:
            novo = Servico(nome=s["nome"], preco=s["preco"], duracao_minutos=s["duracao_minutos"])
            db.session.add(novo)
    db.session.commit()
    print("Serviços inseridos no banco.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        popular_servicos()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)