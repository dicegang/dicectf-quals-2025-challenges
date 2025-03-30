import { Chess } from 'chess.js'
import { ParsedMail, simpleParser, } from 'mailparser'
import { SMTPServerDataStream, SMTPServerSession } from 'smtp-server'
import { SMTPServer } from './smtp-server'
import { adminCert, adminKey, generateUser, sign, verify } from './cert'

const parse = async (raw: Buffer) => {
	try {
		return await simpleParser(raw);
	} catch(e) {
		throw new Error('invalid email!');
	}
}

const parseAndVerify = async(raw: Buffer) => {
	return await parse(await verify(raw));
}

const extractMoves = async (message: ParsedMail, moves: string[] = []): Promise<string[]> => {
	if (moves.length > 10) {
		throw new Error('chain too long!');
	}
	if (!message.text) {
		throw new Error('invalid chain!');
	}
	const previous = message.attachments[0];
	if (!previous) {
		return [message.text.trim(), ...moves];
	}
	const parsed = await parse(previous.content);
	if (!(moves.length % 2) && parsed.from?.text !== 'admin@chess') {
		throw new Error('invalid chain!');
	}
	return extractMoves(await parseAndVerify(previous.content), [message.text.trim(), ...moves]);
}

const play = async (raw: Buffer, recipient: string) => {
	const moves = await extractMoves(await parseAndVerify(raw));
	const game = new Chess();

	for (const move of moves) {
		try {
			game.move(move, { strict: true });
		} catch(e) {
			throw new Error('invalid move!');
		}

		if (game.isGameOver()) {
			if (game.isCheckmate()) {
				if (game.turn() == 'b') return process.env.FLAG ?? 'dice{flag}';
				else return `${game.ascii()}\n\nloss`;
			} else {
				return `${game.ascii()}\n\ndraw`;
			}
		}
	}

	const move = await (await fetch('http://stockfish:8000/next', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ board: game.fen() })
	})).json()

	game.move(move);

	const response = await sign({
		to: recipient,
		from: 'admin@chess',
		text: move,
		attachments: [{ filename: 'previous', content: raw }]
	}, adminCert, adminKey);

	return `${game.ascii()}\n\n${response.toString('base64').match(/(.{1,80})/g)?.join('\n')}`;
}

const register = async (username: string): Promise<string> => {
	if (username === 'admin@chess' || !/^[a-z]{8,16}@chess$/.test(username)) {
		throw new Error('invalid username!')
	}

	const { key, cert } = await generateUser(username);

	return `${key}\n\n${cert}`;
}

const recv = async (stream: SMTPServerDataStream, session: SMTPServerSession): Promise<string> => {
	let parts: Buffer[] = [];
	for await (const part of stream) {
		parts.push(part);
	}
	if (stream.sizeExceeded) {
		throw new Error('max size exceeded!');
	}

	const raw = Buffer.concat(parts);
	const message = await parse(raw);
	if (!message.from || !message?.to || Array.isArray(message.to)) throw new Error('invalid email');

	const to = message.to.text;
	const from = message.from.text;

	if (to == 'admin@chess') {
		return await play(raw, from);
	} else if (to == 'register@chess') {
		return await register(from);
	}

	throw new Error('user not found!');
}

new SMTPServer({
	name: 'bad-chess-challenge',
	size: 3 * 10 ** 5,
	authOptional: true,
	onData: (stream: SMTPServerDataStream, session: SMTPServerSession, callback: (err?: Error | null | undefined, message?: string[]) => void) => {
		recv(stream, session).then((res: string) => {
			callback(null, res.replace(/\r\n/g, '\n').split('\n'));
		}).catch((err: Error) => {
			callback(err);
		});
	},
}).listen(2525).on('listening', () => {
	console.log('listening');
});