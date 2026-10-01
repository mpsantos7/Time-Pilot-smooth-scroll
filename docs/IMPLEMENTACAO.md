# Time Pilot: processo de adaptação para scroll fino

Este guia explica as decisões que levaram à versão final v7. Consulte o [README](../README.md) para os requisitos e comandos de construção. Os resultados relatados são verificações realizadas durante o desenvolvimento; esta revisão documental não representa uma nova execução de testes.

## 1. Entender o fundo original

As nuvens são feitas com caracteres de 8 × 8 pixels na SCREEN 2, não com sprites. Há nove fichas de nuvens em RAM, mas somente dois tamanhos de desenho. As instâncias reutilizam os mesmos padrões porque compartilham o deslocamento fino do fundo.

| Elemento | Função |
|---|---|
| Padrão de caractere | Guarda oito linhas de pixels |
| Tabela de nomes | Escolhe o caractere exibido em cada célula |
| Ficha da nuvem | Guarda tipo e posição usados pelo desenho |

O original combina mudanças de célula com padrões deslocados em quatro pixels. A adaptação distribui o movimento em passos de um pixel, conservando quatro passos por ciclo de seis quadros. Scroll fino não significa necessariamente atualizar o fundo em todo quadro. As rotinas de avião, inimigos, tiros e chefes continuam sendo as originais.

## 2. Separar célula e deslocamento fino

Em cada eixo, pense na posição como `8 × célula + deslocamento fino`. A parte fina vai de 0 a 7. Passar de 6 para 7 muda somente os padrões; passar de 7 para 0 também avança uma célula. No sentido negativo, passar de 0 para 7 recua uma célula.

`STEP` calcula essas passagens e guarda a mudança de célula como pendente. `MOVE_CELLS` a aplica quando o desenho preparado é apresentado. Assim, a posição das fichas acompanha a fase de pixels mostrada na tela.

Na tabela de nomes, uma célula à direita corresponde a +1 no endereço; uma linha abaixo corresponde a +32. A área de jogo tem 24 colunas, e as oito restantes pertencem ao marcador. As rotinas tratam a volta horizontal na coluna 23 e a volta vertical da área de jogo.

## 3. Gerar as fases durante a construção

Deslocar pixels durante a partida consumiria tempo do Z80. O gerador calcula antecipadamente oito posições X × oito posições Y: **64 fases**.

Em [tools/build_scroll.py](../tools/build_scroll.py), `make_tables`:

1. Reconstrói os gráficos originais e extrai os pixels das duas nuvens.
2. Desloca os pixels para cada par `(X, Y)`, de `(0, 0)` a `(7, 7)`.
3. Divide o resultado em caracteres e codifica as oito linhas de cada um.
4. Decodifica novamente os dados e compara os pixels com o resultado esperado, detectando cortes e erros nas bordas entre caracteres.

Cada fase usa 15 caracteres para a nuvem grande e nove para a pequena: 24 × 8 = **192 bytes**. As 64 fases ocupam **12.288 bytes** em `9000h–BFFFh`. Há 128 comparações de pixels: duas nuvens × 64 fases. O espaço dos desenhos inclui os pixels que atravessam uma borda de caractere.

Durante a partida, `UPLOAD` calcula o índice `Y × 8 + X`, consulta uma tabela de 64 ponteiros e transfere apenas os 192 bytes necessários.

As fases cabem na ROM adicional, mas não podem ficar todas disponíveis como caracteres na VRAM. A análise da v6 encontrou 927 padrões distintos após deduplicação, incluindo o vazio; cada terço da SCREEN 2 tem apenas 256 índices, compartilhados com o restante do jogo. A solução usa dois grupos pequenos:

| Grupo | Índices | Padrões físicos na VRAM |
|---|---|---|
| A | `22h–39h` (34–57) | `2110h–21CFh` |
| B | `3Ah–51h` (58–81) | `21D0h–228Fh` |

R4 passa de 7 para 4 para compartilhar os padrões em `2000h` entre os três terços. O gerador verifica a igualdade dos bancos originais nas cinco épocas e a compatibilidade das cores usadas. Isso evita enviar os mesmos padrões três vezes.

## 4. Limpar as bordas abandonadas

Nas primeiras versões, fragmentos de nuvens reapareciam. Um nome de caractere pode continuar na tela mesmo quando o padrão está temporariamente vazio. Quando aquele índice recebe novos pixels, eles também aparecem na posição esquecida.

A correção escreve o caractere de céu, `0Ah`, na borda abandonada. É necessário tratar os dois sentidos de cada eixo, as diagonais e as voltas da tela.

`draw_descriptors` prepara nove casos por tamanho, combinando mudanças de célula X e Y em −1, 0 ou +1. Cada descritor reúne o desenho novo e a borda que precisa voltar a ser céu. Uma passagem faz as duas tarefas. `DRAW3` a `DRAW6` escrevem linhas de três a seis caracteres; nas voltas horizontais, dividem a transferência em dois trechos e preservam o marcador.

## 5. Preparar e apresentar em momentos separados

Modificar padrões que o vídeo está lendo pode mostrar parte da nuvem antiga e parte da nova. A v6 resolveu isso com dois grupos de caracteres, mantidos na v7. O grupo oculto é um conjunto de padrões que os nomes das nuvens não referenciam naquele momento; não é uma segunda tela completa.

Suponha que o grupo A esteja em exibição:

```text
Interrupção N
  FINE apresenta um passo anterior, se houver
  O jogo executa a lógica original
  PREPARE calcula o próximo passo
  UPLOAD carrega os padrões no grupo B, oculto
  A mudança de célula é guardada e a troca fica pendente

Interrupção N+1
  FINE aplica a mudança de célula
  DRAW escreve os nomes do grupo B
  B passa a ser exibido; A pode ser reutilizado
  O jogo executa sua lógica e prepara o próximo passo elegível
```

`E80Dh` identifica o grupo preparado, `E80Eh` indica a troca pendente e `E80Fh` identifica o grupo exibido. `PREPARE` não sobrescreve uma preparação pendente. Os estados do jogo também são consultados para evitar passos em momentos inadequados. O título desativa o scroll fino, e o início de vida o reinicializa.

### Por que o topo precisa de prioridade?

A troca dos nomes exige várias escritas no VDP; não acontece inteira em um instante. O vídeo pode alcançar uma nuvem antes de sua tabela de nomes terminar de ser atualizada, mesmo com padrões já preparados.

`FIND_FIRST` escolhe o início da lista cíclica para atender primeiro as nuvens próximas ao topo e as que reaparecem pela volta vertical. A antecipação de quatro linhas de caracteres inclui as bordas a limpar.

O prazo relevante é terminar cada nuvem antes que a varredura alcance suas linhas. Terminar toda a interrupção dentro de um quadro não garante isso. Os perfis verificam os prazos por nuvem: desenhos inferiores podem terminar durante a imagem ativa enquanto o vídeo ainda está acima deles.

## 6. Distribuir os rumos intermediários na v7

O rumo em `E101h` tem 16 direções. O código original arredonda os rumos intermediários alternadamente para duas das oito direções vizinhas. A v6 recebia esse resultado e distribuía quatro passos retos seguidos de quatro diagonais, ou o inverso. A velocidade média era correta, mas a trajetória formava uma escada perceptível.

A v7 lê diretamente as 16 direções em `ARM`. A tabela usa velocidades em meios pixels, com componentes 0, ±1 e ±2. Os rumos pares mantêm os vetores anteriores; os ímpares usam a média dos vizinhos.

`VELOCITY` soma velocidade e resíduo, extrai o deslocamento inteiro com sinal e conserva a fração. Exemplo: velocidade X = +1 representa +0,5 pixel por passo preparado.

| Passo | Resíduo anterior | Soma | Deslocamento X | Novo resíduo |
|---|---:|---:|---:|---:|
| 1 | 0 | 1 | 0 pixel | 1 |
| 2 | 1 | 2 | +1 pixel | 0 |
| 3 | 0 | 1 | 0 pixel | 1 |
| 4 | 1 | 2 | +1 pixel | 0 |

X avança dois pixels distribuídos em quatro passos. Com Y = −2, Y recua um pixel em cada passo, produzindo um rumo intermediário.

No sentido negativo, soma −1 gera deslocamento −1 e resíduo 1; depois, 1 + (−1) gera deslocamento 0 e resíduo 0. A média é −0,5 pixel por passo. Os resíduos ficam em 0 ou 1 e sobrevivem às curvas para não descartar frações acumuladas. `RESET` os zera.

O acumulador trabalha com meios pixels, mas a tela mostra posições inteiras. Não há desenho de meio pixel. A cadência continua sendo quatro passos por ciclo de seis quadros.

## 7. Integrar com o código original

O gerador amplia a ROM de 16 para 32 KB e altera pontos específicos:

| Endereço | Integração | Finalidade |
|---|---|---|
| `4203h` | Salto para `SLOT` em `7F1Eh` | Acessar a segunda página do cartucho |
| `42D1h` | `SNAP` | Executar a carga original e desativar o scroll no título |
| `469Ch` | `RESET` | Inicializar o estado e desenhar a posição inicial |
| `5083h` | `ARM` | Ler o rumo e armar o ciclo |
| `403Dh` | `FINE` | Apresentar o passo no começo da interrupção |
| `40CAh` | `PREPARE` | Preparar depois da lógica do jogo |
| `4D09h` | R4 = 4 | Compartilhar os padrões entre terços |
| `6921h`, `6981h` | Mapas das nuvens | Usar a nova distribuição de caracteres |

As chamadas precisam devolver os valores esperados pelo código que continua: `FINE` carrega A com o conteúdo de `E050h`, `PREPARE` devolve HL = `E380h` e `RESET` devolve HL = `E100h`. Esses efeitos reproduzem as instruções substituídas.

`SLOT` usa `RSLREG`, informações de slots da BIOS e `ENASLT` para selecionar na página 2 o mesmo cartucho da página 1, incluindo subslot quando necessário. Sem essa seleção, o código e as tabelas adicionais podem não estar acessíveis.

O gerador exige a revisão de entrada e confere os bytes anteriores de cada patch. Não aplique esses endereços a outras revisões do jogo. Forneça sua própria ROM de entrada pelo argumento `--input`, com SHA-256:

```text
183e80262301b18d41762d64a2fc326f4a4bef17832109225637e184d54a70d9
```

### Mapa da ROM final v7

| Endereços da CPU | Conteúdo |
|---|---|
| `4000h–7FFFh` | Jogo original com patches e inicialização de slot |
| `8000h–876Ch` | Código novo: 1.901 bytes |
| `876Dh–878Ch` | 16 vetores: 32 bytes |
| `878Dh–880Ch` | 64 ponteiros: 128 bytes |
| A partir de `8C00h` | Descritores e mapas do grupo A |
| A partir de `8E00h` | Descritores e mapas do grupo B |
| `9000h–BFFFh` | Fases de padrões: 12.288 bytes |

Para localizar um endereço da CPU no arquivo ROM, subtraia `4000h`. Por exemplo, `9000h` corresponde ao offset `5000h`.

O estado adicional fica em `E800h–E815h`, acima da RAM original e da pilha, que cresce para baixo. `E812h–E813h` guardam velocidades; `E814h–E815h` guardam resíduos. Os demais campos estão descritos na v6. A construção gera localmente `build/timepilot-fino-v7.build.json`, com endereços e bytes alterados, e `build/timepilot-fino-v7.asm`, com o fonte resolvido. Esses arquivos não integram o Git.

## 8. Reconstruir e verificar

Execute na raiz do repositório, ajustando os caminhos:

```text
python tools/build_scroll.py --input "C:/jogos/timepilot.rom" --disassembly "C:/fontes/TimePilot-disassembly"
```

No Windows também é possível usar `build.bat` com os mesmos argumentos. O projeto exige Python 3.10 ou superior, sem pacotes adicionais. O montador mínimo `tools/z80_assembler.py` monta somente as rotinas novas. A ferramenta externa `tools/graficos.py` deve ser obtida separadamente conforme o README; ela reconstrói os gráficos a partir da ROM fornecida.

A saída padrão é `build/timepilot-fino-v7.rom`, acompanhada pelos arquivos `.build.json` e `.asm`. Use `--output` para outro destino. O gerador verifica a revisão de entrada, os bytes dos patches, os limites de tabelas e os pixels reconstruídos. Não execute Python com `-O`, pois isso desativa verificações feitas com `assert`.

| Verificação | Pergunta respondida |
|---|---|
| Construção e pixels | As duas nuvens foram codificadas corretamente nas 64 fases? |
| Teste lógico no Z80 durante o desenvolvimento | Padrões, nomes, bordas e estado correspondem ao esperado? |
| Teste de cadência durante o desenvolvimento | A trajetória acompanha os vetores, inclusive nas curvas? |
| Perfil de partida durante o desenvolvimento | Acessos à VRAM e prazos por nuvem são respeitados nos cenários executados? |
| Avaliação visual | O movimento parece estável ao jogar? |

Os scripts de emulação e registros utilizados durante o desenvolvimento não integram este repositório. A construção publicada reproduz a ROM v7, mas não executa esses testes de emulação.

Para avaliar visualmente no openMSX, carregue a ROM gerada como Page12. Observe movimentos retos, diagonais e intermediários, curvas frequentes e nuvens cruzando as bordas. Título, início de vida e mudanças de época também são pontos úteis. Esse roteiro não declara que todas as fases já receberam aprovação visual.

## Verificação realizada

A preparação dos gráficos faz 128 comparações de pixels: dois tamanhos de nuvem em 64 posições finas. O empacotamento dos fontes foi validado reconstruindo uma ROM idêntica à v7 testada.

Durante o desenvolvimento, o Z80 emulado passou por 32.768 casos de rumos, resíduos, posições finas, tamanhos, bordas e grupos. Um teste adicional comparou 3.072 quadros de trajetória contínua com a soma das velocidades fracionárias. O erro de quantização ficou limitado a meio pixel.

Foram medidos cenários de rotação e tiros de 30 segundos no Philips VG-8020, C-BIOS MSX1 e Casio MX-10. Nenhuma das 29.772 atualizações completas de nuvens registradas perdeu seu prazo individual de desenho. As novas rotinas não produziram acessos rápidos à VRAM nesses cenários. Essas medições não constituem uma prova para todas as situações de todas as fases.

Os scripts de emulação e os registros de teste não são necessários à build e não integram este repositório. O usuário realizou a avaliação visual e relatou melhora significativa com a v7.

## 9. Resultado e uso

A versão final é uma ROM de 32 KB, Page12, em `4000h–BFFFh`. No openMSX, selecione esse tipo de ROM ao carregá-la. O usuário informou funcionamento com ExecROM e SofaRun. Por isso, a proposta de conversão para `BLOAD"tpilotss.bin",R` foi cancelada; não há BIN nem loader BASIC na implementação final.

Para estudar o gerador, siga: `make_tables` → `ARM`/`VELOCITY` → `STEP` → `UPLOAD` → `FINE`/`DRAW` → `draw_descriptors` → `build`. Essa ordem acompanha os dados, o movimento, a apresentação e a montagem dos patches.

## Referência e distribuição

O projeto de referência é o [TimePilot-disassembly, de antxiko](https://github.com/antxiko/TimePilot-disassembly). A ferramenta externa permanece sujeita à licença daquele projeto. Este repositório distribui os fontes da modificação e a documentação; ROMs, gráficos extraídos, disassembly e resultados gerados ficam fora do Git. Consulte o README para a atribuição completa.
