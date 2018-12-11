from collections import OrderedDict
import itertools
from pprint import pprint

class invertedIndex:
    def __init__(self, texts, id_field='_id', preprocessed_field='text_pre_processed_v3', preprocess_with_start_end=True):
        '''

        :param texts: as array with dicts inside with keys/fields like: id, raw text, preprocessed text
        :param id_field: name of id_field (unique id)
        :param preprocessed_field: name of field with preprocessed text
        :param preprocess_with_start_end: if true: preprocess in list with (start, end, token), otherwise just list with tokens
        '''
        self.texts = texts
        self.id_field = id_field
        self.preprocessed_field = preprocessed_field
        self.preprocess_with_start_end = preprocess_with_start_end
        self.uniqueWords = self.getUniqueWords()
        self.index = self.computeInverseIndex()

    def getUniqueWords(self):
        #return sorted(set(word[2] for report in police_reports for word in report['text_pre_processed_v3']))
        return sorted(set(word[2] if self.preprocess_with_start_end else word for text in self.texts for word in text[self.preprocessed_field]))

    def computeInverseIndex(self):
        if self.preprocess_with_start_end:
            return {word:set((str(text[self.id_field]), token[0], token[1])
                             for text in self.texts
                             for token in text[self.preprocessed_field]
                             if token[2] == word
                             )
                    for word in self.uniqueWords}
        else:
            return {word:set((str(text[self.id_field]), index)
                             for text in self.texts
                             for index, token in enumerate(text[self.preprocessed_field])
                             if token == word
                             )
                    for word in self.uniqueWords}

    def fullTextSearch(self, searchTokenList):
        '''
        search in index
        :param searchTokenList: list with lemmatized tokens
        :return:
        '''
        searchResults = {}
        #angenommen suche nach ['test']
        for i, word in enumerate(searchTokenList):
            #check if 'test' ist in index enthalten
            if word in self.index:
                # loop durch alle dokumente die 'test' enthalten
                for occurence in self.index[word]:
                    # occurence[0] entspricht text-id
                    # prüfen, ob jeweiliges dokument, das 'test' enthält schon im ergebnis enthalten
                    if occurence[0] in searchResults:
                        searchResults[occurence[0]]['occurences_count'] += 1

                        # prüfen, ob das jeweilige wort schon einen eintrag für 'test' in ergebnis hat
                        # wichtig für dokumente, in denen 'test' mehrmals vorkommt
                        if i in searchResults[occurence[0]]['occurences']:
                            searchResults[occurence[0]]['occurences'][i].append((occurence[1], occurence[2]))
                        else:
                            searchResults[occurence[0]]['occurences'][i] = [(occurence[1], occurence[2])]
                    else:
                        #searchResults[occurence[0]] = [(occurence[1], occurence[2])]
                        searchResults[occurence[0]] = {
                            'occurences': {
                                i: [(occurence[1], occurence[2])]
                            }
                        }
                        searchResults[occurence[0]]['occurences_count'] = 1

        for doc, res in searchResults.items():
            if len(res['occurences']) > 1:
                res['min_dist'] = self.__computeMinWordDistance(res['occurences'])


        #return searchResults

        #orderec dict sorted by occurences of search terms
        return OrderedDict(sorted(searchResults.items(), key=lambda t: t[1]['occurences_count'], reverse=True))


    def __computeMinWordDistance(self, occurences):
        '''

        :param occurences: like: {
        #     0: ['null1', 'null2', 'null3'],
        #     1: ['eins1', 'eins2']
        # }
        :return: minimum distance of possible word combinations in text
        '''
        # test = {
        #     0: ['null1', 'null2', 'null3'],
        #     1: ['eins1', 'eins2']
        # }
        # -> [['null1', 'null2', 'null3'], ['eins1', 'eins2']]
        flattened_occurences = list(occ for key, occ in sorted(occurences.items()))
        # --> [('null1', 'eins1'),
        #  ('null1', 'eins2'),
        #  ('null2', 'eins1'),
        #  ('null2', 'eins2'),
        #  ('null3', 'eins1'),
        #  ('null3', 'eins2')]
        possible_combinations = list(itertools.product(*flattened_occurences))
        #pprint(possible_combinations)

        distances = []

        for combination in possible_combinations:
            #print(combination)
            dist = 0
            last_end = 0
            counter = 0
            # loop through specific word_combination
            for position in combination:
                # calc distance for 2 words if second word is after first word
                if counter > 0 and last_end <= position[0]:
                    dist += (position[0] - last_end)

                last_end = position[1]
                counter += 1
            if dist != 0:
                distances.append(dist)
        #print(distances)

        return min(distances)