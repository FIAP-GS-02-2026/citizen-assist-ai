"""Classe Orientacao: um registro da base de conhecimento."""

# Tupla com os campos obrigatórios de cada orientação no JSON.
# Tupla porque a lista de campos não muda durante a execução.
CAMPOS_OBRIGATORIOS = (
    "id", "categoria", "titulo", "palavras_chave", "resposta",
    "documentos", "onde", "fonte", "verificado_em",
)

# Campos que precisam ser texto não vazio.
CAMPOS_TEXTO = ("categoria", "titulo", "resposta", "onde", "fonte", "verificado_em")

AVISO = "Aviso: este assistente NÃO é um canal oficial. Confirme no canal oficial antes de agir."


def _lista_de_textos(valor, pode_ser_vazia):
    """True se o valor é uma lista só com textos não vazios."""
    if not isinstance(valor, list) or (not valor and not pode_ser_vazia):
        return False
    return all(isinstance(item, str) and item.strip() for item in valor)


class Orientacao:
    """Guarda os dados de uma orientação e sabe exibi-la na tela."""

    def __init__(self, id, categoria, titulo, palavras_chave, resposta,
                 documentos, onde, fonte, verificado_em):
        self.id = id
        self.categoria = categoria
        self.titulo = titulo
        self.palavras_chave = palavras_chave
        self.resposta = resposta
        self.documentos = documentos
        self.onde = onde
        self.fonte = fonte
        self.verificado_em = verificado_em

    @classmethod
    def de_dicionario(cls, dados):
        """Cria uma Orientacao a partir de um dicionário do JSON, validando campos e tipos.

        Levanta ValueError se faltar campo ou se algum tipo estiver errado,
        para que um registro ruim seja ignorado em vez de derrubar o programa.
        """
        if not isinstance(dados, dict):
            raise ValueError("o registro não é um dicionário")
        faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in dados]
        if faltando:
            raise ValueError("campos ausentes: " + ", ".join(faltando))
        # bool é subclasse de int em Python, por isso a checagem extra.
        if not isinstance(dados["id"], int) or isinstance(dados["id"], bool):
            raise ValueError("id precisa ser um número inteiro")
        for campo in CAMPOS_TEXTO:
            if not isinstance(dados[campo], str) or not dados[campo].strip():
                raise ValueError(f"{campo} precisa ser um texto não vazio")
        if not _lista_de_textos(dados["palavras_chave"], pode_ser_vazia=False):
            raise ValueError("palavras_chave precisa ser uma lista de textos")
        if not _lista_de_textos(dados["documentos"], pode_ser_vazia=True):
            raise ValueError("documentos precisa ser uma lista de textos")
        return cls(**{campo: dados[campo] for campo in CAMPOS_OBRIGATORIOS})

    def exibir(self):
        """Mostra a orientação completa, com fonte, data de verificação e aviso."""
        print(f"\n>> {self.titulo} [{self.categoria}]")
        print(self.resposta)
        if self.documentos:
            print("Documentos necessários:")
            for documento in self.documentos:
                print(f"  - {documento}")
        else:
            print("Documentos necessários: nenhum.")
        print(f"Onde: {self.onde}")
        print(f"Fonte: {self.fonte} (verificado em {self.verificado_em})")
        print(AVISO)
