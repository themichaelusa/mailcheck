### IMPORTS ###
import socket
import smtplib
import dns.resolver
import concurrent.futures
from multiprocessing import cpu_count

### GLOBALS/CONSTANTS/LAMBDAS ###
socket.setdefaulttimeout(5)

AT_SYMB = '@'
VP_RCPT_CODE = 2
DEFAULT_WORKER_N = 5*cpu_count()
get_domain = lambda email: email[email.find(AT_SYMB) + 1:]

### FUNCTIONS ###
def fmt_veri_package(vp, error, data):
	vp['error'] = error
	vp['data'] = data
	return vp 

def get_smtp_hostname(domain):
	smallest_pref_host = (9000, 'temp')
	for answer in dns.resolver.query(domain, 'MX'):
		if (answer.preference < smallest_pref_host[0]):
			smallest_pref_host = (answer.preference, answer.exchange)
	return str(smallest_pref_host[1])

def init_smtp(domain, timeout):
	conn_dict = {'error': False, 'conn': None, 'data': None}

	smtp_hostname = None
	try:
		smtp_hostname = get_smtp_hostname(domain)
	except dns.resolver.NoAnswer as e:
		# print("BAD MX:", domain)
		return fmt_veri_package(conn_dict,
		error=True,
		data=('BAD MX', domain, str(e)))
	
	smtp_conn = None
	try:
		smtp_conn = smtplib.SMTP(host=smtp_hostname, timeout=timeout)
	except (
		socket.timeout,
		socket.gaierror,
		smtplib.SMTPConnectError,
		smtplib.SMTPServerDisconnected, 
		ConnectionRefusedError) as e:

		# print('BAD DOMAIN CONNECT:', domain)
		return fmt_veri_package(conn_dict,
		error=True,
		data=('BAD DOMAIN CONNECT', domain, str(e)))

	conn_dict['conn'] = smtp_conn
	return conn_dict

def verify_email(email, timeout=5):
	domain = get_domain(email)
	conn_dict = init_smtp(domain, timeout)
	veri_package = {'error': False, 'data': None}

	if conn_dict['error']:
		return conn_dict
	conn = conn_dict['conn']

	### send HELO call to SMTP conn
	try:
		if (conn.helo()[0]) != 250:
			conn.quit()
			return fmt_veri_package(veri_package,
			error=True, 
			data=('BAD SMTP HELO', email, None))

		conn.mail('')
	except smtplib.SMTPServerDisconnected as e:
		#print('BAD SMTP HELO:', email)
		return fmt_veri_package(veri_package, 
			error=True, 
			data=('BAD SMTP HELO', email, str(e)))

	### send RCPT command to SMTP server to see if email exists
	rcpt_status = None
	try:
		rcpt_status = conn.rcpt(email)[0]
	except smtplib.SMTPServerDisconnected as e:
		#print('BAD RCPT:', email)
		return fmt_veri_package(veri_package,
		error=True, 
		data=('BAD RCPT', email, str(e)))

	### kill SMTP conn to free up ports
	try:
		conn.quit()
	except smtplib.SMTPServerDisconnected as e:
		#print('BAD QUIT:', email)
		return fmt_veri_package(veri_package,
		error=True, 
		data=('BAD QUIT', email, str(e)))

	### check RCPT status codes to verify email is valid
	veri_data = [domain, email, None]
	if rcpt_status == 250:
		veri_data[VP_RCPT_CODE] = True
	elif rcpt_status == [550, 450, 421]:
		veri_data[VP_RCPT_CODE] = False

	veri_package['data'] = tuple(veri_data)
	return veri_package

def bulk_email_verify(emails, to_csv=None, workers=DEFAULT_WORKER_N):
	resp_err, resp_ok = 0, 0
	verified_emails = []

	# verify emails conncurrently
	with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
	    future_to_smtp = {executor.submit(
	    	verify_email, email): email for email in emails}

	    for future in concurrent.futures.as_completed(future_to_smtp):
	        rcpt_status = future_to_smtp[future]

	        try:
	            data = future.result()
	            print("PARSE DONE: {}".format(data))
	            verified_emails.append(data)
	        except Exception as exc:
	        	# todo: add loggers here
	            resp_err = resp_err + 1
	        else:
	            resp_ok = resp_ok + 1

	if to_csv is None:
		return verified_emails


