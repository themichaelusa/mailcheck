
### STDLIB ###
import smtplib
import concurrent.futures as cf
from multiprocessing import cpu_count
import os.path

### EXTERNAL IMPORTS ###
import dns.resolver

class Verify:
	def __init__(self):
		self.SMTP_CONN_DICT = {}
		self.executor = cf.ThreadPoolExecutor(max_workers=cpu_count())
		self.__parallel_init_smtp(common_domains)
		self.at_sym = '@'

	def __call__(self, emails):
		emails = list(emails)
		if len(emails) <= 1:
			self.verify_email(emails[0])
		else:
			self.verify_emails(emails)

	# THREAD POOL FUNCS
	def __generic_parallel_exec(self, func, map_list):
		return_vals = []
		with self.executor as ex:
			outputs = [ex.submit(func, arg) for arg in map_list]
			for future in cf.as_completed(outputs):
				try:
					return_vals.append(future.result())
				except Exception as e:
					print("EXCEPTION: ", e)

		return return_vals
	
	# SMTP INIT
	def __init_smtp(self, domain, timeout=2):
		if domain not in SMTP_CONN_DICT.keys():
			smtp_hostname = self.__get_smtp_hostname(domain)
			SMTP_CONN_DICT[domain] = smtplib.SMTP(host=smtp_hostname, timeout=timeout)
	
	def __parallel_init_smtp(self, domains):
		self.__generic_parallel_exec(self.__init_smtp, domains)

	# MISC PRIVATE HELPERS
	def __get_smtp_hostname(self, domain):
		smallest_pref_host = (9000, 'temp')
		for answer in dns.resolver.query(domain, 'MX'):
			if (answer.preference < smallest_pref_host[0]):
				smallest_pref_host = (answer.preference, answer.exchange)
		return str(smallest_pref_host[1])

	def __add_unknown_domains_from_path(self, path):
		all_domains = []
		with open(path, 'r') as file:
			lines = (line for line in file.readlines())
			for line in lines:
				domain = email[email.find(self.at_sym) + 1:]
				all_domains.append(domain)

		self.__parallel_init_smtp(list(set(all_domains)))

    # USER METHODS
	def verify_email(self, email):
		domain = email[email.find(self.at_sym) + 1:]
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

	def verify_emails(self, emails, cache_domains=True):
		# if is path, get addresses, exec in parallel
		addresses = emails
		if os.path.isfile(emails):
			if cache_domains: 
				self.__add_unknown_domains_from_path(emails)
			with open(emails, 'r') as file:
				addresses = [line for line in file.readlines()]

		return self.__generic_parallel_exec(self.verify_email, addresses)

