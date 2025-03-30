import smime from 'nodemailer-smime-plus'
import Mail from 'nodemailer/lib/mailer';
import { $ } from 'bun'
import { promisify } from 'node:util';
import { createTransport } from 'nodemailer'

export const generateUser = async (commonName: string) => {
	const {stdout: key} = await $`openssl genrsa 2048`.quiet();
	// why bun is so fucked i have no idea, but i can't use bun shell for this...
	const subject = `/CN=${commonName}/C=US/ST=NY/L=New York/O=bad-chess-challenge`
	const proc = Bun.spawn(['openssl', 'req', '-nodes', '-new', '-key', '/dev/stdin', '-subj', subject], { stdin: Buffer.from(key) });
	const csr = await new Response(proc.stdout).arrayBuffer();
	const {stdout: cert} = await $`openssl x509 -req -in - -days 365 -CA ca.pem -CAkey priv.pem < ${csr}`.quiet();
	return { key: key.toString().trim(), cert: cert.toString().trim() }
}

export const verify = async (raw: Buffer): Promise<Buffer> => {
	try {
		const { stdout, stderr } = await $`openssl cms -verify -in - -CAfile ca.pem < ${Buffer.from(raw.toString() + '\n')}`.quiet();
		if (stderr.toString().trim() !== 'CMS Verification successful') {
			throw new Error('unsigned email!')
		}
		return stdout;
	} catch(e) {
		throw new Error('unsigned email!');
	}
}

export const sign = async (email: Mail.Options, cert: string, key: string): Promise<Buffer> => {
	const transport = createTransport({ streamTransport: true, buffer: true });
	transport.use('stream', smime({ cert, key, chain: [] }));
	const { message } = await promisify(transport.sendMail.bind(transport))(email);
	transport.close();
	return message;
}

export const { key: adminKey, cert: adminCert } = await generateUser('admin@chess');