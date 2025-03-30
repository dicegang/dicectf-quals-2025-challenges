from flask import Flask, request, jsonify
from stockfish import Stockfish

app = Flask('stockfish')

@app.post('/next')
def next():
	if not request.json or 'board' not in request.json:
		return jsonify('no move?')

	game = Stockfish('./stockfish-ubuntu-x86-64-avx2', parameters={'Threads': 4}, depth=15)
	game.set_fen_position(request.json['board'])

	return jsonify(game.get_best_move_time(2000))