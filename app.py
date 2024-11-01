from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

def create_db():
    conn = sqlite3.connect('todo_list.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tarefas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        custo REAL NOT NULL,
        data_limite TEXT,
        ordem_apresentacao INTEGER NOT NULL UNIQUE
    )''')
    conn.commit()
    conn.close()

create_db()

@app.route('/')
def index():
    conn = sqlite3.connect('todo_list.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tarefas ORDER BY ordem_apresentacao")
    tarefas = cursor.fetchall()
    conn.close()
    return render_template('index.html', tarefas=tarefas)

@app.route('/incluir', methods=['POST'])
def incluir():
    nome = request.form['nome']
    custo = float(request.form['custo'])
    data_limite = request.form['data_limite']
    conn = sqlite3.connect('todo_list.db')
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ordem_apresentacao) FROM tarefas")
    max_ordem = cursor.fetchone()[0] or 0
    try:
        cursor.execute("INSERT INTO tarefas (nome, custo, data_limite, ordem_apresentacao) VALUES (?, ?, ?, ?)", 
                       (nome, custo, data_limite, max_ordem + 1))
        conn.commit()
    except sqlite3.IntegrityError:
        flash("Erro: Nome da tarefa já existe.")
    conn.close()
    return redirect(url_for('index'))

@app.route('/excluir/<int:id>', methods=['GET', 'POST'])
def excluir(id):
    if request.method == 'POST':
        conn = sqlite3.connect('todo_list.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tarefas WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        flash('Tarefa excluída com sucesso!')
        return redirect(url_for('index'))
    return render_template('confirm_delete.html', id=id)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = sqlite3.connect('todo_list.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        nome = request.form['nome']
        custo = request.form['custo']
        data_limite = request.form['data_limite']
        try:
            cursor.execute("UPDATE tarefas SET nome = ?, custo = ?, data_limite = ? WHERE id = ?", 
                           (nome, custo, data_limite, id))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Erro: Nome da tarefa já existe.")
        conn.close()
        return redirect(url_for('index'))
    cursor.execute("SELECT * FROM tarefas WHERE id = ?", (id,))
    tarefa = cursor.fetchone()
    conn.close()
    return render_template('edit.html', tarefa=tarefa)

@app.route('/mover/<int:id>/<direcao>')
def mover(id, direcao):
    conn = sqlite3.connect('todo_list.db')
    cursor = conn.cursor()
    
    # Obter a tarefa atual e a ordem de apresentação
    cursor.execute("SELECT id, ordem_apresentacao FROM tarefas WHERE id = ?", (id,))
    tarefa_atual = cursor.fetchone()
    if not tarefa_atual:
        return redirect(url_for('index'))

    ordem_atual = tarefa_atual[1]
    nova_ordem = ordem_atual - 1 if direcao == 'subir' else ordem_atual + 1
    
    # Obter a tarefa vizinha na ordem desejada
    cursor.execute("SELECT id FROM tarefas WHERE ordem_apresentacao = ?", (nova_ordem,))
    tarefa_vizinha = cursor.fetchone()

    # Se houver uma tarefa na posição de destino, troque as posições
    if tarefa_vizinha:
        vizinha_id = tarefa_vizinha[0]
        
        # Passo 1: Definir uma posição temporária para evitar conflito
        cursor.execute("UPDATE tarefas SET ordem_apresentacao = -1 WHERE id = ?", (vizinha_id,))
        conn.commit()
        
        # Passo 2: Mover a tarefa atual para a nova posição
        cursor.execute("UPDATE tarefas SET ordem_apresentacao = ? WHERE id = ?", (nova_ordem, id))
        conn.commit()
        
        # Passo 3: Atribuir a nova posição para a tarefa vizinha
        cursor.execute("UPDATE tarefas SET ordem_apresentacao = ? WHERE id = ?", (ordem_atual, vizinha_id))
        conn.commit()

    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)