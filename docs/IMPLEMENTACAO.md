# Implementação do scroll fino v7

## Build e entrada

O gerador verifica o SHA-256 da ROM original e os bytes esperados nos pontos de alteração. O montador em `tools/z80_assembler.py` converte apenas as novas rotinas incluídas no gerador. Ele não contém o disassembly do jogo.

O módulo externo `tools/graficos.py`, do [TimePilot-disassembly](https://github.com/antxiko/TimePilot-disassembly), reconstrói a VRAM a partir da ROM fornecida pelo usuário. O gerador extrai dessa reconstrução os pixels das nuvens e prepara 64 combinações de deslocamento X/Y (0 a 7 pixels por eixo).

Cada combinação contém 24 padrões de oito bytes: 15 para a nuvem grande e nove para a pequena. As 64 combinações ocupam 12.288 bytes na extensão da ROM. Nenhuma imagem original ou tabela de pixels pré-calculada é incluída no repositório.

## Preparação e apresentação

Dois grupos de 24 caracteres compartilham o intervalo originalmente reservado às nuvens:

| Grupo | Nomes | Padrões na VRAM |
|---|---|---|
| A | 34–57 | 2110–21CF |
| B | 58–81 | 21D0–228F |

PREPARE, ao final da interrupção, envia os padrões para o grupo oculto. FINE, no início da interrupção seguinte, atualiza as posições grossas e a tabela de nomes para apresentar esse grupo.

O desenho começa pelas nuvens próximas ao topo, incluindo as que atravessam a borda inferior. Cada transição de célula desenha a nova nuvem e apaga sua borda de saída no mesmo retângulo. Isso evita tanto os resíduos de nuvens quanto a atualização de padrões ainda visíveis.

O registrador R4 do VDP é configurado para compartilhar a tabela de padrões entre os três terços da tela. A build verifica que os padrões originais desses terços coincidem nas cinco épocas e que a faixa de cores usada pelas nuvens é uniforme.

## Dezesseis rumos

O rumo original de 16 posições está em E101. A versão anterior recebia o rumo já arredondado para oito posições e dividia cada movimento em quatro passos. Nos rumos intermediários, isso alternava quatro passos retos com quatro diagonais, formando uma escada visível.

ARM agora lê E101 diretamente. A tabela usa componentes 0, ±1 e ±2 em unidades de meio pixel. VELOCITY acumula essas frações e fornece a STEP deslocamentos inteiros de no máximo um pixel por eixo. Os resíduos são conservados entre mudanças de rumo e zerados ao iniciar a vida.

O eixo menor dos rumos intermediários passa a avançar em passos alternados. A velocidade média corresponde à média dos dois rumos vizinhos do jogo original; não foi adotada uma nova tabela trigonométrica. Permanecem quatro passos por ciclo de seis quadros.

## Memória

| Região | Uso |
|---|---|
| 4000–7FFF | ROM original com alterações pontuais |
| 7F1E–7F44 | Inicialização do slot da segunda página |
| 8000–880C | Novas rotinas, vetores e ponteiros |
| 8C00–8DC3 | Descritores de desenho do grupo A |
| 8E00–8FC3 | Descritores de desenho do grupo B |
| 9000–BFFF | 64 conjuntos de padrões |
| E800–E811 | Posição fina, cadência, grupos e dados de desenho |
| E812–E813 | Velocidades em meios pixels |
| E814–E815 | Resíduos fracionários de X/Y |

A ROM resultante ocupa as páginas 1 e 2, sem mapper bancado. A build preserva o restante da ROM de entrada. Os endereços exatos das rotinas novas e os pontos alterados ficam no relatório gerado localmente.

## Verificação realizada

A preparação dos gráficos faz 128 comparações de pixels: dois tamanhos de nuvem em 64 posições finas. O empacotamento dos fontes foi validado reconstruindo uma ROM idêntica à v7 testada.

Durante o desenvolvimento, o Z80 emulado passou por 32.768 casos de rumos, resíduos, posições finas, tamanhos, bordas e grupos. Um teste adicional comparou 3.072 quadros de trajetória contínua com a soma das velocidades fracionárias. O erro de quantização ficou limitado a meio pixel.

Foram medidos cenários de rotação e tiros de 30 segundos no Philips VG-8020, C-BIOS MSX1 e Casio MX-10. Nenhuma das 29.772 atualizações completas de nuvens registradas perdeu seu prazo individual de desenho. As novas rotinas não produziram acessos rápidos à VRAM nesses cenários. Essas medições não constituem uma prova para todas as situações de todas as fases.

Os scripts de emulação e os registros de teste não são necessários à build e não integram este repositório. O usuário realizou a avaliação visual e relatou melhora significativa com a v7.
