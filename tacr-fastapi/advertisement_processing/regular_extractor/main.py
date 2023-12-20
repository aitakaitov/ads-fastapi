import argparse
from collections import Counter, defaultdict
import glob
import os
from text_processor import LEMMATIZED_FOLDER, SPECIAL_TOKENS, TextProcessor
from collections import OrderedDict

from utils.html_utils import process_for_extraction

BLACK_LIST = ["Evropského parlamentu", "Rady", "EU", "ES", "GDPR", "Pplk", "Úřadu pro ochranu osobních údajů", "Úřad pro ochranu osobních údajů", "Správce", "Provozovatel", "Vámi"] + SPECIAL_TOKENS

def extract_spravce(text_processor: TextProcessor):
    input_texts = [
        ['správce', '*1', 'osobní', 'údaj'],
        ['zpracování', '*1', 'osobní', 'údaj'],
        ['souhlas', '*1', 'zpracování', '*1', 'osobní', 'údaj', '*8', 'provozovatel']
    ]

    start_idxs = []
    for text in input_texts:
        starts, _ = text_processor.find_start_reg(text)
        start_idxs += starts


    if start_idxs == []:
        return None, None

    start_idxs.sort()    


    # named_entities_of_type_A = [entity for entity in text_processor.named_entities if entity.type == "A"]
    
    # if len(named_entities_of_type_A) > 0:
    #     print("Named entities of type A:", named_entities_of_type_A)

    # Locate company   


    company = None
    first_company = None
    address = None
    for start_idx in start_idxs:
        range = text_processor.get_heading_for_token(start_idx)
        start_range = range[0]
        end_range = range[1]
        company = text_processor.find_closest_named_entity(["if","io"], start_range, start_range, end_range, BLACK_LIST) 

        if company is not None:
            if not first_company:
                first_company = company

            average_position = int((company.start_index + company.end_index) / 2)

            # Locate address
            start_index = average_position
            address = text_processor.find_closest_named_entity(["A"], start_index, start_range, end_range)

            if address is not None:
                first_company = company
                break

    return first_company, address

def extract_predavani(text_processor: TextProcessor):

    input_texts = [
        ['předávat', "*2", 'osobní', 'údaj'],
        ['kdo', 'moci', '*2', 'údaj', '*3', 'zpřístupnit'],    # kdo moci údaj o vy zpřístupnit
        ['příjemce', '*1', 'osobní', 'údaj'],  # příjemce osobní údaj
    ]

    start_idxs = []
    end_lens = []
    for text in input_texts:
        starts, length = text_processor.find_start_reg(text)
        start_idxs += starts
        end_lens += length

    if start_idxs == []:
        return []

    # Locate company
    companies = []

    for start_idx in start_idxs:
        range = text_processor.get_heading_for_token(start_idx)
        start_range = range[0]
        end_range = range[1]

        companies += text_processor.find_all_named_entities(["if","io"], start_range, end_range, BLACK_LIST)


    if len(companies) > 0:
        return list(OrderedDict.fromkeys([company.text for company in companies]))
    else:
        return [text_processor._conlu_to_text(text_processor.flattened_tokens[range[0]:range[1]]) for range in [text_processor.get_heading_for_token(start_idx) for start_idx in start_idxs]]


def extract_druh(text_processor: TextProcessor):
    found = []
    tok_2 = "*3"
    # Naše společnost zpracovává Vaše osobní údaje v rozsahu nezbytném pro naplnění výše uvedených účelů. Zpracováváme kontaktní údaje (kontaktní adresy, telefonní čísla, e-mailové a faxové adresy či jiné obdobné kontaktní údaje) a identifikační údaje (jméno, příjmení, datum narození, adresa trvalého pobytu, typ, číslo a platnost průkazu totožnosti; u klienta fyzické osoby – podnikatele také IČ a DIČ).

# výkon práv a povinností vyplývajících ze smluvního vztahu mezi Vámi a správcem; při objednávce jsou vyžadovány osobní údaje, které jsou nutné pro úspěšné vyřízení objednávky (jméno a adresa, kontakt), poskytnutí osobních údajů je nutným požadavkem pro uzavření a plnění smlouvy, bez poskytnutí osobních údajů není možné smlouvu uzavřít či jí ze strany správce plnit, zasílání obchodních sdělení a činění dalších marketingových aktivit.

    #  Pro jednoznačnou identifikaci subjektu údajů vyžadujeme následující OÚ: jméno, příjmení, datum narození, adresa trvalého bydliště.

# u e-mailových newsletterů. Provozovatel bude zpracovávat váš e‐mail a křestní jméno.

# údaje zadané v rámci tvorby uživatelského účtu (email, zvolené heslo, přezdívku, pohlaví, jméno, pokud nám ho dobrovolně poskytnete),
# přezdívku, jméno, příjmení a doručovací adresu pro účely účasti v soutěžích a turnajích a předání výher výhercům,
# komentáře a diskusní příspěvky, které na stránku sám návštěvník přidá a které tvoří obsah stránky,
# elektronickou komunikaci mezi námi a návštěvníkem vč. elektronických adres (např. obsah emailové komunikace s dotazy návštěvníka aj.),

# naje třetí osoba, je příjemcem osobních údajů tato třetí osoba. Jedná se o:
# jméno a příjmení
# zvolenou přezdívku
# herní ID.

# při objednávka být vyžadovaný osobní údaj , který být nutný pro úspěšný vyřízení objednávka ( jméno a adresa , kontakt ) , 

#  vyplnit o se další údaj , jako být jméno , příjmení , telefon a adresa ( pro využívání placený služba být tento údaj , vyjma telefon , vyžadovaný ) . dále o vy být ukládat váš příspěvek zadaný do služba , zvolený nastavení v uživatelský rozhraní služba , vy zvolený hlídací pes a oblíbený inzerát 
# osobní údaj správce být zpracovávaný váš následující osobní údaj : jméno a příjmení , adresa , telefonní číslo , e - mail , v případ podnikající osoba IČ , DIČ ( dále jen " osobní údaj " ) účel zpracování účel zpracování osobní údaj být plnění právní povinnost správce vyplývající z obsah uzavřený smlouva mezi vy jako kupující a správce jako prodávající , a plnění právní povinnost správce vyplývající z obecně závazný právní předpis . příjemce osobní údaj osobní údaj zpracovávaný pro plnění povinnost vyplývající z zvláštní právní předpis správce moci v odůvodněný případ předat orgán činný v trestní řízení .
    ret = dict()

    def search_for(key, regs: list):
        regs_poss = list() 
        
        regs_poss.extend([["zpracovávat"] + r for r in regs])
        regs_poss.extend([["osobní","údaj"] + r for r in regs])
        regs_poss.extend([["ukládat"] + r for r in regs])
        

        regs = regs_poss
        starts, ends = text_processor.find_all_reg(regs, method="sentence")
        if len(starts) > 0:
            ret[key] = text_processor.get_whole_sentence(starts+ends)

    search_for("jméno",[["jméno"]])
    search_for("příjmení",[["příjmení"]])
    search_for("narozeni",[["datum","narození"]])
    search_for("adresa",[["adresa"]])
    search_for("prukaz",[["průkaz","totožnost"]])
    search_for("ic",[["IČ"]])
    search_for("dic",[["DIČ"]])
    search_for("lokace",[["lokační","údaj"]])
    search_for("spz",[["SPZ"]])
    search_for("podpis",[["podpis"]])
    search_for("dat_schr",[["datový","schránka"]])

    # SFDI nebo zpracovatel zpracovaný následující osobní údaj : SPZ , stát registrace vozidlo , v který být vozidlo registrovaný , osobní údaj o oznamovatel : jméno , příjmení , datum narození , adresa bydliště , úředně ověřený podpis nebo jeho ekvivalent ( číslo datový schránka nebo uznávaný elektronický podpis ) . Pppppe PPPPPS tento osobní údaj SFDI získávat přímo od vy nebo od třetí osoba , který zažádat o vrácení uhrazený časový poplatek 


# v rámec registrace být o majitel příslušný realitní kancelář ukládat jméno , příjmení , místo podnikání , IČ a DIČ , pokud být on přidělený ( tento údaj být po zadání IČ automaticky importovaný z ARES ) a heslo do služba . následně moci v rámec rozhraní vyplnit o se další údaj , jako telefon a e - mail ( a u právnický osoba dále jméno a příjmení kontaktní osoba ) . dále o vy být ukládat váš inzerát zadaný do služba , zvolený nastavení v uživatelský rozhraní služba , přehled váš placený služba ( nákup a čerpání kredit ) a statistika návštěvnost , výkonnost a využívání služba , přehled makléř zadaný do váš účet , přehled pobočka

# lokační údaj , síťový identifikátor
    

    

    


    #  jméno , příjmení , datum narození , adresa trvalý pobyt , typ , číslo a platnost průkaz totožnost ; u klient fyzický osoba – podnikatel také IČ a DIČ ) . způsob zpracování osobní údaj způsob , který náš společnost zpracovávat váš osobní údaj , zah

        

    # sentences containing the found tokens
    # sentences = 

    # duration: {'short': (0, 'údaje budeme zpracovávat pouze po dobu nezbytně nutnou k dosažení '), 'long_text': [{'text': 'Pokud jste dočetli až sem, dozvíte se, že Vaše osobní údaje budeme zpracovávat pouze po dobu nezbytně nutnou k dosažení účelu, pro který byly získány. ', 'range': (1780, 1809)}, {'text': 'Vaše osobní údaje ukládáme a zpracováváme pouze po dobu nezbytně nutnou v ohledu na účel jejich zpracování\n\n', 'range': (687, 703)}]}
    print("DRUH: ",{k:v for k,v in ret.items() if v is not None and len(v) > 0}.keys())
    return ret



def extract_doba_zpracovani(text_processor: TextProcessor):
    # budou vaše osobní údaje obecně zpracovávány po dobu 7 let
    # vaše osobní údaje budeme zpracovávat po dobu 7 let, popř. do doby vyslovení vašeho nesouhlasu s jejich dalším
    # Cookies: cookies zahrnující chování uživatele mažeme po 30 dnech s tím, že starší data jsou dostupná v anonymizované podobě v Google Analytics.
    # doba zpracování a uložení osobní údaj
    # osobní údaj být SFDI zpracovaný jen po doba
    # pracovávaný po doba
    # data být uchovávaný po doba
    # zpracovávaný po doba 10
    # údaj uložit po doba
    # osobní údaj ukládat a zpracovávat pouze po doba
    # osobní údaj být zpracovávat pouze po doba
    # uchovávat osobní údaj po doba
    # osobní údaj být zpracovávaný po doba
    # být uložený v systém evidence časový poplatek po doba
    # být uložený v spisový evidence minimálně po doba 5 léta
    found = []
    
    tok_2 = "*3"
    regs = [
        ['osobní',tok_2,'údaj',tok_2,'zpracovávat',tok_2, 'po', tok_2, 'doba'],
        ['osobní',tok_2,'údaj',tok_2,'být',tok_2,'zpracovávaný',tok_2, 'po', tok_2, 'doba'],
        ['uchovávat',tok_2,'osobní',tok_2,'údaj',tok_2, 'po', tok_2, 'doba'],
        ['data',tok_2,'být',tok_2,'uchovaný',tok_2, 'po', tok_2, 'doba'],
        ['data',tok_2,'být',tok_2,'uchovávaný',tok_2, 'po', tok_2, 'doba'],
        ['uložený',tok_2,'po',tok_2,'doba',tok_2, 'léta'],
        ['být',tok_2,'zpracovávaný',tok_2,'po',tok_2, 'doba'],
        ['být',tok_2,'uložený',"*4",'po',tok_2, 'doba'],
    ]
    starts, ends = text_processor.find_all_reg(regs)
    
    
    sentences = text_processor.get_whole_sentence(starts+ends)
    short = text_processor.extract_time(sentences)
    return {"short" : short , "long_text" : sentences}

def extract_pristup(text_processor: TextProcessor):
    found = []
    tok_2 = "*3"
    # Za podmínek stanovených v GDPR máte právo na přístup ke svým osobním údajům dle čl. 15 GDPR,
    # Právo na přístup znamená, že si kdykoliv můžete požádat o naše potvrzení, zda osobní údaje, které se Vás týkají, jsou či nejsou zpracovávány,
    # b)      Právo na přístup k osobním údajům
    # Jako vlastník osobních údajů máte právo získat od SFDI potvrzení, zda Vaše osobní údaje jsou či nejsou zpracovávány.
    # máte dále právo k nim získat přístup spolu s následujícími informace o:

    # že mají právo:
    # získat od Správce potvrzení, zda osobní údaje, které se jich týkají, jsou či nejsou zpracovávány, a pokud je tomu tak, mají právo získat přístup k těmto osobním údajům a k následujícím informacím:

    # Máte právo kdykoliv odvolat svůj souhlas, opravit či doplnit osobní údaje, požadovat omezení zpracování, vznést námitku či stížnost proti zpracování osobních údajů, požadovat přenesení údajů, přístupu ke svým osobním údajům, být informován o porušení zabezpečení osobních údajů, výmazu a další práva stanovená v GDPR.

    # Na vaši žádost vystavíme potvrzení, zda zpracováváme nebo nezpracováváme vaše osobní údaje. Pokud je zpracováváme, máte také právo na informace vymezené čl. 15 nařízení evropského parlamentu a rady (EU) 2016/ 679 (GDPR).

    # právo na přístup k osobním údajům,

    # právo na přístup ke svým osobním údajům,
    # vyžádat si přístup k těmto údajům a tyto nechat aktualizovat nebo opravit,
    
    # Současně máte právo na přístup k těmto informacím týkajících se vašich osobních údajů:
    # mít právo na přístup k tento informace týkající se váš osobní údaj 
    

    tok_2 = "*3"
    regs = [
        # právo na přístup k svůj osobní údaj
        ['právo',tok_2,'přístup',"*5", 'osobní', 'údaj'],
        # Můžete nás požádat, abychom vám zaslali přehled vašich osobních údajů
        ['přehled',tok_2, 'osobní', 'údaj'],
        # kdykoliv moci požádat o náš potvrzení , zda osobní údaj , který se vy týkat , být či být zpracovávaný 
        ['potvrzení','*4','osobní','údaj'],
        # přístup k osobní údaj na váš žádost vystavit potvrzení , zda zpracovávat nebo zpracovávat 
        ['potvrzení','*4','zpracovávat' '*2', 'zpracovávat'],
        # požadovat přenesení údaj , přístup k svůj osobní údaj 
        ['přístup','*2', 'svůj', '*2', 'osobní', 'údaj']
    ]
    starts, ends = text_processor.find_all_reg(regs)

    # sentences containing the found tokens
    sentences = text_processor.get_whole_sentence(starts+ends)

    return sentences

def extract_vymaz(text_processor: TextProcessor):
    found = []
    # požadovat od my oprava nebo výmaz váš osobní údaj nebo
    # právo na výmaz některý osobní údaj 

    # právo na výmaz osobních
    # Právo na výmaz znamená, že musíme vymazat Vaše osobní údaje pokud 

    # osobních údajů, výmazu a další práva stanovená v GDPR.
    # lemma
    #oprava nebo výmaz osobní údaj
    #  právo na výmaz jako vlastník osobní údaj mít p
    # právo na výmaz se uplatnit
    # oprava nebo výmaz osobní údaj 
    # výmaz a další právo stanovený 
    # požádat o jeho výmaz 
    #  právo na výmaz moci požádat
    #bez zbytečný odklad vymazat osobní údaj , který se vy týkat
    # právo na výmaz údaj
    # právo na výmaz
    # žádost o výmaz
    # , právo na výmaz osobní údaj 
    # požadovat výmaz tento osobní údaj

    
    regs = [
        ['právo','*2', 'výmaz'],
        ['výmaz','*2', 'osobní', 'údaj'],
        ['osobní', 'údaj','*2', 'výmaz']
    ]
    starts, ends = text_processor.find_all_reg(regs)
    # sentences containing the found tokens
    sentences = text_processor.get_whole_sentence(starts+ends)
    return sentences

def extract_lhuta(text_processor: TextProcessor):

    regs = [
        ['obdržet','*4', 'žádost'],
        ['žádosti','*4', 'lhůtu']
    ]
    starts, ends = text_processor.find_all_reg(regs)
    # sentences containing the found tokens
    sentences = text_processor.get_whole_sentence(starts+ends)
    return sentences


def extract_from_agreements(texts: list[dict[str, object]], text_processor: TextProcessor):
    text_processor.process(texts)
    
    company, address = extract_spravce(text_processor)
    third_companies = extract_predavani(text_processor)
    
    duration = extract_doba_zpracovani(text_processor)

    access = extract_pristup(text_processor)
 
    delete  = extract_vymaz(text_processor)
    lhuta  = extract_lhuta(text_processor)

    druh = extract_druh(text_processor)

    return {
        "company": company.text if company is not None else None,
        "address": address.text if address is not None else None,
        "third_companies": third_companies,
        "duration": duration,
        "access" :access,
        "delete" : delete,
        "lhuta" : lhuta,
        "druh" :druh
    }


def main(args):
    datapath = args.datadir
    
    found_entities = defaultdict(list)
    for filename in glob.glob(os.path.join(datapath, '*.html')):
        print("\n ===== Processing file:", filename)            
        with open(filename, "r", encoding="utf8") as file:
            html = file.read()

        processed = process_for_extraction(html)

        textProcessor = TextProcessor(filename)

        out_dict = extract_from_agreements(processed["texts"], textProcessor)


        for key,value in out_dict.items():
            found_entities[key].append(value)

        # print("Company:", out_dict["company"])
        # print("Address:", out_dict["address"])

        # for company in out_dict["third_companies"]:
        #     print("3rd party company:", company)

        for key, value in out_dict.items():
            print(f"{key}: {value}")

        if args.lemmatize:
            if not os.path.exists(LEMMATIZED_FOLDER):
                os.makedirs(LEMMATIZED_FOLDER)
            textProcessor.write_lemmatized_text()
    
    # count found entities
    for key,value in found_entities.items():
        total = len(value)
        value = [v for v in value if v is not None and len(v) > 0]
        print(f"{key}: {len(value)}/{total}")
        if key=="druh":
            sum = Counter()
            for site in value:
                for d,v in site.items():
                    sum[d] += 1
            
            print(f"\t{sum}")
            



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Evaluate directory.')
    parser.add_argument('--datadir', type=str, help='Predicted directory', required=True)
    parser.add_argument('--lemmatize', action='store_true', help='Lemmatize the text and write it to a new file')
    args = parser.parse_args()
    
    main(args)