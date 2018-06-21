import smtplib
import dns.resolver

### GLOBAL ###
SMTP_CONN_DICT = {}

def get_smtp_hostname(domain):
	smallest_pref_host = (9000, 'temp')
	for answer in dns.resolver.query(domain, 'MX'):
		if (answer.preference < smallest_pref_host[0]):
			smallest_pref_host = (answer.preference, answer.exchange)
	return str(smallest_pref_host[1])

def init_smtp(domain, timeout=2):
	if domain not in SMTP_CONN_DICT.keys():
		smtp_hostname = get_smtp_hostname(domain)
		SMTP_CONN_DICT[domain] = smtplib.SMTP(host=smtp_hostname, timeout=timeout)

def verify_email(domain, email):
	conn = SMTP_CONN_DICT[domain]

	if (conn.helo()[0]) != 250:
		conn.quit()
		return False

	conn.mail('')
	rcpt_status = conn.rcpt(email)[0]
	conn.quit()

	if rcpt_status == 250:
		return True
	elif rcpt_status == 550:
		return False
	else:
		return None

if __name__ == '__main__':
	init_smtp('gmail.com')
	print(verify_email('gmail.com', 'musachenko@gmail.com'))
