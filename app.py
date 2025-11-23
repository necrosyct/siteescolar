from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from sqlalchemy.exc import IntegrityError 
import os # Importado para manipulação de caminhos de arquivo
from werkzeug.utils import secure_filename # Importado para proteger nomes de arquivo

# --- Configuração do Flask e Banco de Dados ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_muito_forte_para_o_sistema_escola' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# NOVO: Configuração para upload de arquivos
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Função auxiliar para verificar a extensão do arquivo
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Modelos do Banco de Dados (Sem Alterações Aqui) ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False) 
    tipo = db.Column(db.String(10), nullable=False) 
    
    turma = db.Column(db.String(50), nullable=True)
    ano_letivo = db.Column(db.String(4), nullable=True) 
    # Agora armazena o nome do arquivo, que estará em static/uploads/
    foto_perfil = db.Column(db.String(255), nullable=True, default='default_user.png') 

    ocorrencias_enviadas = db.relationship('Ocorrencia', foreign_keys='Ocorrencia.professor_id', backref='professor', lazy=True)
    ocorrencias_recebidas = db.relationship('Ocorrencia', foreign_keys='Ocorrencia.aluno_id', backref='aluno_info', lazy=True)
    licoes = db.relationship('Licao', backref='professor_licao', lazy=True)

class Ocorrencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data = db.Column(db.String(20), nullable=False)

class Licao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prazo = db.Column(db.String(20), nullable=False)

# --- Funções de Inicialização e Rotas ---

def inicializar_banco_e_usuarios():
    with app.app_context():
        db.create_all()
        
        if Usuario.query.first() is None:
            # Garante que a pasta de upload exista
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
                
            db.session.add(Usuario(nome='Administrador Master', usuario='admin', senha='123', tipo='professor')) 
            db.session.add(Usuario(nome='Professor Teste', usuario='prof', senha='123', tipo='professor'))
            db.session.add(Usuario(nome='João da Silva', usuario='joao', senha='456', tipo='aluno', turma='A', ano_letivo='2025', foto_perfil='default_user.png'))
            db.session.add(Usuario(nome='Maria de Souza', usuario='maria', senha='456', tipo='aluno', turma='B', ano_letivo='2026', foto_perfil='default_user.png'))
            
            db.session.commit()
            print("Banco de dados e usuários iniciais criados.")

# Rotas de login, logout, professor_dashboard e aluno_dashboard (MANTIDAS COMO ANTES)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_digitado = request.form['usuario']
        senha_digitada = request.form['senha']
        
        user = Usuario.query.filter_by(usuario=usuario_digitado, senha=senha_digitada).first()
        
        if user:
            session['user_id'] = user.id
            session['user_tipo'] = user.tipo
            session['user_nome'] = user.nome
            session['user_username'] = user.usuario 

            if user.usuario == 'admin':
                return redirect(url_for('admin_dashboard'))
                
            elif user.tipo == 'professor':
                return redirect(url_for('dashboard_professor'))
            
            else: 
                return redirect(url_for('dashboard_aluno'))
        else:
            return render_template('login.html', erro="Usuário ou senha incorretos.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_tipo', None)
    session.pop('user_nome', None)
    session.pop('user_username', None) 
    return redirect(url_for('index'))

@app.route('/professor/dashboard', methods=['GET', 'POST'])
def dashboard_professor():
    if session.get('user_tipo') != 'professor':
        return redirect(url_for('login'))
        
    professor_id = session['user_id']
    alunos = Usuario.query.filter_by(tipo='aluno').order_by(Usuario.nome).all()
    
    if request.method == 'POST':
        if request.form.get('acao') == 'ocorrencia': 
            aluno_id = request.form.get('aluno_ocorrencia')
            descricao = request.form.get('descricao_ocorrencia')
            
            nova_ocorrencia = Ocorrencia(
                aluno_id=aluno_id, 
                professor_id=professor_id, 
                descricao=descricao, 
                data=str(date.today())
            )
            db.session.add(nova_ocorrencia)
            db.session.commit()
            return redirect(url_for('dashboard_professor', mensagem_sucesso='Ocorrência registrada!'))
            
        elif request.form.get('acao') == 'licao': 
            descricao = request.form.get('licao_descricao')
            prazo = request.form.get('licao_prazo')
            
            nova_licao = Licao(
                professor_id=professor_id, 
                descricao=descricao, 
                prazo=prazo
            )
            db.session.add(nova_licao)
            db.session.commit()
            return redirect(url_for('dashboard_professor', mensagem_sucesso='Lição de casa adicionada!'))
            
    mensagem = request.args.get('mensagem_sucesso')
    return render_template('professor_dashboard.html', 
                           alunos=alunos, 
                           mensagem_sucesso=mensagem,
                           nome_professor=session['user_nome'])

@app.route('/aluno/dashboard')
def dashboard_aluno():
    if session.get('user_tipo') != 'aluno':
        return redirect(url_for('login'))
        
    aluno_id = session['user_id']
    aluno_info = Usuario.query.get(aluno_id)
    
    ocorrencias = Ocorrencia.query.filter_by(aluno_id=aluno_id).order_by(Ocorrencia.data.desc()).all()
    licoes = Licao.query.order_by(Licao.prazo).all()
    
    return render_template('aluno_dashboard.html', 
        aluno=aluno_info, 
        ocorrencias=ocorrencias, 
        licoes=licoes
    )

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # RESTRIÇÃO DE ACESSO
    if session.get('user_username') != 'admin':
        if session.get('user_tipo') == 'professor':
            return redirect(url_for('dashboard_professor')) 
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'adicionar':
            nome = request.form.get('nome')
            usuario_novo = request.form.get('usuario')
            senha = request.form.get('senha')
            tipo = request.form.get('tipo')
            turma = request.form.get('turma')
            ano_letivo = request.form.get('ano_letivo')

            try:
                novo_usuario = Usuario(nome=nome, usuario=usuario_novo, senha=senha, tipo=tipo, turma=turma, ano_letivo=ano_letivo)
                db.session.add(novo_usuario)
                db.session.commit()
                return redirect(url_for('admin_dashboard', mensagem_admin='Usuário adicionado com sucesso!'))
            except IntegrityError:
                db.session.rollback()
                return redirect(url_for('admin_dashboard', erro_admin='Erro: Nome de usuário já existe.'))
        
        elif acao == 'remover':
            usuario_id = request.form.get('usuario_id')
            usuario_a_remover = Usuario.query.get(usuario_id)
            
            if usuario_a_remover:
                # Remove dados relacionados
                Ocorrencia.query.filter((Ocorrencia.aluno_id == usuario_id) | (Ocorrencia.professor_id == usuario_id)).delete(synchronize_session=False)
                Licao.query.filter(Licao.professor_id == usuario_id).delete(synchronize_session=False)

                # Apaga o arquivo de foto se não for o default
                if usuario_a_remover.foto_perfil and usuario_a_remover.foto_perfil != 'default_user.png':
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], usuario_a_remover.foto_perfil))
                    except OSError:
                        pass # Ignora se o arquivo não existir

                db.session.delete(usuario_a_remover)
                db.session.commit()
                return redirect(url_for('admin_dashboard', mensagem_admin='Usuário removido com sucesso!'))

    alunos = Usuario.query.filter_by(tipo='aluno').order_by(Usuario.nome).all()
    professores = Usuario.query.filter_by(tipo='professor').order_by(Usuario.nome).all()
    
    mensagem = request.args.get('mensagem_admin')
    erro = request.args.get('erro_admin')

    return render_template('admin_dashboard.html', 
                           alunos=alunos, 
                           professores=professores, 
                           mensagem_admin=mensagem,
                           erro_admin=erro)

@app.route('/admin/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    # Restrição de acesso ao admin
    if session.get('user_username') != 'admin':
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(user_id)

    if request.method == 'POST':
        
        # Lógica de Upload de Arquivo
        if 'foto_upload' in request.files:
            file = request.files['foto_upload']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Cria um nome único baseado no ID do usuário para evitar conflitos
                unique_filename = f'{usuario.id}_{filename}'
                
                # Apaga a foto antiga (se não for a default)
                if usuario.foto_perfil and usuario.foto_perfil != 'default_user.png':
                     try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], usuario.foto_perfil))
                     except OSError:
                        pass

                # Salva o novo arquivo
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                usuario.foto_perfil = unique_filename
        
        # Atualização dos demais campos
        usuario.nome = request.form['nome']
        usuario.usuario = request.form['usuario']
        if request.form['senha']:
            usuario.senha = request.form['senha']
            
        usuario.tipo = request.form['tipo']
        usuario.turma = request.form['turma']
        usuario.ano_letivo = request.form['ano_letivo']
        
        try:
            db.session.commit()
            return redirect(url_for('admin_dashboard', mensagem_admin=f'Perfil de {usuario.nome} atualizado com sucesso!'))
        except IntegrityError:
            db.session.rollback()
            return render_template('admin_editar_usuario.html', usuario=usuario, erro='Erro: Nome de usuário já existe.')

    return render_template('admin_editar_usuario.html', usuario=usuario)
