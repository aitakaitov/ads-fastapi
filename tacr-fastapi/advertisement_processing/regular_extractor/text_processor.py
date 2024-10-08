import os
from typing import Tuple
from perscache import Cache
import xml.etree.ElementTree as ET
import requests
import conllu
import json
from dataclasses import dataclass
import re
LEMMATIZED_FOLDER="RegularExtractor/lemmatized"

H_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

@dataclass
class NamedEntity:
    type: str
    start_index: int
    end_index: int
    tokens: list
    text: str

    def __str__(self):
        return f"{self.type}: {self.text}"

class TextProcessor:
    cache = Cache()

    def __init__(self, filename):
        self.filename = filename
        self.hierarchical_tokens = []
        self.flattened_tokens = []
        self.named_entities = []
        self.parsed_conllu = None
        self.sent_ids_for_tokens = []


    @cache
    @staticmethod
    def process_text(tokenizer, tagger, parser, output, data):
        url = 'http://lindat.mff.cuni.cz/services/udpipe/api/process'
        payload = {
            'tokenizer': tokenizer,
            'input': 'generic_tokenizer',
            'tagger': tagger,
            'parser': parser,
            'output': output,
            'data': data
        }
        response = requests.post(url, data=payload)
        return response.text

    @cache
    @staticmethod
    def recognize_entities(conllu_input):
        url = 'http://lindat.mff.cuni.cz/services/nametag/api/recognize'
        payload = {
            'data': conllu_input,
            'input': "conllu",
            'output': "conllu-ne",
        }
        response = requests.post(url, data=payload)
        return response.text

    @staticmethod
    def _add_text_index(parsed_tags):
        text_index = 0
        for tag in parsed_tags:
            for sentence in tag["parsed_text"]:    
                for token in sentence:
                    token['text_index'] = text_index
                    text_index += 1

    @staticmethod
    def _conllu_to_text(flattened_tokens):
        text = ''
        for token in flattened_tokens:

            # if token['form'] == 'Elektrická':
            #     pass
            
            space = ' '

            if 'misc' in token and token['misc'] is not None:
                if 'SpaceAfter' in token['misc'] and token['misc']['SpaceAfter'] == 'No':
                    space = ''
                elif 'SpacesAfter' in token['misc'] and token['misc']['SpacesAfter'] is not None:
                    space = token['misc']['SpacesAfter']
                    space = space.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r').replace('\\s', '')
            
            text += token['form'] + space
        return text
    

    def _extract_named_entities(self):
        named_entities = {}
        
        for idx, token in enumerate(self.flattened_tokens):
            if 'misc' in token and token['misc'] and 'NE' in token['misc']:
                entity = token['misc']['NE']
                entities = entity.split('-')
                for entity in entities:
                    entity_tuple = tuple(entity.split('_'))+(self.tag_ids_for_tokens[idx],)
                    named_entity = named_entities.get(entity_tuple)
                    if named_entity:
                        named_entity.end_index = idx
                        named_entity.tokens.append(token)
                        if 'misc' in token and token['misc'] and 'SpaceAfter' in token['misc'] and token['misc']['SpaceAfter'] == 'No':
                            space = ''
                        else:
                            space = ' '
                        
                        named_entity.text += token['form'] + space
                    else:
                        named_entities[entity_tuple] = NamedEntity(
                            type=entity_tuple[0],
                            start_index=idx,
                            end_index=idx,
                            tokens=[token],
                            text=token['form'] + ' ' if ('misc' not in token or 'SpaceAfter' not in token['misc'] or token['misc']['SpaceAfter'] != 'No') else token['form']
                        )

        self.named_entities = list(named_entities.values())
    
    # # found : list[start,len]
    # def find_time(self, found):
    #     times = []
        
    #     for start,end in found:
    #         for tok in self.flattened_tokens[start[0]:end[0]]:
    #             print(tok['form'])    
    #             if tok['misc'] is not None:
    #                 print(self.flattened_tokens[start[0]]['misc'])    
    #                 if 'NE' in tok['misc']:
    #                     ner = tok['misc']
    #                     print(ner, tok['form'])      
    #     return times 

    def _recognize_entities(self, text: str):
        json_output = TextProcessor.process_text(tokenizer=None, tagger="data", parser=None, output="conllu", data=text)
        parsed_output = json.loads(json_output)
        json_output = TextProcessor.recognize_entities(parsed_output['result'])
        parsed_output = json.loads(json_output)
        parsed_conllu = conllu.parse(parsed_output['result'])
        return parsed_conllu
        

    def process(self, texts:list[dict[str, object]]):
        parsed_tags = [{"id": text['id'], "text": text['text'], "parsed_text": self._recognize_entities(text['text']), "tag": text['tag']} for text in texts]

        self._add_text_index(parsed_tags)

        self.hierarchical_tokens = parsed_tags

        # flatened =  [token for tag in parsed_tags for sentence in tag["parsed_text"] for token in sentence]

        token_index = 0
        sentence_index = 0
        tag_index = 0
        self.flattened_tokens = []
        self.flattened_sentences = []
        self.sent_ids_for_tokens = []
        self.tag_ids_for_tokens = []
        for tag in parsed_tags:
            for sentence in tag["parsed_text"]:
                self.flattened_sentences.append(sentence)
                for token in sentence:
                    self.flattened_tokens.append(token)
                    self.sent_ids_for_tokens.append(sentence_index)
                    self.tag_ids_for_tokens.append(tag_index)
                    token_index += 1
                sentence_index += 1
            tag_index += 1


        assert all([i == token["text_index"] for i, token in enumerate(self.flattened_tokens)])

        self.heading_ranges = [tag['parsed_text'][0][0]['text_index'] for tag in self.hierarchical_tokens if (len(tag['parsed_text']) > 0) and len(tag['parsed_text'][0]) > 0 and (tag['tag'] in H_TAGS)] + [len(self.flattened_tokens)-1]

        if self.heading_ranges[0] != 0:
            self.heading_ranges = [0] + self.heading_ranges

        self._extract_named_entities()

    def get_tokens_with_tags(self, flattened_tokens):
        return [(token['form'], self.tag_ids_for_tokens[token["text_index"]]) for token in flattened_tokens]

    def get_heading_for_token(self, token_index: int):
        """
        Returns the heading for the given token index.
        :param token_index: The index of the token to get the heading for.
        """
        for heading_index in range(len(self.heading_ranges) - 1):
            if self.heading_ranges[heading_index] <= token_index < self.heading_ranges[heading_index + 1]:
                return (self.heading_ranges[heading_index], self.heading_ranges[heading_index + 1])
        return None

    def write_lemmatized_text(self):
            lematized_text  = ''
            for token in self.flattened_tokens:
                lema = token['lemma']
                lematized_text += lema + ' '
            
            filebase = os.path.basename(self.filename)
            with open(os.path.join(LEMMATIZED_FOLDER,filebase), 'w+', encoding="utf8") as file:
                file.write(lematized_text)

    def find_start_indices(self, lemma_seq:list[str]):
        """
            Finds the indices of the first token of the given lemma sequence.
            :param lemma_seq: The sequence of lemmas to find.

            :returns: A list of indices of the first token of the given lemma sequence.
        """
        start_indices = []
        for i in range(len(self.flattened_tokens) - len(lemma_seq)):
            if self.flattened_tokens[i]['lemma'] == lemma_seq[0]:
                if all(self.flattened_tokens[i+j]['lemma'] == lemma_seq[j] for j in range(1, len(lemma_seq))):
                    start_indices.append(i)
        return start_indices

    def _check_lemma_sequence(self, start_index: int, lemma_list: list[str]) -> Tuple[bool,int]:
        i = 0
        end_index = 0
        while i < len(lemma_list):
            lemma = lemma_list[i]
            if lemma.startswith('*'):
                num_arbitrary_tokens = int(lemma[1:])

                j = 0
                while self.flattened_tokens[start_index + i + j]['lemma'] != lemma_list[i+1]:
                    j += 1
                    if j > num_arbitrary_tokens:
                        return False,-1
                    
                    if start_index + i + j >= len(self.flattened_tokens):
                        return False,-1
                end_index = start_index + i + j
                start_index += j - 1

            elif self.flattened_tokens[start_index + i]['lemma'] != lemma:
                return False,-1
            i += 1

            if start_index + i >= len(self.flattened_tokens):
                return False,-1
        
        return True, end_index
    
    def _check_lemma_in_sentence(self, start_index: int, lemma_list: list[str]) -> Tuple[bool,int]:
        i = 0
        end_index = 0
        while i < len(lemma_list):
            lemma = lemma_list[i]
            if self.flattened_tokens[start_index + i]['lemma'] != lemma and i==0:
                return False,-1
            
            j=0
            while self.flattened_tokens[start_index + i + j]['lemma'] != lemma_list[i]:
                j += 1
                if start_index + i + j >= len(self.flattened_tokens):
                    return False,-1
                if self.flattened_tokens[start_index + i + j]['lemma'] ==".":   # todo end of sentence or max len
                    return False,-1
                
                if start_index + i + j >= len(self.flattened_tokens):
                    return False,-1
            end_index = start_index + i + j
            start_index += j - 1

            
            i += 1

            if start_index + i >= len(self.flattened_tokens):
                return False,-1
        
        return True, end_index
    
    def start_end_from_sentence(self, sent_id):
        start = self.flattened_tokens.index(self.flattened_sentences[sent_id][0])
        end = self.flattened_tokens.index(self.flattened_sentences[sent_id][-1])
        return start,end


    def _remove_empty(self, found):
        return [f for f in found if f[0] != []]


    def extract_time(self,sentences):
        times = []
        for sent in sentences:
            # print(sent)
            s,e = sent["range"]
            
            regs =[["doba", "*1","léta"]]
            regs =[["po", "doba", "*1","léta"]]
            found = self.find_all_reg(regs,s,e)
            for s,e in zip(found[0],found[1]):
                
                text = self._conllu_to_text(self.flattened_tokens[s:e+1])
                numbers = re.findall(r'\d+', text)
                if len(numbers) > 0:
                    for n in numbers:
                        times.append((int(n),text))
                    continue
            
            if len(found[0]) == 0:
                # print(self._conlu_to_text(self.flattened_tokens[s:e]))
                regs2 =[["doba"]]
                starts,_ =  self.find_all_reg(regs2,s,e)
                if len(starts) == 0:
                    continue
                st = starts[0]
                text = self._conllu_to_text(self.flattened_tokens[st-5:st+5])
                times.append((int(0),text))
        # print("times",times)

        if len(times) == 0:
            return []

        return max(times)

    def get_whole_sentence(self, token_indexes: list[int]):
        token_indexes = sorted(token_indexes)
        sent_ids = set()
        for token_index in token_indexes:
            sent_ids.add(self.sent_ids_for_tokens[token_index])

        sentences = []
        sentences_token_lits = [(sent_id, [w for w in self.flattened_sentences[sent_id]]) for sent_id in sent_ids]

        
        sentences = [{"text":self._conllu_to_text(sent), "range":self.start_end_from_sentence(sent_id)} for sent_id,sent in sentences_token_lits] 

        return sentences
    
    def find_all_reg(self, lemma_list: list[list[str]], from_index=0, to_index=-1, method = "strict"):
            found = []
            
            for lemma_seq in lemma_list:
                found.append(self.find_start_reg(lemma_seq, from_index, to_index,method=method))
            
            found = [f for f in found if f[0] != []]
            
            starts = []
            ends = []
            for start,length in found:
                starts += start
                ends += length

            if starts == []:
                return [],[]
            
            return starts, ends

    def find_start_reg(self, lemma_list: list[str], from_index=0, to_index=-1, method = "strict"):
        """
            Finds the indices of the first token of the given lemma sequence. This list may contain *n, which means that there can be n arbitrary tokens between the previous and the next lemma.
            For example: ['zapsaný', '*5', 'vedený', 'městský','*10', 'Praha'] will find the first token of the sequence 'zapsaný * vedený městský * Praha.
            :param lemma_seq: The sequence of lemmas to find.

            :returns: A list of indices of the first token of the given lemma sequence.
        """
        if to_index == -1:
            to_index = len(self.flattened_tokens)
        
        starts = []
        ends = []
        for i in range(from_index,to_index - len(lemma_list)+1):
            if method == "sentence":
                found, end = self._check_lemma_in_sentence(i, lemma_list)
                    
            else:
                found, end = self._check_lemma_sequence(i, lemma_list)
                
            
            
            if found:
                # print(f"{i=}, {end=}")
                    # print(self.get_whole_sentence([i,end]))
                starts.append(i)
                ends.append(end)
        return starts, ends


    def find_all_named_entities(self, entity_type: list[str], start_range: int, end_range:int, black_list: list[str] = []):
        """
        Finds all named entities of the given types within the given range of tokens.
        :param entity_type: The types of the named entities to find.
        :param start_position: The position of the token to start searching from.
        :param start_range_offset: The number of tokens to search before the start position.
        :param end_range_offset: The number of tokens to search after the start position.
        """
        black_list = [token.lower() for token in black_list]  
        named_entities = []

        for i in range(start_range, end_range):
            token = self.flattened_tokens[i]
            if 'misc' in token and token['misc'] and 'NE' in token['misc']:
                entity = token['misc']['NE']
                entities = entity.split('-')
                # remove the _* suffix from entities
                entities = [entity.split('_')[0] for entity in entities]

                for entity in entities:
                    if entity in entity_type:
                        named_entities.append(i)

        if named_entities:
            named_entities = [entity for entity in self.named_entities if entity.start_index in named_entities and entity.type in entity_type and entity.text.lower().strip() not in black_list]
            
            # Print the text of the named entities
            # for entity in named_entities:
            #     print(entity.text)



        return named_entities
    
    def find_closest_named_entity(self, entity_type: list[str], start_position: int, start_range: int, end_range:int, black_list: list[str] = []):
        """
        Finds the closest named entity of the given types within the given range of tokens.
        :param entity_type: The types of the named entities to find.
        :param start_position: The position of the token to start searching from.
        :param start_range_offset: The number of tokens to search before the start position.
        :param end_range_offset: The number of tokens to search after the start position.
        """
        named_entities = self.find_all_named_entities(entity_type, start_range, end_range, black_list)
        if named_entities:
            return min(named_entities, key=lambda x: abs(x.start_index - start_position))
        return None


