import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QMessageBox, QInputDialog,
    QGroupBox, QScrollArea, QGridLayout, QHeaderView, QDateEdit, QTextEdit
)
from PyQt5.QtCore import QDateTime, Qt, QDate
import sqlite3

DB_NAME = "estoque.db"

class DBManager:
    @staticmethod
    def initialize_database():
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco REAL NOT NULL
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                status TEXT NOT NULL,
                data_hora TEXT,
                itens TEXT NOT NULL
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS fluxo_caixa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL,
                valor REAL NOT NULL
            )''')
            conn.commit()

    @staticmethod
    def execute_query(query, params=None):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()

class EstoqueApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Estoque e Vendas")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.create_navigation_menu(layout)
        self.create_content_area(layout)
        self.create_footer(layout)

        self.mostrar_kanban()

    def create_navigation_menu(self, layout):
        menu_layout = QHBoxLayout()
        buttons = [
            ("Venda de Produtos", self.mostrar_venda),
            ("Gerenciar Estoque", self.mostrar_estoque),
            ("Histórico de Pedidos", self.mostrar_historico),
            ("Kanban de Pedidos", self.mostrar_kanban),
            ("Registrar Despesa", self.registrar_despesa)
        ]

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            menu_layout.addWidget(btn)

        layout.addLayout(menu_layout)

    def create_content_area(self, layout):
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        layout.addWidget(self.content_area)

    def create_footer(self, layout):
        footer_label = QLabel("Sistema de Venda FronyTech 1.0")
        footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer_label)

    def limpar_content_area(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def mostrar_kanban(self):
        self.limpar_content_area()
        self.kanban = KanbanPedidos(self)
        self.content_layout.addWidget(self.kanban)

    def mostrar_venda(self):
        self.limpar_content_area()
        venda = VendaProdutos(self)
        self.content_layout.addWidget(venda)

    def mostrar_estoque(self):
        self.limpar_content_area()
        self.estoque = GerenciarEstoque(self)
        self.content_layout.addWidget(self.estoque)

    def mostrar_historico(self):
        self.limpar_content_area()
        historico = HistoricoPedidos(self)
        self.content_layout.addWidget(historico)

    def registrar_despesa(self):
        valor, ok = QInputDialog.getDouble(self, "Registrar Despesa", "Valor da despesa:", 0, 0, 1000000, 2)
        if ok:
            descricao, ok = QInputDialog.getText(self, "Registrar Despesa", "Descrição da despesa:")
            if ok:
                data_atual = QDateTime.currentDateTime().toString("yyyy-MM-dd")
                DBManager.execute_query("INSERT INTO fluxo_caixa (data, tipo, valor) VALUES (?, ?, ?)",
                                        (data_atual, f"Despesa: {descricao}", valor))
                QMessageBox.information(self, "Sucesso", "Despesa registrada com sucesso!")

class KanbanPedidos(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        self.coluna_abertos = self.criar_coluna("Pedidos Abertos")
        self.coluna_andamento = self.criar_coluna("Em Andamento")
        self.coluna_finalizados = self.criar_coluna("Finalizados")

        layout.addWidget(self.coluna_abertos)
        layout.addWidget(self.coluna_andamento)
        layout.addWidget(self.coluna_finalizados)

        self.carregar_pedidos()

    def criar_coluna(self, titulo):
        grupo = QGroupBox(titulo)
        layout = QVBoxLayout(grupo)
        scroll = QScrollArea()
        content = QWidget()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        content_layout = QVBoxLayout(content)
        content_layout.addStretch(1)
        layout.addWidget(scroll)
        return grupo

    def carregar_pedidos(self):
        pedidos = DBManager.execute_query("SELECT id, cliente, status, data_hora, itens FROM pedidos WHERE status != 'Concluído'")
        for pedido in pedidos:
            self.adicionar_pedido_kanban(pedido)

    def adicionar_pedido_kanban(self, pedido):
        id, cliente, status, data_hora, itens = pedido
        pedido_widget = QWidget()
        layout = QVBoxLayout(pedido_widget)
        
        layout.addWidget(QLabel(f"Pedido #{id}"))
        layout.addWidget(QLabel(f"Cliente: {cliente}"))
        layout.addWidget(QLabel(f"Data: {data_hora}"))
        layout.addWidget(QLabel(f"Itens: {itens}"))
        
        if status == "Finalizado":
            btn_text = "Concluir"
            btn_avancar = QPushButton(btn_text)
            btn_avancar.setStyleSheet("font-size: 14px; padding: 8px;")
            btn_avancar.clicked.connect(lambda: self.concluir_pedido(id))
        else:
            btn_text = "Avançar"
            btn_avancar = QPushButton(btn_text)
            btn_avancar.setStyleSheet("font-size: 14px; padding: 8px;")
            btn_avancar.clicked.connect(lambda: self.avancar_pedido(id, status))
        layout.addWidget(btn_avancar)

        coluna = self.coluna_abertos if status == "Aberto" else self.coluna_andamento if status == "Em Andamento" else self.coluna_finalizados
        coluna.findChild(QScrollArea).widget().layout().insertWidget(0, pedido_widget)

    def avancar_pedido(self, pedido_id, status_atual):
        novo_status = "Em Andamento" if status_atual == "Aberto" else "Finalizado"
        DBManager.execute_query("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        self.atualizar_kanban()

    def concluir_pedido(self, pedido_id):
        DBManager.execute_query("UPDATE pedidos SET status = 'Concluído' WHERE id = ?", (pedido_id,))
        QMessageBox.information(self, "Sucesso", f"Pedido #{pedido_id} foi concluído e removido do Kanban.")
        self.atualizar_kanban()

    def limpar_kanban(self):
        for coluna in [self.coluna_abertos, self.coluna_andamento, self.coluna_finalizados]:
            scroll_area = coluna.findChild(QScrollArea)
            layout = scroll_area.widget().layout()
            for i in reversed(range(layout.count()-1)):
                layout.itemAt(i).widget().setParent(None)

    def atualizar_kanban(self):
        self.limpar_kanban()
        self.carregar_pedidos()

class VendaProdutos(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.itens_pedido = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.btn_novo_pedido = QPushButton("Fazer Novo Pedido")
        self.btn_novo_pedido.clicked.connect(self.iniciar_novo_pedido)
        layout.addWidget(self.btn_novo_pedido)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        self.produtos_layout = QVBoxLayout(self.scroll_content)
        layout.addWidget(self.scroll_area)

        self.area_itens_pedido = QVBoxLayout()
        layout.addLayout(self.area_itens_pedido)

        self.btn_finalizar_pedido = QPushButton("Finalizar Pedido")
        self.btn_finalizar_pedido.clicked.connect(self.finalizar_pedido)
        self.btn_finalizar_pedido.hide()
        layout.addWidget(self.btn_finalizar_pedido)

        self.btn_voltar_kanban = QPushButton("Voltar ao Kanban")
        self.btn_voltar_kanban.clicked.connect(self.voltar_ao_kanban)
        self.btn_voltar_kanban.hide()
        layout.addWidget(self.btn_voltar_kanban)

    def iniciar_novo_pedido(self):
        self.itens_pedido = []
        self.limpar_area_itens()
        self.mostrar_produtos()
        self.btn_novo_pedido.hide()
        self.btn_finalizar_pedido.show()
        self.btn_voltar_kanban.show()

    def mostrar_produtos(self):
        produtos = DBManager.execute_query("SELECT id, nome, quantidade, preco FROM produtos")

        for i in reversed(range(self.produtos_layout.count())): 
            self.produtos_layout.itemAt(i).widget().setParent(None)

        grid_layout = QGridLayout()
        for i, produto in enumerate(produtos):
            btn = QPushButton(f"{produto[1]}\nR$ {produto[3]:.2f}")
            btn.clicked.connect(lambda _, p=produto: self.adicionar_ao_pedido(p))
            grid_layout.addWidget(btn, i // 3, i % 3)

        self.produtos_layout.addLayout(grid_layout)

    def adicionar_ao_pedido(self, produto):
        quantidade_disponivel = produto[2]  # A quantidade está no índice 2 da tupla do produto
        if quantidade_disponivel <= 0:
            QMessageBox.warning(self, "Erro", f"O produto {produto[1]} está fora de estoque.")
            return

        quantidade, ok = QInputDialog.getInt(self, "Quantidade", f"Quantidade de {produto[1]} (máx. {quantidade_disponivel}):", 1, 1, quantidade_disponivel)
        if ok:
            self.itens_pedido.append((produto, quantidade))
            self.atualizar_lista_itens()

    def atualizar_lista_itens(self):
        self.limpar_area_itens()
        subtotal = 0
        for item in self.itens_pedido:
            produto, quantidade = item
            valor_item = produto[3] * quantidade
            subtotal += valor_item
            self.area_itens_pedido.addWidget(QLabel(f"{quantidade}x {produto[1]} - R$ {valor_item:.2f}"))
    
        # Adicionar o subtotal
        self.area_itens_pedido.addWidget(QLabel(f"Subtotal: R$ {subtotal:.2f}"))


    def limpar_area_itens(self):
        for i in reversed(range(self.area_itens_pedido.count())):
            layout_item = self.area_itens_pedido.itemAt(i)
            if layout_item.widget():
                layout_item.widget().setParent(None)
            elif layout_item.layout():
                self.limpar_layout(layout_item.layout())

    def limpar_layout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self.limpar_layout(item.layout())

    def finalizar_pedido(self):
        if not self.itens_pedido: # se vazio !!
            QMessageBox.warning(self, "Erro", "Adicione itens ao pedido antes de finalizar!")
            return

        cliente, ok = QInputDialog.getText(self, "Nome do Cliente", "Digite o nome do cliente:")
        if ok and cliente:
            itens_str = ", ".join([f"{q}x {p[1]}" for p, q in self.itens_pedido])
            data_hora = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

            DBManager.execute_query("INSERT INTO pedidos (cliente, status, data_hora, itens) VALUES (?, ?, ?, ?)",
                                    (cliente, "Aberto", data_hora, itens_str))

            for produto, quantidade in self.itens_pedido:
                DBManager.execute_query("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?", (quantidade, produto[0]))

            total_venda = sum(p[3] * q for p, q in self.itens_pedido)
            DBManager.execute_query("INSERT INTO fluxo_caixa (data, tipo, valor) VALUES (?, ?, ?)",
                                    (QDate.currentDate().toString("yyyy-MM-dd"), "Venda", total_venda))

            self.voltar_ao_kanban()
        else:
            QMessageBox.warning(self, "Erro", "É necessário informar o nome do cliente!")

    def voltar_ao_kanban(self):
        self.parent.mostrar_kanban()

class GerenciarEstoque(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome do produto")
        layout.addWidget(self.nome)

        self.quantidade = QLineEdit()
        self.quantidade.setPlaceholderText("Quantidade")
        layout.addWidget(self.quantidade)

        self.preco = QLineEdit()
        self.preco.setPlaceholderText("Preço")
        layout.addWidget(self.preco)

        btn_adicionar = QPushButton("Adicionar Produto")
        btn_adicionar.clicked.connect(self.adicionar_produto)
        layout.addWidget(btn_adicionar)

        btn_layout = QHBoxLayout()
        btn_editar = QPushButton("Editar Produto")
        btn_editar.clicked.connect(self.editar_produto)
        btn_layout.addWidget(btn_editar)

        btn_excluir = QPushButton("Excluir Produto")
        btn_excluir.clicked.connect(self.excluir_produto)
        btn_layout.addWidget(btn_excluir)

        layout.addLayout(btn_layout)

        self.tabela_produtos = QTableWidget()
        self.tabela_produtos.setColumnCount(4)
        self.tabela_produtos.setHorizontalHeaderLabels(["ID", "Nome", "Quantidade", "Preço"])
        self.tabela_produtos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_produtos)

        self.carregar_produtos()

    def carregar_produtos(self):
        produtos = DBManager.execute_query("SELECT id, nome, quantidade, preco FROM produtos")
        self.tabela_produtos.setRowCount(len(produtos))
        for row, produto in enumerate(produtos):
            for col, valor in enumerate(produto):
                self.tabela_produtos.setItem(row, col, QTableWidgetItem(str(valor)))

    def adicionar_produto(self):
        nome = self.nome.text()
        quantidade = self.quantidade.text()
        preco = self.preco.text()

        if not nome or not quantidade or not preco:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return

        try:
            quantidade = int(quantidade)
            preco = float(preco)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Quantidade deve ser um número inteiro e Preço deve ser um número decimal!")
            return

        DBManager.execute_query("INSERT INTO produtos (nome, quantidade, preco) VALUES (?, ?, ?)",
                                (nome, quantidade, preco))

        QMessageBox.information(self, "Sucesso", "Produto adicionado com sucesso!")
        self.nome.clear()
        self.quantidade.clear()
        self.preco.clear()
        self.carregar_produtos()

    def excluir_produto(self):
        row = self.tabela_produtos.currentRow()
        if row > -1:
            produto_id = self.tabela_produtos.item(row, 0).text()
            confirma = QMessageBox.question(self, 'Confirmar Exclusão',
                                            "Tem certeza que deseja excluir este produto?",
                                            QMessageBox.Yes | QMessageBox.No)
            if confirma == QMessageBox.Yes:
                DBManager.execute_query("DELETE FROM produtos WHERE id = ?", (produto_id,))
                self.carregar_produtos()
        else:
            QMessageBox.warning(self, "Erro", "Selecione um produto para excluir.")

    def editar_produto(self):
        row = self.tabela_produtos.currentRow()
        if row > -1:
            produto_id = self.tabela_produtos.item(row, 0).text()
            nome_atual = self.tabela_produtos.item(row, 1).text()
            quantidade_atual = self.tabela_produtos.item(row, 2).text()
            preco_atual = self.tabela_produtos.item(row, 3).text()

            nome, ok1 = QInputDialog.getText(self, 'Editar Produto', 'Nome:', text=nome_atual)
            if ok1:
                quantidade, ok2 = QInputDialog.getInt(self, 'Editar Produto', 'Quantidade:', int(quantidade_atual))
                if ok2:
                    preco, ok3 = QInputDialog.getDouble(self, 'Editar Produto', 'Preço:', float(preco_atual))
                    if ok3:
                        DBManager.execute_query("UPDATE produtos SET nome = ?, quantidade = ?, preco = ? WHERE id = ?",
                                                (nome, quantidade, preco, produto_id))
                        self.carregar_produtos()
        else:
            QMessageBox.warning(self, "Erro", "Selecione um produto para editar.")


class HistoricoPedidos(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.date_select = QDateEdit(calendarPopup=True)
        self.date_select.setDate(QDate.currentDate())
        self.date_select.dateChanged.connect(self.atualizar_relatorio)
        layout.addWidget(self.date_select)

        btn_gerar_relatorio = QPushButton("Gerar Relatório")
        btn_gerar_relatorio.clicked.connect(self.atualizar_relatorio)
        layout.addWidget(btn_gerar_relatorio)

        self.relatorio_area = QTextEdit()
        self.relatorio_area.setReadOnly(True)
        layout.addWidget(self.relatorio_area)

        self.tabela_historico = QTableWidget()
        self.tabela_historico.setColumnCount(5)
        self.tabela_historico.setHorizontalHeaderLabels(["ID", "Cliente", "Status", "Data/Hora", "Itens"])
        self.tabela_historico.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_historico)

        self.carregar_historico()
        self.atualizar_relatorio()

    def carregar_historico(self):
        pedidos = DBManager.execute_query("SELECT id, cliente, status, data_hora, itens FROM pedidos ORDER BY data_hora DESC")
        self.tabela_historico.setRowCount(len(pedidos))
        for row, pedido in enumerate(pedidos):
            for col, valor in enumerate(pedido):
                self.tabela_historico.setItem(row, col, QTableWidgetItem(str(valor)))

    def atualizar_relatorio(self):
        data_selecionada = self.date_select.date().toString("yyyy-MM-dd")
        
        total_vendas = DBManager.execute_query("SELECT SUM(valor) FROM fluxo_caixa WHERE data = ? AND tipo = 'Venda'", (data_selecionada,))[0][0] or 0
        total_despesas = DBManager.execute_query("SELECT SUM(valor) FROM fluxo_caixa WHERE data = ? AND tipo LIKE 'Despesa%'", (data_selecionada,))[0][0] or 0
        detalhes = DBManager.execute_query("SELECT * FROM fluxo_caixa WHERE data = ? ORDER BY tipo", (data_selecionada,))
        
        relatorio = f"Relatório de Caixa - {data_selecionada}\n\n"
        relatorio += f"Total de Vendas: R$ {total_vendas:.2f}\n"
        relatorio += f"Total de Despesas: R$ {total_despesas:.2f}\n"
        relatorio += f"Saldo do Dia: R$ {total_vendas - total_despesas:.2f}\n\n"
        relatorio += "Detalhes:\n"
        
        # Buscar todas as vendas do dia
        vendas = DBManager.execute_query("SELECT id, cliente, itens FROM pedidos WHERE data_hora LIKE ?", (f"{data_selecionada}%",))
        
        for item in detalhes:
            if item[2] == "Venda":
                venda_id = item[0]  # Assumindo que o ID da venda no fluxo_caixa corresponde ao ID do pedido
                venda = next((v for v in vendas if v[0] == venda_id), None)
                if venda:
                    relatorio += f"Venda #{venda[0]} - Cliente: {venda[1]} - R$ {item[3]:.2f}\n"
                    relatorio += f"  Itens: {venda[2]}\n"
                else:
                    relatorio += f"{item[2]}: R$ {item[3]:.2f}\n"
            else:
                relatorio += f"{item[2]}: R$ {item[3]:.2f}\n"
    
        self.relatorio_area.setText(relatorio)

if __name__ == "__main__":
    DBManager.initialize_database()
    app = QApplication(sys.argv)
    janela = EstoqueApp()
    janela.show()
    sys.exit(app.exec_())

