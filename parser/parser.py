import glob
import json
import unidecode

from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Triple:
    text: str
    triple_list: list[list[str]]

@dataclass
class Label:
    name: str
    start: int
    stop: int

def load_file(file_location: str) -> dict[str, Any]:
    with open(file_location, 'rb') as file:
        data = json.load(file)
    
    return data

def parse_file(data: dict[str, Any]) -> tuple[list[Triple], dict[int, str]]:

    triples: list[Triple] = []
    relations = set()

    entities: dict[str, Label] = {}  # id: name, start, stop

    for article in data:

        try:
            article['data']['text'] = article['data'].pop('0')
        except:
            ...

        t: dict[tuple[int, int], Triple] = {}
        for annotation in article['annotations']:
            for triple in annotation['result']:
                
                if triple['type'] == 'labels':
                    entities[triple['id']] = Label(
                        triple['value']['text'],
                        triple['value']['start'],
                        triple['value']['end']
                    )
                elif triple['type'] == 'relation':

                    from_entity = entities[triple['from_id']]
                    to_entity = entities[triple['to_id']]

                    begin_text_pos = min(from_entity.start, to_entity.start)
                    end_text_pos = max(from_entity.stop, to_entity.stop)

                    sp, ep = get_sentences(article['data']['text'], begin_text_pos, end_text_pos)

                    interval_to_change = None
                    for interval in t:
                        overlapping_interval = get_overlapping_interval(interval, (sp, ep))
                        if overlapping_interval:
                            if overlapping_interval != interval:
                                interval_to_change = interval
                            sp, ep = overlapping_interval
                            break
                    
                    if (sp, ep) in t and interval_to_change:
                        t[(sp, ep)].text = article['data']['text'][sp:ep+1]
                        t[(sp, ep)].triple_list = t[(sp, ep)].triple_list + t.pop(interval_to_change).triple_list
                    elif interval_to_change:
                        t[(sp, ep)] = t.pop(interval_to_change)
                        t[(sp, ep)].text = article['data']['text'][sp:ep+1]
                    elif not (sp, ep) in t:
                        t[(sp, ep)] = Triple(article['data']['text'][sp:ep+1], [])

                    for relation in triple['labels']:
                        relations.add(relation)
                        t[(sp, ep)].triple_list.append([unidecode.unidecode(from_entity.name).strip(), relation, unidecode.unidecode(to_entity.name).strip()])
    
        for k in t:
            t[k].text = unidecode.unidecode(t[k].text).strip()
            triples.append(t[k])

        relations_result: dict[int, str] = {}
        for i, relation in enumerate(relations):
            relations_result[i] = relation

    return triples, relations_result

def get_overlapping_interval(i1: tuple[int, int], i2: tuple[int, int]) -> Optional[tuple[int, int]]:
    if i1[1] >= i2[0] and i1[0] <= i2[1]:
        return (min(i1[0], i2[0]), max(i1[1], i2[1]))

def get_sentences(text: str, begin_pos: int, end_pos: int) -> tuple[int, int]:
    chars = list(text)

    start_sentence = 0
    for i in range(begin_pos, -1, -1):
        if chars[i] == '.':
            start_sentence = i + 2
            break

    stop_sentence = len(chars) - 1
    for i in range(end_pos, len(chars)):
        if chars[i] == '.':
            stop_sentence = i
            break

    return start_sentence, stop_sentence


def store_triples(file_name: str, triples: list[Triple]) -> None:

    result: list[dict[str, Any]] = []

    for triple in triples:
        result.append({'text': triple.text, 'triple_list': triple.triple_list})

        with open(f'{file_name}_spn.json', 'a') as spn_file:
            line = {'sentText': triple.text, 'relationMentions': []}
            for t in triple.triple_list:
                line['relationMentions'].append({'em1Text': t[0], 'em2Text': t[2], 'label': t[1]})
            json.dump(line, spn_file, ensure_ascii=False)
            spn_file.write('\n')

    with open(file_name, 'w') as file:
        json.dump(result, file, ensure_ascii=False)

def store_relations(file_name: str, relations: dict[int, str]) -> None:

    result: list[dict[str, tuple[str, int]]] = []
    result.append(dict())
    result.append(dict())

    for key in relations:
        result[0][str(key)] = relations[key]
        result[1][relations[key]] = key

    with open(file_name, 'w') as file:
        json.dump(result, file, ensure_ascii=False)

def split(triples: list[Triple], ratio_train: float = 0.8) -> tuple[list[Triple], list[Triple]]:

    number_of_relations: dict[str, int] = {}

    for text in triples:
        for triple in text.triple_list:
            if triple[1] not in number_of_relations:
                number_of_relations[triple[1]] = 0

            number_of_relations[triple[1]] += 1

    print(number_of_relations)
    train_split: list[Triple] = []
    test_split: list[Triple] = []

    train_statistics = {}
    test_statistics = {}

    for relation in number_of_relations:
        train_statistics[relation] = 0
        test_statistics[relation] = 0

    for text in triples:

        train_punishment = 0
        test_punishment = 0

        for triple in text.triple_list:
            if train_statistics[triple[1]] > ratio_train * number_of_relations[triple[1]]:
                train_punishment += train_statistics[triple[1]] - ratio_train * number_of_relations[triple[1]]
            if test_statistics[triple[1]] > (1 - ratio_train) * number_of_relations[triple[1]]:
                test_punishment += test_statistics[triple[1]] - (1 - ratio_train) * number_of_relations[triple[1]]

        if train_punishment <= test_punishment:
            train_split.append(text)

            for triple in text.triple_list:
                train_statistics[triple[1]] += 1

        else:
            test_split.append(text)
            
            for triple in text.triple_list:
                test_statistics[triple[1]] += 1

    for stat in train_statistics:
        train_statistics[stat] = round(train_statistics[stat] / number_of_relations[stat], 2)

    for stat in test_statistics:
        test_statistics[stat] = round(test_statistics[stat] / number_of_relations[stat], 2)
    
    print('train_statistics: ', str(train_statistics))
    print('test_statistics: ', str(test_statistics))
    return train_split, test_split
if __name__ == '__main__':

    train_data = json.loads('[]')
    test_data = json.loads('[]')

    for file in glob.glob('labeled_data/*.json'):
        part_data = load_file(file)

        for data in part_data:
            try:
                data['data']['text'] = data['data'].pop('0')
            except:
                ...
            if 'austria' in data['data']['text'][:100].lower() or 'germany' in data['data']['text'][:100].lower():
                test_data += [data]
            else:
                train_data += [data]


    train_triples, relations = parse_file(train_data)
    test_triples, _ = parse_file(test_data)

    train, validation = split(train_triples, 0.8)

    store_triples('parsed/triples_train.json', train)
    store_triples('parsed/triples_validation.json', validation)
    store_triples('parsed/triples_test.json', test_triples)
    store_relations('parsed/rel2id.json', relations)
