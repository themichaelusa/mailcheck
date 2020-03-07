import json
from verify import bulk_email_verify

def import_test_set(path):
	test_set = None
	with open(path) as tset:
		test_set = json.load(tset)

	parsed_tset = []
	for addrs in test_set.values():
		for addr in addrs:
			parsed_tset.append(addr[0])

	return parsed_tset

def test_bulk(path):
	tset = import_test_set(path)
	return bulk_email_verify(tset)

if __name__ == '__main__':
	test_bulk('vemails.json')
