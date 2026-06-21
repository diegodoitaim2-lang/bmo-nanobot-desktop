import sys

def print_board(board):
    for row in board:
        print(' | '.join(row))
        print('-' * 5)

def check_winner(board, player):
    # rows, columns, diagonals
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
        if all(board[j][i] == player for j in range(3)):
            return True
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    return False

def is_full(board):
    return all(cell != ' ' for row in board for cell in row)

def main():
    board = [[' ' for _ in range(3)] for _ in range(3)]
    current = 'X'
    while True:
        print('\nTabuleiro:')
        print_board(board)
        try:
            move = input(f"Jogador {current}, escolha linha e coluna (ex: 1 2): ")
            row, col = map(int, move.split())
        except Exception:
            print('Entrada inválida. Tente novamente.')
            continue
        if not (1 <= row <= 3 and 1 <= col <= 3):
            print('Posição fora do intervalo. Use 1 a 3.')
            continue
        if board[row-1][col-1] != ' ':
            print('Casa já ocupada. Escolha outra.')
            continue
        board[row-1][col-1] = current
        if check_winner(board, current):
            print_board(board)
            print(f'Parabéns! Jogador {current} venceu!')
            break
        if is_full(board):
            print_board(board)
            print('Empate!')
            break
        current = 'O' if current == 'X' else 'X'

if __name__ == '__main__':
    main()
