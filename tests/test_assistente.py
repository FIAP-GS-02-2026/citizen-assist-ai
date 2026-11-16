"""Bateria de testes do Citizen Assist AI Mobilidade.

Execute na raiz do projeto com: python -m unittest -v
Usa só a biblioteca padrão.
"""

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from assistente import Assistente, COLUNAS_CSV, contem_dado_pessoal  # noqa: E402
from base_conhecimento import BaseConhecimento, classificar_confianca, normalizar  # noqa: E402
from orientacao import CAMPOS_OBRIGATORIOS, Orientacao  # noqa: E402

BASE_REAL = os.path.join(RAIZ, "data", "base_conhecimento.json")

CARTAO_SUS = {
    "id": 3, "categoria": "Saúde", "titulo": "Fazer o Cartão Nacional de Saúde (Cartão SUS)",
    "palavras_chave": ["cartao sus", "cartao do sus", "sus", "cns"],
    "resposta": "Pode ser feito em uma UBS.", "documentos": ["CPF"], "onde": "UBS",
    "fonte": "https://www.gov.br/saude", "verificado_em": "2026-11-05",
}


def base_temporaria(pasta, conteudo):
    caminho = os.path.join(pasta, "base.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo if isinstance(conteudo, str) else json.dumps(conteudo))
    return caminho


class TestBaseReal(unittest.TestCase):
    """Requisitos da seção 4: mínimo de 10 orientações, 3 categorias, 3 palavras-chave, fonte e data."""

    def setUp(self):
        with open(BASE_REAL, encoding="utf-8") as arquivo:
            self.dados = json.load(arquivo)

    def test_minimos_do_enunciado(self):
        self.assertGreaterEqual(len(self.dados), 10)
        self.assertGreaterEqual(len({o["categoria"] for o in self.dados}), 3)

    def test_campos_obrigatorios_e_tipos(self):
        ids = set()
        for registro in self.dados:
            for campo in CAMPOS_OBRIGATORIOS:
                self.assertIn(campo, registro, f"id {registro.get('id')} sem {campo}")
                self.assertNotEqual(registro[campo], "", f"id {registro['id']} com {campo} vazio")
            self.assertIsInstance(registro["id"], int)
            self.assertNotIn(registro["id"], ids, "id duplicado")
            ids.add(registro["id"])
            self.assertGreaterEqual(len(registro["palavras_chave"]), 3, f"id {registro['id']}")
            self.assertTrue(registro["fonte"].startswith("https://"), f"id {registro['id']}")
            self.assertRegex(registro["verificado_em"], r"^\d{4}-\d{2}-\d{2}$")

    def test_fontes_oficiais(self):
        oficiais = ("sptrans.com.br", "prefeitura.sp.gov.br", "gov.br", "planalto.gov.br")
        for registro in self.dados:
            self.assertTrue(any(d in registro["fonte"] for d in oficiais), registro["fonte"])


class TestBusca(unittest.TestCase):

    def setUp(self):
        self.base = BaseConhecimento(BASE_REAL)
        self.assertTrue(self.base.carregar())

    def test_normalizar(self):
        self.assertEqual(normalizar("  Como FAÇO o Cartão do SUS?! "), " como faco o cartao do sus ")

    def test_exemplo_do_enunciado_vale_7_pontos(self):
        sus = Orientacao.de_dicionario(CARTAO_SUS)
        self.assertEqual(self.base.pontuar("Como faço o cartão do SUS?", sus), 7)
        self.assertEqual(classificar_confianca(7), "ALTA")

    def test_palavra_chave_so_casa_palavra_inteira(self):
        sus = Orientacao.de_dicionario(CARTAO_SUS)
        self.assertEqual(self.base.pontuar("o susto foi grande", sus), 0)

    def test_limites_de_confianca(self):
        self.assertEqual(classificar_confianca(6), "ALTA")
        self.assertEqual(classificar_confianca(5), "MÉDIA")
        self.assertEqual(classificar_confianca(3), "MÉDIA")
        self.assertIsNone(classificar_confianca(2))
        self.assertIsNone(classificar_confianca(0))

    def test_buscar_devolve_tuplas_ordenadas(self):
        resultados = self.base.buscar("quanto custa a passagem do ônibus no domingo")
        self.assertTrue(resultados)
        for item in resultados:
            self.assertIsInstance(item, tuple)
            self.assertIsInstance(item[0], int)
            self.assertIsInstance(item[1], Orientacao)
        pontos = [p for p, _ in resultados]
        self.assertEqual(pontos, sorted(pontos, reverse=True))

    def test_perguntas_reais_encontram_a_orientacao_certa(self):
        casos = {
            "Tenho 62 anos, preciso pagar ônibus?": 2,
            "Como faço o bilhete único?": 10,
            "perdi meu bilhete, e agora?": 12,
            "quanto custa a passagem": 8,
            "o ônibus é de graça no domingo?": 7,
            "como reclamar de ônibus lotado": 15,
            "sou estudante de faculdade, pago meia?": 5,
            "tem ônibus de madrugada?": 17,
            "como colocar crédito no cartão": 11,
            "meu filho é autista, tem direito?": 3,
        }
        for pergunta, esperado in casos.items():
            with self.subTest(pergunta=pergunta):
                resultados = self.base.buscar(pergunta)
                self.assertTrue(resultados, "nada encontrado")
                self.assertEqual(resultados[0][1].id, esperado)
                self.assertIsNotNone(classificar_confianca(resultados[0][0]))

    def test_fora_do_escopo_nao_encontra(self):
        for pergunta in ("quero uma receita de bolo", "qual a previsão do tempo"):
            resultados = self.base.buscar(pergunta)
            melhor = resultados[0][0] if resultados else 0
            self.assertIsNone(classificar_confianca(melhor), pergunta)

    def test_categorias_e_por_categoria(self):
        categorias = self.base.categorias()
        self.assertEqual(categorias, sorted(categorias))
        self.assertEqual(len(categorias), len(set(categorias)))
        for categoria in categorias:
            itens = self.base.por_categoria(categoria)
            self.assertTrue(itens)
            self.assertTrue(all(o.categoria == categoria for o in itens))


class TestArquivosRuins(unittest.TestCase):
    """JSON ausente ou corrompido não pode travar o programa."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def test_json_ausente(self):
        base = BaseConhecimento(os.path.join(self.pasta, "nao_existe.json"))
        self.assertFalse(base.carregar())
        self.assertIn("não encontrado", base.erro)
        self.assertEqual(base.buscar("idoso"), [])

    def test_json_corrompido(self):
        base = BaseConhecimento(base_temporaria(self.pasta, "[{ isso não é json"))
        self.assertFalse(base.carregar())
        self.assertIn("corrompido", base.erro)

    def test_json_que_nao_e_lista(self):
        base = BaseConhecimento(base_temporaria(self.pasta, {"a": 1}))
        self.assertFalse(base.carregar())

    def test_registro_incompleto_e_ignorado(self):
        incompleto = {"id": 9, "titulo": "sem campos"}
        base = BaseConhecimento(base_temporaria(self.pasta, [CARTAO_SUS, incompleto]))
        self.assertTrue(base.carregar())
        self.assertEqual(len(base.orientacoes), 1)
        self.assertIn("ignoradas", base.erro)

    def test_historico_corrompido_comeca_vazio(self):
        caminho = os.path.join(self.pasta, "historico.json")
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write("{{{")
        assistente = Assistente("t", BaseConhecimento(BASE_REAL), caminho, os.path.join(self.pasta, "a.csv"))
        self.assertEqual(assistente.historico, [])


class TestDadosPessoais(unittest.TestCase):

    def test_detecta(self):
        for texto in ("meu cpf é 123.456.789-00", "liga 11 98765-4321", "me manda em a@b.com", "12345678"):
            self.assertTrue(contem_dado_pessoal(texto), texto)

    def test_nao_bloqueia_pergunta_normal(self):
        for texto in ("tenho 62 anos", "linha 8000-10 passa no domingo?", "quanto custa a passagem"):
            self.assertFalse(contem_dado_pessoal(texto), texto)


class TestAtendimento(unittest.TestCase):
    """Fluxos do assistente com entradas simuladas."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        base = BaseConhecimento(BASE_REAL)
        base.carregar()
        self.assistente = Assistente("t", base, os.path.join(self.pasta, "historico.json"),
                                     os.path.join(self.pasta, "atendimentos.csv"))

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def rodar(self, metodo, entradas):
        with mock.patch("builtins.input", side_effect=entradas), mock.patch("builtins.print"):
            metodo()

    def test_pergunta_encontrada_e_registrada(self):
        self.rodar(self.assistente.perguntar, ["Como faço o bilhete único?", "x", "s"])
        self.assertEqual(len(self.assistente.historico), 1)
        atendimento = self.assistente.historico[0]
        self.assertEqual(atendimento["id_orientacao"], 10)
        self.assertTrue(atendimento["encontrou"])
        self.assertTrue(atendimento["ajudou"])
        self.assertEqual(atendimento["tentativas"], 1)
        self.assertEqual(atendimento["origem"], "pergunta")
        self.assertIsInstance(atendimento["tempo_s"], float)
        with open(self.assistente.caminho_historico, encoding="utf-8") as arquivo:
            self.assertEqual(len(json.load(arquivo)), 1)

    def test_dado_pessoal_nao_e_registrado(self):
        self.rodar(self.assistente.perguntar, ["meu cpf é 123.456.789-00", "a@b.com", "0"])
        self.assertEqual(self.assistente.historico, [])

    def test_nao_encontrada_depois_encontrada_conta_tentativas(self):
        self.rodar(self.assistente.perguntar, ["", "receita de bolo", "perdi meu bilhete", "s"])
        self.assertEqual(len(self.assistente.historico), 1)
        self.assertEqual(self.assistente.historico[0]["tentativas"], 2)
        self.assertEqual(self.assistente.historico[0]["id_orientacao"], 12)

    def test_desistir_vira_duvida_sem_solucao(self):
        self.rodar(self.assistente.perguntar, ["receita de bolo", "0"])
        atendimento = self.assistente.historico[0]
        self.assertFalse(atendimento["encontrou"])
        self.assertIsNone(atendimento["id_orientacao"])
        self.assertIn("receita de bolo", self.assistente.indicadores()["duvidas_sem_solucao"])

    def test_voltar_sem_perguntar_nao_registra(self):
        self.rodar(self.assistente.perguntar, ["0"])
        self.assertEqual(self.assistente.historico, [])

    def test_navegacao_com_entradas_invalidas(self):
        # categoria: letra, vazio, fora da faixa, depois 1; item: 99, depois 1; s/n inválido; voltar duas vezes
        entradas = ["a", "", "99", "1", "99", "1", "talvez", "n", "0", "0"]
        self.rodar(self.assistente.navegar, entradas)
        self.assertEqual(len(self.assistente.historico), 1)
        atendimento = self.assistente.historico[0]
        self.assertEqual(atendimento["origem"], "categoria")
        self.assertFalse(atendimento["ajudou"])

    def test_indicadores_e_csv(self):
        self.rodar(self.assistente.perguntar, ["Como faço o bilhete único?", "s"])
        self.rodar(self.assistente.perguntar, ["receita de bolo", "0"])
        self.assistente.registrar_nota(4)
        dados = self.assistente.indicadores()
        self.assertEqual(dados["total_atendimentos"], 2)
        self.assertEqual(dados["resposta_encontrada_pct"], 50.0)
        self.assertEqual(dados["taxa_acerto_ajudou_pct"], 50.0)
        self.assertEqual(dados["tentativas_media"], 1.0)
        self.assertEqual(dados["facilidade_media"], 4)
        with mock.patch("builtins.print"):
            self.assertTrue(self.assistente.exportar_csv())
        with open(self.assistente.caminho_csv, encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))
        self.assertEqual(len(linhas), 2)
        self.assertEqual(tuple(linhas[0].keys()), COLUNAS_CSV)
        self.assertEqual(linhas[0]["nota_facilidade"], "4")

    def test_indicadores_sem_dados(self):
        self.assertEqual(self.assistente.indicadores()["total_atendimentos"], 0)
        with mock.patch("builtins.print"):
            self.assistente.exibir_indicadores()


class TestProgramaCompleto(unittest.TestCase):
    """Roda python main.py de verdade numa cópia do projeto, com entradas pelo teclado simulado."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        for nome in ("main.py", "orientacao.py", "base_conhecimento.py", "assistente.py"):
            shutil.copy(os.path.join(RAIZ, nome), self.pasta)
        os.makedirs(os.path.join(self.pasta, "data"))
        shutil.copy(BASE_REAL, os.path.join(self.pasta, "data"))

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def executar(self, entradas):
        return subprocess.run([sys.executable, "main.py"], cwd=self.pasta, input="\n".join(entradas) + "\n",
                              capture_output=True, text=True, timeout=30)

    def test_sessao_completa(self):
        entradas = [
            "abc", "", "9",                              # menu: letra, vazio, fora da faixa
            "1", "meu telefone é 11987654321", "como tirar o bilhete único", "s",
            "1", "receita de bolo", "0",
            "2", "1", "1", "s", "0", "0",
            "3", "4",
            "0", "7", "x", "5",                          # nota fora da faixa e letra antes da válida
        ]
        resultado = self.executar(entradas)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(resultado.stderr, "")
        saida = resultado.stdout
        self.assertIn("Confiança da resposta: ALTA", saida)
        self.assertIn("não digite CPF", saida)
        self.assertIn("Não encontrei", saida)
        self.assertIn("NÃO é um canal oficial", saida)
        self.assertIn("Fonte: https://", saida)
        self.assertIn("Opção fora da faixa", saida)
        with open(os.path.join(self.pasta, "data", "historico.json"), encoding="utf-8") as arquivo:
            historico = json.load(arquivo)
        self.assertEqual(len(historico), 3)
        self.assertTrue(all(a["nota_facilidade"] == 5 for a in historico))
        self.assertNotIn("11987654321", json.dumps(historico))
        self.assertTrue(os.path.exists(os.path.join(self.pasta, "data", "atendimentos.csv")))

    def test_fim_de_entrada_nao_trava(self):
        # Só uma opção e acaba a entrada: o programa precisa terminar sem traceback.
        resultado = subprocess.run([sys.executable, "main.py"], cwd=self.pasta, input="1\n",
                                   capture_output=True, text=True, timeout=10)
        self.assertNotIn("Traceback", resultado.stderr)
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("encerrado", resultado.stdout)

    def test_base_corrompida_nao_trava(self):
        with open(os.path.join(self.pasta, "data", "base_conhecimento.json"), "w", encoding="utf-8") as arquivo:
            arquivo.write("{corrompido")
        resultado = self.executar(["1", "3", "0", "3"])
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn("corrompido", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
