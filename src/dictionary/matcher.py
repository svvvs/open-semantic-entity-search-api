import requests
import json
import hashlib
import pysolr
from opensemanticetl import export_solr

#
# Management of dictionaries in Solr schema
#

class Dictionary_Matcher(object):

	solr = 'http://localhost:8983/solr/'
	solr_core = 'core1-dictionary'


	def matches(self, text, dict_ids):

		matches = {}

		hash = hashlib.sha256(text.encode('utf-8'))
		docid=hex_dig = hash.hexdigest()

		solr = export_solr.export_solr(solr = self.solr, core = self.solr_core)

		data = {}
		data['id'] = docid
		data['text_txt'] = text
		
		solr.post(data=data, commit=True)

		headers = {'content-type' : 'application/json'}

		params = {
			'wt': 'json',
			'rows': 0, # we do not need document field results, only the facet
			'facet.limit': -1, # This param indicates the maximum number of constraint counts that should be returned for the facet fields. A negative value means unlimited.
			'facet': 'on',
			'facet.field': dict_ids,
			'fq': 'id:' + docid
		}
		
		r = requests.get(self.solr + self.solr_core + '/select', params=params, headers=headers)
		result = r.json()
		
		for dict_id in dict_ids:
			if dict_id in result['facet_counts']['facet_fields']:
				matches[dict_id] = []
								
				is_value = True
				for value in result['facet_counts']['facet_fields'][dict_id]:
					if is_value:
						matches[dict_id].append(value)
						# next list entry is count
						is_value=False
					else:
						# next list entry is a value
						is_value = True
		
		# delete analyzed and indexed text from dictionary index
		solr = pysolr.Solr(self.solr + self.solr_core)
		result = solr.delete(id=docid)		

		return matches