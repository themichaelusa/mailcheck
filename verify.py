import socket
import smtplib
import dns.resolver

### GLOBALS/CONSTANTS/LAMBDAS ###
socket.setdefaulttimeout(5)

AT_SYMB = '@'
VP_RCPT_CODE = None
get_domain = lambda email: email[email.find(AT_SYMB) + 1:]

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

def verify_email(email, timeout=5):
	domain = get_domain(email)
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

	veri_package = (domain, email, None)
	if rcpt_status == 250:
		veri_package[VP_RCPT_CODE] = True
	elif rcpt_status == 550:
		veri_package[VP_RCPT_CODE] = False

	return veri_package

def bulk_email_verify(emails, to_csv=None, workers=20):
	resp_err, resp_ok = 0, 0
	verified_emails = []

	# verify emails in parallel baby
	with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
	    future_to_smtp = {executor.submit(
	    	verify_email, email): email for url in emails}

	    for future in concurrent.futures.as_completed(future_to_smtp):
	        rcpt_status = future_to_smtp[future]

	        try:
	            data = future.result()
	            print("PARSE DONE")
	        except Exception as exc:
	        	# todo: add loggers here
	            resp_err = resp_err + 1
	        else:
	            resp_ok = resp_ok + 1

	if to_csv is None:
		return verified_emails

if __name__ == '__main__':
	main()




