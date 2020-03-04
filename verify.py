import socket
import smtplib
import dns.resolver

### GLOBAL ###
socket.setdefaulttimeout(5)

def get_smtp_hostname(domain):
	smallest_pref_host = (9000, 'temp')
	for answer in dns.resolver.query(domain, 'MX'):
		if (answer.preference < smallest_pref_host[0]):
			smallest_pref_host = (answer.preference, answer.exchange)
	return str(smallest_pref_host[1])

def init_smtp(domain, timeout):

	smtp_hostname = None
	try:
		smtp_hostname = get_smtp_hostname(domain)
	except dns.resolver.NoAnswer as e:
		print("BAD MX:", domain)
		return None
	
	smtp_conn = None
	try:
		smtp_conn = smtplib.SMTP(host=smtp_hostname, timeout=timeout)
	except (
		socket.timeout,
		socket.gaierror,
		smtplib.SMTPConnectError,
		smtplib.SMTPServerDisconnected, 
		ConnectionRefusedError) as e:

		print('BAD DOMAIN CONNECT:', domain)
		return None

	return smtp_conn

def verify_email(domain, email, timeout=5):

	conn = init_smtp(domain, timeout)
	if conn is None:
		return None

	try:
		if (conn.helo()[0]) != 250:
			conn.quit()
			return None
		conn.mail('')
	except smtplib.SMTPServerDisconnected as e:
		print('BAD SMTP HELO:', email)
		return None

	rcpt_status = None
	try:
		rcpt_status = conn.rcpt(email)[0]
	except smtplib.SMTPServerDisconnected as e:
		print('BAD RCPT:', email)
		return None

	try:
		conn.quit()
	except smtplib.SMTPServerDisconnected as e:
		print('BAD QUIT:', email)
		return None

	if rcpt_status == 250:
		return True
	elif rcpt_status == 550:
		return False
	else:
		return None
