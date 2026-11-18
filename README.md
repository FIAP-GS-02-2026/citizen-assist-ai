# Citizen Assist AI Mobilidade

Assistente no terminal que orienta quem usa ônibus na cidade de São Paulo sobre gratuidades, Bilhete Único, tarifas, acessibilidade e onde reclamar, e quem usa bicicleta ou patinete elétrico sobre recarga, energia solar e regras de circulação. Ele responde só com informações de fontes oficiais, mostra a fonte e a data em que ela foi conferida e avisa que não é um canal oficial.

Global Solution 2026.2 · FIAP · Ciência da Computação 1CCR · Pensamento Computacional e Automação com Python.

## Integrantes

| Nome | RM |
| --- | --- |
| Glauco Kelly | 572840 |
| Gabriel Fagundes | 569074 |
| Thiago Renatino | 569073 |

## Público e problema

**Público:** quem depende do ônibus municipal em São Paulo, principalmente pessoas idosas, pessoas com deficiência, estudantes e pessoas com pouca familiaridade digital.

**Problema:** a informação sobre direitos e serviços do transporte existe, mas está espalhada entre SP156, SPTrans e Prefeitura. Ainda circula informação antiga, como a de que a gratuidade do idoso só começa aos 65 anos; desde o Decreto Municipal 62.057/2022 ela vale a partir dos 60. Pouca gente também sabe que o ônibus municipal é de graça aos domingos. O assistente reúne essas orientações num só lugar, em linguagem simples e com a fonte.

## ODS relacionados

- **ODS 11 (Cidades e comunidades sustentáveis)**, meta 11.2: acesso a transporte seguro, acessível e sustentável, com atenção a pessoas idosas e com deficiência.
- **ODS 10 (Redução das desigualdades)**: informação sobre gratuidades para quem mais precisa delas.

## Como executar

Requer Python 3.9 ou superior e não usa bibliotecas externas.

```bash
python main.py
```

Testes automatizados (opcional):

```bash
python -m unittest -v
```

## Estrutura

```
citizen-assist-ai/
├── README.md
├── main.py                  menu principal
├── orientacao.py            classe Orientacao (um registro da base)
├── base_conhecimento.py     classe BaseConhecimento e a busca por pontuação
├── assistente.py            classe Assistente: atendimento, histórico, indicadores e CSV
├── data/
│   ├── base_conhecimento.json   orientações com fonte oficial
│   ├── historico.json           atendimentos registrados
│   └── atendimentos.csv         exportação dos atendimentos
└── tests/                   47 testes (unittest) e bateria de perguntas reais
```

**Composição das classes:**

```
Assistente
 └── base: BaseConhecimento
      └── orientacoes: [Orientacao, Orientacao, ...]
```

## Base de conhecimento

O arquivo `data/base_conhecimento.json` é uma lista de dicionários, um por orientação. Cada registro tem os campos `id`, `categoria`, `titulo`, `palavras_chave`, `resposta`, `documentos`, `onde`, `fonte` e `verificado_em`.

- São 24 orientações em 7 categorias: Gratuidades, Tarifas, Bilhete Único, Acessibilidade, Atendimento e reclamação, Linhas e horários, Energia e mobilidade elétrica.
- Em 16/11/2026 (orientações 1 a 17), 17/11/2026 (18 a 22) e 18/11/2026 (23 e 24), a equipe abriu cada página oficial citada e conferiu, frase a frase, se a resposta estava escrita nela. O que não estava foi retirado.
- A orientação 23 é a única com estimativa da equipe: ela resume a análise de energia (custo de carregar na tomada, na Tarifa Branca e com energia solar). A resposta avisa que são estimativas, a fonte é a tarifa oficial da Enel e o campo "onde" aponta o repositório com os cálculos, as premissas e as limitações.
- Ao carregar, o programa valida os tipos de cada registro. Registro incompleto, com tipo errado ou com `id` repetido é ignorado com aviso.

**Uso de dicionários e tuplas:**

- Cada registro do JSON é lido como dicionário e vira um objeto `Orientacao`.
- Os campos obrigatórios ficam numa tupla (`CAMPOS_OBRIGATORIOS`), e as colunas do CSV em outra (`COLUNAS_CSV`).
- A busca devolve tuplas `(pontos, orientacao)`.
- Cada atendimento é guardado como dicionário no histórico.

## Regra de pontuação

A pergunta, as palavras-chave e o título são comparados sem acentos, sem pontuação e em minúsculas pela função `normalizar()`.

| Regra | Resultado |
| --- | --- |
| Palavra-chave da orientação aparece na pergunta (palavra inteira) | +3 pontos |
| Palavra da pergunta com 4 letras ou mais aparece no título | +1 ponto |
| Melhor orientação com 6 pontos ou mais | Confiança ALTA |
| Melhor orientação com 3 a 5 pontos | Confiança MÉDIA |
| Nenhuma orientação com 3 pontos | "Não encontrei" + sugestão de categorias |

`buscar()` devolve a lista de tuplas `(pontos, orientacao)` da maior para a menor pontuação. Em empate, vem primeiro o menor `id`. O assistente mostra a melhor orientação e até duas alternativas com pelo menos 3 pontos.

**Exemplo:** "Tenho 62 anos, pago ônibus?" soma 5 pontos na orientação 2 e fica com confiança MÉDIA:

- +3 pela palavra-chave "62 anos";
- +1 por "anos" no título;
- +1 por "onibus" no título.

**Ajustes da equipe, permitidos pelo enunciado desde que explicados:**

1. **Palavras comuns não pontuam no título.** A tupla `PALAVRAS_IGNORADAS_TITULO` lista palavras como "como", "para", "onde", "quero" e "tenho". Elas têm 4 letras ou mais, mas não dizem nada sobre o assunto. Sem esse ajuste, "Como faço para recarregar o Bilhete Único?" empatava entre "tirar o bilhete" e "recarga" só por causa do "como".
2. **Palavra-chave casa só como palavra inteira.** "tea" (autismo) não casa com "teatro", porque `normalizar()` põe espaço nas pontas.
3. **`normalizar()` foi reforçada.** Além do dicionário `ACENTOS` do enunciado, ela remove acentos fora da lista e troca emoji e reticências por espaço.
4. **Idades viraram palavras-chave.** A busca por regras não interpreta números, então "60 anos" a "64 anos" estão na orientação 2 e "65 anos" a "100 anos" na orientação 1. Assim "meu pai tem 68 anos" encontra a resposta certa.

**Acerto medido:** a pasta `tests/` tem uma bateria de 121 perguntas escritas como um cidadão escreveria, sem acento, com gíria e abreviação.

- Num grupo de 28 perguntas escritas depois do ajuste das palavras-chave, e que não foi usado para escolhê-las, o acerto foi de 22 em 28 (79%). As falhas viraram as palavras-chave do item 4.
- Na categoria de energia, 10 perguntas novas, escritas depois do ajuste, acertaram 8 (80%). As 2 falhas ("carregando" e "tirar carteira") viraram palavras-chave.
- Nas orientações 23 e 24, 6 perguntas novas acertaram só 2 antes do ajuste. Depois do ajuste, "bateria do patinete estragou, onde levo?" ainda não é encontrada: a palavra "estragou" sozinha faria "meu bilhete estragou" cair no descarte de bateria.
- Resultado atual na bateria inteira: 118 de 121 (97,5%).
- O teste exige pelo menos 90% de acerto na bateria inteira.

## Regras de atendimento

- **Navegação:** por categorias numeradas, com "0 para voltar" em todas as telas, inclusive na pergunta "ajudou? (s/n)".
- **Entradas inválidas:** opção fora da faixa, letras, resposta vazia, s/n inválido ou caracteres como "²" nunca encerram o programa. Ctrl+D e Ctrl+C encerram com segurança e salvam o atendimento em andamento.
- **Dados pessoais:** o assistente nunca pede nome, CPF, telefone ou e-mail. Pergunta com 8 ou mais dígitos ou com @ é recusada e não é registrada. Como reforço, também recusa frases como "meu nome é", "me chamo" e "moro na rua".
- **Transparência:** toda resposta mostra a fonte, a data de verificação e o aviso de que o assistente não é canal oficial.
- **Arquivos:** base ausente, corrompida ou fora de UTF-8 não trava o programa. Histórico corrompido é guardado com outro nome (`historico.json.corrompido-...`) em vez de ser apagado.

## Histórico, indicadores e CSV

Cada atendimento é salvo em `data/historico.json` com os campos:

- `data`;
- `sessao`;
- `origem` (pergunta ou categoria);
- `pergunta`;
- `id_orientacao`;
- `encontrou`;
- `ajudou` (sim, não ou não respondeu);
- `tentativas`;
- `tempo_s` (medido com `time.time()` e `round(..., 1)`);
- `nota_facilidade`;
- `perguntas_sem_resultado`, com as formulações que não acharam nada antes da que deu certo.

Ao sair, o assistente pede uma nota de facilidade de 1 a 5 (0 pula) e grava essa nota nos atendimentos da sessão. Se a sessão não teve nenhum atendimento, a nota não é pedida.

**Indicadores (menu 3):**

- resposta encontrada (%);
- taxa de acerto, ou seja, quanto ajudou (%);
- tempo médio para encontrar;
- tentativas por atendimento;
- facilidade de uso (1 a 5);
- lista de dúvidas sem solução;
- perguntas que não foram entendidas na primeira tentativa, que servem de pista para novas palavras-chave.

A exportação para `data/atendimentos.csv` usa `csv.DictWriter`. Ela roda pelo menu 4 e automaticamente ao sair. O arquivo é gravado em UTF-8 com BOM para os acentos abrirem certos no Excel.

## Integrações com outras disciplinas

Todas as disciplinas do grupo na GS 2026.2 usam o mesmo tema, mobilidade urbana.

**Soluções em Energias Renováveis e Sustentáveis:** a categoria "Energia e mobilidade elétrica" (orientações 18 a 24) é a contribuição dessa disciplina dentro do assistente. Ela responde quanto custa carregar bicicleta ou patinete elétrico na tomada, o que muda com a bandeira tarifária, como funcionam os créditos de energia solar em casa, as regras de circulação desses veículos e onde descartar a bateria. A orientação 23 traz o resultado da análise que compara tomada, Tarifa Branca e energia solar, feita no repositório da disciplina: https://github.com/FIAP-GS-02-2026/citizen-assist-ai-energia

## Fontes consultadas

As fontes das orientações 1 a 17 foram acessadas e conferidas em 16/11/2026, e as de energia em 17/11/2026.

**SPTrans, perguntas e respostas:**

- Pessoa idosa 65+: https://www.sptrans.com.br/perguntas-e-respostas/?sobre=bilhete-pessoa-idosa
- 60 a 64 anos: https://www.sptrans.com.br/perguntas-e-respostas/?sobre=gratuidade-60-64
- Pessoa com deficiência: https://www.sptrans.com.br/perguntas-e-respostas/?sobre=bilhete-pcd
- Estudante: https://www.sptrans.com.br/perguntas-e-respostas/?sobre=bilhete-estudante
- Domingos: https://www.sptrans.com.br/perguntas-e-respostas/?sobre=tarifa-zero
- Bilhete Único: https://www.sptrans.com.br/perguntas-e-respostas/?sobre=bilhete-unico
- Atende+: https://www.sptrans.com.br/perguntas-e-respostas/?sobre=atende

**SPTrans, outras páginas:**

- Tarifas: https://www.sptrans.com.br/tarifas/
- Recarga: https://www.sptrans.com.br/compra-de-creditos-e-servicos
- Linhas noturnas: https://www.sptrans.com.br/linhas-noturnas/
- Ouvidoria: https://www.sptrans.com.br/fale-conosco/ouvidoria-sptrans/

**SP156, Prefeitura de São Paulo:**

- Bilhete Especial PcD: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?conteudo=4326
- Gratuidade estudante: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?t=&a=NTgx&conteudo=1325
- Bilhete Único Comum: https://sp156.prefeitura.sp.gov.br/portal/servicos/informacao?t=&a=Nzc4&conteudo=1322
- Canais: https://sp156.prefeitura.sp.gov.br/portal/outros-canais-de-atendimento

**Prefeitura de São Paulo, pessoa com deficiência** (Lei 15.914/2013, desembarque fora do ponto): https://prefeitura.sp.gov.br/web/pessoa_com_deficiencia/w/publicacoes/307915

**Energia e mobilidade elétrica:**

- Tarifa residencial B1 da Enel SP (Resolução Homologatória ANEEL 3.596/2026): https://www.enel.com.br/pt-saopaulo/Para_Voce/tarifa-energia-eletrica.html
- Bandeiras tarifárias, ANEEL: https://www.gov.br/aneel/pt-br/assuntos/tarifas/bandeiras-tarifarias
- Lei 14.300/2022, micro e minigeração distribuída: https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm
- Resolução Contran 996/2023, bicicleta elétrica e autopropelidos: https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-contran/resolucoes/Resolucao9962023.pdf/@@display-file/file
- Lei 12.305/2010, Política Nacional de Resíduos Sólidos (logística reversa de pilhas e baterias): https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/lei/l12305.htm
- Prefeitura de SP, velocidade em ciclovias e calçadas: https://prefeitura.sp.gov.br/w/prefeitura-limita-velocidade-de-bicicletas-el%C3%A9tricas-e-patinetes-a-20-km/h-em-ciclovias

## Teste com usuários

*Em andamento: esta seção será preenchida com os resultados reais do teste. A meta é de pelo menos 3 pessoas de fora da equipe e 10 atendimentos.*

## Limitações

- **Escopo:** cobre o ônibus municipal da cidade de São Paulo e, na categoria de energia, bicicleta e patinete elétrico. Metrô e trem aparecem apenas na integração tarifária.
- **Tarifa de energia:** a orientação 18 mostra a tarifa da tabela da Enel; a página não diz se ela inclui impostos, então o valor final é o da conta de luz.
- **Regras mudam:** cada orientação mostra a data em que foi conferida, e a pessoa deve confirmar no canal oficial.
- **Palavras exatas:** a busca não tolera erro de digitação. "pasagem" pontua menos que "passagem", e "idozo" não encontra nada. A navegação por categorias é a alternativa.
- **Empates:** em empate de pontos vence o menor `id`, e a resposta certa pode aparecer como alternativa.
- **Filtro de dados pessoais:** segue a regra de 8 dígitos. Por isso uma data completa ("10/11/2026") é recusada por precaução. Um endereço sem número e sem as frases da lista não é detectado.
- **Sem tempo real:** não consulta horários nem a posição dos ônibus.

## Vídeo técnico

*O link será adicionado após a gravação.*
