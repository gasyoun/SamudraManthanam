# xwalk-s7 — Samudra sibling corpora shape verification (H4743)

_Generated: 15-09-2026 by `scripts/xwalk_s7_verify_siblings.py` — deterministic, re-run to reproduce._

**Verdict: FAIL**

Verifies presumed-same-shape of numbered sibling JSONL corpora
(`NN_atharvaveda.jsonl`, `NN_mahabharata-*.jsonl`): schema parity,
line/group parity (one `sa` + one `ru` per group), id/group/chapter
consistency, first/middle/last sample language sanity.

## Family `atharvaveda` — 19 sibling files (expected 20)

- **FINDING**: expected 20 files, found 19
  - AVŚ book 20 (Kuntāpa) absent from the corpus — documented shape fact, not sibling drift (book-20 hymns have no RU side to align).
| file | lines | sa | ru | groups | parity defects | schema |
|---|---|---|---|---|---|---|
| 01_atharvaveda.jsonl | 450 | 153 | 153 | 153 | 0 | OK |
| 02_atharvaveda.jsonl | 583 | 207 | 207 | 207 | 0 | OK |
| 03_atharvaveda.jsonl | 659 | 230 | 230 | 230 | 0 | OK |
| 04_atharvaveda.jsonl | 941 | 324 | 324 | 324 | 0 | OK |
| 05_atharvaveda.jsonl | 1040 | 376 | 376 | 376 | 0 | OK |
| 06_atharvaveda.jsonl | 1320 | 454 | 454 | 454 | 0 | OK |
| 07_atharvaveda.jsonl | 905 | 286 | 286 | 286 | 0 | OK |
| 08_atharvaveda.jsonl | 727 | 259 | 259 | 259 | 0 | OK |
| 09_atharvaveda.jsonl | 853 | 302 | 302 | 302 | 0 | OK |
| 10_atharvaveda.jsonl | 915 | 350 | 350 | 350 | 0 | OK |
| 11_atharvaveda.jsonl | 828 | 313 | 313 | 313 | 0 | OK |
| 12_atharvaveda.jsonl | 776 | 304 | 304 | 304 | 0 | OK |
| 13_atharvaveda.jsonl | 502 | 188 | 187 | 188 | 1 | OK |
| 14_atharvaveda.jsonl | 388 | 139 | 139 | 139 | 0 | OK |
| 15_atharvaveda.jsonl | 492 | 220 | 220 | 220 | 0 | OK |
| 16_atharvaveda.jsonl | 237 | 103 | 103 | 103 | 0 | OK |
| 17_atharvaveda.jsonl | 80 | 30 | 30 | 30 | 0 | OK |
| 18_atharvaveda.jsonl | 742 | 283 | 283 | 283 | 0 | DRIFT(ru) |
| 19_atharvaveda.jsonl | 813 | 311 | 311 | 311 | 0 | OK |

Family schema — sa key set (14 keys): chapter, deleted, group, html, id, lang, passage, script, seg, seq, slp1, structure, text, work
Family schema — ru key set: author, chapter, deleted, group, html, id, lang, passage, script, seg, seq, structure, text, work
- ru variant with extra keys []: documented heterogeneity (commentary-annotated ru segments)
- schema parity across siblings (no novel key-set variants): **FAIL**

### Sample parity (first · middle · last group, per file)

- `01_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ye triṣaptāḥ pariyanti viśvā rūpāṇi bibhrataḥ । vācas patir balā teṣāṃ tanvo adya dadhātu …'
  - ru: 'Те трижды семь, что вокруг движутся, Неся все формы, — Пусть Повелитель Речи силы их, (Их)…'
- `01_atharvaveda:26.3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yūyam naḥ pravato napān marutaḥ sūryatvacasaḥ । śarma yachatha saprathāḥ ॥3॥'
  - ru: 'Вы, отпрыски высоты, Маруты солнечнокожие, Даруйте нам широкую защиту!'
- `01_atharvaveda:9.4` — sa_ok=True ru_ok=True → **PASS**
  - sa: "aiṣāṃ yajñam uta varco dade 'haṃ rāyas poṣam uta cittāny agne । sapatnā asmad adhare bhava…"
  - ru: 'Я забрал себе их жертву и блеск, (Их) процветание богатства и намерения, о Агни. Да будут …'
- `02_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'venas tat paśyat paramaṃ guhā yad yatra viśvaṃ bhavaty ekarūpam । idaṃ pṛśnir aduhaj jāyam…'
  - ru: 'Вена видит то, что в глубокой тайне, Где все бывает одной формы. Это (всё) Пришни дала над…'
- `02_atharvaveda:26.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'eha yantu paśavo ye pareyur vāyur yeṣāṃ sahacāraṃ jujoṣa । tvaṣṭā yeṣāṃ rūpadheyāni vedāsm…'
  - ru: 'Пусть придут сюда животные, которые ушли прочь, (Те), чьим обществом насладился Ваю, (Те),…'
- `02_atharvaveda:9.5` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yaś cakāra sa niṣ karat sa eva subhiṣaktamaḥ । sa eva tubhyaṃ bheṣajāni kṛṇavad bhiṣajā śu…'
  - ru: 'Кто сделал (это), тот пусть и приведет в порядок — Ведь он лучший из целителей. Это он пус…'
- `03_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'agnir naḥ śatrūn praty etu vidvān pratidahann abhiśastim arātim । sa senāṃ mohayatu pareṣā…'
  - ru: 'Пусть Агни-знаток выступит против наших врагов, Встречая огнем проклятие, враждебность! Пу…'
- `03_atharvaveda:22.3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yena hastī varcasā saṃbabhūva yena rājā manuṣyesv apsv antaḥ । yena devā devatām agra āyan…'
  - ru: '(Тот) блеск, с которым возник слон, С которым царь среди людей, в водах, С которым боги вн…'
- `03_atharvaveda:9.6` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ekaśataṃ viṣkandhāni viṣṭhitā pṛthivīm anu । teṣāṃ tvām agre uj jaharur maṇiṃ viṣkandhadūṣ…'
  - ru: 'Сто одна вишкандха Рассеяны по земле. Для них сначала они вынули тебя — Амулет, вредящий в…'
- `04_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'brahma jajñānaṃ prathamaṃ purastād vi sīmataḥ suruco vena āvaḥ । sa budhnyā upamā asya viṣ…'
  - ru: 'Брахмана, рожденного первым на востоке, Выделил Вена из ярко светящейся границы. Он вы(дел…'
- `04_atharvaveda:27.6` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yadīd idaṃ maruto mārutena yadi devā daivyenedṛg āra । yūyam īśidhve vasavas tasya niṣkṛte…'
  - ru: 'Если уж, о Маруты, из-за (чего-то), связанного с Марутами, Если, о боги, из-за (чего-то), …'
- `04_atharvaveda:9.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yad āñjanaṃ traikakudam jātaṃ himavatas pari । yātūṃś ca sarvāñ jambhayat sarvāś ca yātudh…'
  - ru: 'Та мазь, происходящая с Трикакуда, Что рождена на Гималаях. Да загрызет она всех колдунов …'
- `05_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: "ṛdhaṅmantro yoniṃ ya ābabhūvāmṛtāsur vardhamānaḥ sujanmā । adabdhāsur bhrājamāno 'heva tri…"
  - ru: 'Кто находится в лоне с особым священным изречением, С бессмертной силой жизни, возрастающи…'
- `05_atharvaveda:23.5` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ye krimayaḥ śitikakṣā ye kṛṣṇāḥ śitibāhavaḥ । ye ke ca viśvarūpās tān krimīn jambhayāmasi …'
  - ru: '(Те) черви, что с белыми плечами, (Те) черные, что с белыми руками, И какие бы они ни были…'
- `05_atharvaveda:9.8` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ud āyur ud balam ut kṛtam ut kṛtyām un manīṣām ud indriyam । āyuṣkṛd āyuṣpatnī svadhāvanta…'
  - ru: 'Вверх срок жизни! Вверх силу! Вверх действие! Вверх исполнение! Вверх понимание! Вверх ощу…'
- `06_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'doṣo gāya bṛhad gāya dyumad dhehi । ātharvaṇa stuhi devaṃ savitāram ॥1॥'
  - ru: 'Пой вечером! Пой (мелодию) брихат! Награждай блистательным (добром), о сын Атхарвана! Слав…'
- `06_atharvaveda:32.3` — sa_ok=True ru_ok=True → **PASS**
  - sa: "abhayaṃ mitrāvaruṇāv ihāstu no 'rciṣāttriṇo nudataṃ pratīcaḥ । mā jñātāraṃ mā pratiṣṭhāṃ v…"
  - ru: 'Да будет у нас здесь отсутствие страха, о Митра-Варуна! Пламенем вашим оттолкните прочь ат…'
- `06_atharvaveda:99.3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'pari dadma indrasya bāhū samantaṃ trātus trāyatāṃ naḥ । deva savitaḥ soma rājant sumanasaṃ…'
  - ru: 'Мы соединяем вокруг себя две руки Индры-спасителя. Пусть он спасет нас! О бог Савитар! О ц…'
- `07_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: "dhītī vā ye anayan vāco agraṃ manasā vā ye 'vadann ṛtāni । tṛtīyena brahmaṇā vāvṛdhānās tu…"
  - ru: '(Те), кто вел начало речи с помощью озарения Или кто мыслью высказывал истины, Усиливаясь …'
- `07_atharvaveda:51.2` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'uta gnā vyantu devapatnīr indrāṇy agnāyy aśvinī rāṭ । ā rodasī varunānī śṛṇotu vyantu devī…'
  - ru: 'А также божественные жены — супруги богов пусть охотно придут: Индрани, Агнайи, Ашвини-цар…'
- `07_atharvaveda:99.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'dhruvaṃ dhruveṇa haviṣāva somaṃ nayāmasi । yathā na indraḥ kevalīr viśaḥ saṃmanasas karat …'
  - ru: 'Крепким возлиянием крепкого Сому мы направляем вниз, Чтобы Индра сделал племена Принадлежа…'
- `08_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'antakāya mṛtyave namaḥ prānā apānā iha te ramantām । ihāyam astu puruṣaḥ sahāsunā sūryasya…'
  - ru: 'Причиняющей конец Смерти поклон! Вдохи и (выдохи) твои пусть останутся здесь! Здесь пусть …'
- `08_atharvaveda:4.6` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'indrāsomā pari vāṃ bhūtu viśvata iyaṃ matiḥ kakṣyāśveva vājinā । yāṃ vāṃ hotrāṃ parihinomi…'
  - ru: 'О Индра-Сома, да окружит вас со всех сторон Эта молитва, как подпруга — двоих коней, прино…'
- `08_atharvaveda:9.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'aprāṇaiti prāṇena prāṇatīnāṃ virāṭ svarājam abhy eti paścāt । viśvaṃ mṛśantīm abhirūpāṃ vi…'
  - ru: 'Лишенная дыхания, она движется дыханием дышащих. Вирадж приближается к Самовластному сзади…'
- `09_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'divas pṛthivyā antarikṣāt samudrād agner vātān madhukaśā hi jajñe । tāṃ cāyitvāmṛtaṃ vasān…'
  - ru: 'Ведь медовая плеть родилась с неба, с земли, Из воздушного пространства, из океана, из огн…'
- `09_atharvaveda:5.27` — sa_ok=True ru_ok=True → **PASS**
  - sa: "yā pūrvaṃ patiṃ vittvā 'thānyaṃ vindate 'param । pañcaudanaṃ ca tāv ajaṃ dadāto na vi yoṣa…"
  - ru: 'Какая (женщина), приобретя прежнего мужа, Затем приобретает другого, последующего, — Если …'
- `09_atharvaveda:9.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yuktā mātāsid dhuri dakṣiṇāyā atiṣṭhad garbho vṛjanīṣv antaḥ । amīmed vatso anu gām apaśya…'
  - ru: 'Мать запряжена была в ярмо дакшины. Плод пребывал внутри загонов. Теленок мычал (и) глядел…'
- `10_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yāṃ kalpayanti vahatau vadhūm iva viśvarūpāṃ hastakṛtāṃ cikitsavaḥ । sārād etv apa nudāma …'
  - ru: '(Ее), сделанную руками, многообразную, кого умельцы Готовят как невесту на свадьбу, — Пуст…'
- `10_atharvaveda:5.32` — sa_ok=True ru_ok=True → **PASS**
  - sa: "viṣṇoḥ kramo 'si sapatnahauṣadhīsaṃśito somatejāḥ । oṣadhīr anu vi krame 'haṃ oṣadhībhyas …"
  - ru: 'Ты — шаг Вишну, убивающий соперников, отточенный (целебными) травами, воспламененный сомой…'
- `10_atharvaveda:9.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'devāḥ pitaro manuṣyā gandharvāpsarasaś ca ye । te tvā sarve gopsyanti sātirātram ati drava…'
  - ru: 'Боги, отцы, люди, И (те), что гандхарвы-апсараc, — Все они будут охранять тебя. Спеши чере…'
- `11_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'agne jāyasvāditir nāthiteyaṃ brahmaudanaṃ pacati putrakāmā । saptaṛṣayo bhūtakṛtas te tvā …'
  - ru: 'Агни, рождайся! Адити, обращаясь здесь за помощью, Варит брахманскую рисовую кашу, желая с…'
- `11_atharvaveda:4.14` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'apānati prāṇati puruṣo garbhe antarā । yadā tvaṃ prāṇa jinvasy atha sa jāyate punaḥ ॥14॥'
  - ru: 'Человек в утробе Выдыхает (и) вдыхает. Когда ты, дыхание, оживляешь (его), Тогда он рождае…'
- `11_atharvaveda:9.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'aliklavā jāṣkamadā gṛdhrāḥ śyenāḥ patatriṇaḥ । dhvāṅkṣāḥ śakunayas tṛpyantv amitreṣu samīk…'
  - ru: 'Пусть стервятники (?), джашкамада, Ястребы, соколы крылатые, Вороны, птицы насытятся, Пока…'
- `12_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'satyaṃ bṛhad ṛtam ugraṃ dīkṣā tapo brahma yajñaḥ pṛthivīṃ dhārayanti । sā no bhūtasya bhav…'
  - ru: 'Высокая истина, грозный (космический) закон, посвящение, покаяние, Брaхман, жертва поддерж…'
- `12_atharvaveda:3.40` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yāvanto asyāḥ pṛthivīṃ sacante asmat putrāḥ pari ye saṃbabhūvuḥ । sarvāṃs tām̐ upa pātre h…'
  - ru: 'Сколь многие у нее живут на земле, (Те) сыновья, которые произошли от нас, — Всех их вы пр…'
- `12_atharvaveda:5.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'āyuś ca rūpaṃ ca nāma ca kīrtiś ca prāṇaś cāpānaś ca cakṣuś ca śrotraṃ ca ॥9॥'
  - ru: 'И срок жизни, и форма, и имя, и почет, и вдох, и выдох, и зрение, и слух,'
- `13_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'udehi vājin yo apsv antar idaṃ rāṣṭraṃ pra viśa sūnṛtāvat । yo rohito viśvam idaṃ jajāna s…'
  - ru: 'Поднимись, могучий, (тот), что внутри вод! Войди в это царство, полное блаженства! Рохита,…'
- `13_atharvaveda:2.40` — sa_ok=True ru_ok=True → **PASS**
  - sa: "rohito loko abhavad rohito 'ty atapad divam । rohito raśmibhir bhūmiṃ samudram anu saṃ car…"
  - ru: 'Рохита стал мирозданием. Рохита переполнил небо жаром. Рохита (своими) лучами странствует …'
- `13_atharvaveda:4.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'raśmibhir nabha ābhṛtaṃ mahendra ety āvṛtaḥ ॥9॥'
  - ru: 'Он идет по небосводу, наполненному (его) лучами, великий Индра, окруженный.'
- `14_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'satyenottabhitā bhūmiḥ sūryeṇottabhitā dyauḥ । ṛtenādityās tiṣṭhanti divi somo adhi śritaḥ…'
  - ru: 'Правдой держится земля. Солнцем держится небо. Законом существуют Адитьи, Сома устроен на …'
- `14_atharvaveda:2.14` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ātmanvaty urvarā nārīyam āgan tasyāṃ naro vapata bījam asyām । sā vaḥ prajāṃ janayad vakṣa…'
  - ru: 'Одушевленная пашня — пришла эта женщина, В нее такую бросайте семя, о мужи! Пусть родит он…'
- `14_atharvaveda:2.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'idaṃ su me naraḥ śṛṇuta yayāśiṣā daṃpatī vāmam aśnutaḥ । ye gandharvā apsarasaś ca devīr e…'
  - ru: 'Сейчас, о мужи, услышьте же от меня, Каким благословением супружеская чета достигнет (всег…'
- `15_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'vrātya āsīd īyamāna eva sa prajāpatiṃ sam airayat ॥1॥'
  - ru: 'Был Братья, бродящий (вокруг). Он возбудил Праджапати.'
- `15_atharvaveda:2.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'sa ud atiṣṭhat sa prācīṃ diśam anu vy acalat । [1]'
  - ru: 'Он поднялся. Он последовал в восточную сторону.'
- `15_atharvaveda:9.3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'sabhāyāś ca vai sa samiteś ca senāyāś ca surāyāś ca priyaṃ dhāma bhavati ya evaṃ veda ॥3॥'
  - ru: 'Любимой родиной и для собрания, и для места встреч, и для войска, и для суры становится то…'
- `16_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: "atisṛṣṭo apāṃ vṛṣabho 'tisṛṣṭā agnayo divyāḥ ॥1॥"
  - ru: 'Отброшен бык вод; отброшены небесные огни.'
- `16_atharvaveda:6.8` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kumbhīkāḥ dūṣīkāḥ pīyakān ॥8॥'
  - ru: '(Демонов) кумбхика, (тех), кто наводит порчу, хулителей.'
- `16_atharvaveda:9.4` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'vasyobhūyāya vasumān yajño vasu vaṃsiṣīya vasumān bhūyāsaṃ vasu mayi dhehi ॥4॥'
  - ru: 'Чтобы стать лучше. Жертва — носительница добра. Я хочу создать себе добро. Да буду я носит…'
- `17_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'viṣāsahiṃ sahamānaṃ sāsahānaṃ sahīyāṃsam । sahamānaṃ sahojitaṃ svarjitaṃ gojitaṃ saṃdhanāj…'
  - ru: 'Всепобеждающего, победного, Победившего, самого победоносного, Победного, завоевавшего поб…'
- `17_atharvaveda:1.23` — sa_ok=True ru_ok=True → **PASS**
  - sa: "astaṃyate namo 'stameṣyate namo 'stamitāya namaḥ । virāje namaḥ svarāje namaḥ samrāje nama…"
  - ru: 'Заходящему поклон, собирающемуся зайти Поклон, зашедшему поклон. Правящему поклон, самосто…'
- `17_atharvaveda:1.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tvaṃ na indra mahate saubhagāyādabdhebhiḥ pari pāhy aktubhis taved viṣṇo bahūdhā vīryāni ।…'
  - ru: 'Ты нас, о Индра, на великое счастье Защити повсюду невредимыми лучами! Ведь у тебя, о Вишн…'
- `18_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'o cit sakhāyaṃ sakhyā vavṛtyāṃ tiraḥ puru cid arṇavaṃ jaganvān । pitur napātam ā dadhīta v…'
  - ru: 'Как бы я хотела повернуть друга к дружбе, Даже если он прошел много через бурный поток. Пр…'
- `18_atharvaveda:3.28` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'somo mā viśvair devair udīcyā diśaḥ pātu bāhucyutā pṛthivī dyām ivopari । lokakṛtaḥ pathik…'
  - ru: 'Сома со Всеми-Богами пусть защитит меня с северной стороны, Сдвинута рукой земля, словно к…'
- `18_atharvaveda:4.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'pūrvo agniṣ ṭvā tapatu śaṃ purastāc chaṃ paścāt tapatu gārhapatyaḥ । dakṣiṇāgniṣ ṭe tapatu…'
  - ru: 'Да сожжет тебя на благо восточный огонь спереди! На благо да сожжет тебя огонь домохозяина…'
- `19_atharvaveda:1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'saṃsaṃ sravantu nadyaḥ saṃ vātāḥ saṃ patatriṇaḥ । yajñam imaṃ vardhayatā giraḥ saṃsrāvyeṇa…'
  - ru: 'Пусть вместе стекутся реки, Вместе ветры, вместе птицы! О песни, усильте эту жертву! Я при…'
- `19_atharvaveda:27.5` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ghṛtena tvā sam ukṣāmy agne ājyena vardhayan । agneś candrasya sūryasya mā prāṇaṃ māyino d…'
  - ru: 'Я кроплю всего тебя жиром, о Агни, Подкрепляя жертвенным маслом. Пусть коварные не повредя…'
- `19_atharvaveda:9.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: "nakṣatram ulkābhihataṃ śam astu naḥ śaṃ no 'bhicārāḥ śam u santu kṛtyāḥ । śaṃ no nikhātā v…"
  - ru: 'Созвездие, ударенное метеоритом, — нам на благо. На благо нам волшебство, на благо пусть б…'

### Structural problems (19 files)

- `01_atharvaveda.jsonl`: L3: id mismatch '01_atharvaveda:1.1.comm1'; L3: group mismatch '01_atharvaveda:1.1'; L3: unexpected seg 'comm1'; L4: id mismatch '01_atharvaveda:1.1.comm2'; L4: group mismatch '01_atharvaveda:1.1'
- `02_atharvaveda.jsonl`: L1: chapter '1' != book 2; L3: id mismatch '02_atharvaveda:1.1.comm1'; L3: group mismatch '02_atharvaveda:1.1'; L3: unexpected seg 'comm1'; L4: id mismatch '02_atharvaveda:1.1.comm2'
- `03_atharvaveda.jsonl`: L1: chapter '1' != book 3; L3: id mismatch '03_atharvaveda:1.1.comm1'; L3: group mismatch '03_atharvaveda:1.1'; L3: unexpected seg 'comm1'; L4: id mismatch '03_atharvaveda:1.1.comm2'
- `04_atharvaveda.jsonl`: L1: chapter '1' != book 4; L3: id mismatch '04_atharvaveda:1.1.comm1'; L3: group mismatch '04_atharvaveda:1.1'; L3: unexpected seg 'comm1'; L4: id mismatch '04_atharvaveda:1.1.comm2'
- `05_atharvaveda.jsonl`: L1: chapter '1' != book 5; L3: id mismatch '05_atharvaveda:1.1.comm1'; L3: group mismatch '05_atharvaveda:1.1'; L3: unexpected seg 'comm1'; L4: id mismatch '05_atharvaveda:1.1.comm2'

## Family `mahabharata` — 18 sibling files (expected 18)

| file | lines | sa | ru | groups | parity defects | schema |
|---|---|---|---|---|---|---|
| 01_mahabharata-adiparva.jsonl | 3742 | 1387 | 1387 | 1387 | 0 | OK |
| 02_mahabharata-sabhaparva.jsonl | 2132 | 438 | 438 | 438 | 0 | OK |
| 03_mahabharata-aranyakaparva.jsonl | 5385 | 2033 | 2033 | 2033 | 0 | OK |
| 04_mahabharata-virataparva.jsonl | 1196 | 360 | 360 | 360 | 0 | OK |
| 05_mahabharata-udyogaparva.jsonl | 3878 | 1006 | 1006 | 1006 | 0 | OK |
| 06_mahabharata-bhishmaparva.jsonl | 3450 | 1337 | 1337 | 1337 | 0 | OK |
| 07_mahabharata-dronaparva.jsonl | 4367 | 1219 | 1219 | 1219 | 0 | OK |
| 08_mahabharata-karnaparva.jsonl | 1726 | 618 | 618 | 618 | 0 | OK |
| 09_mahabharata-shalyaparva.jsonl | 1995 | 533 | 533 | 533 | 0 | OK |
| 10_mahabharata-sauptikaparva.jsonl | 460 | 85 | 85 | 85 | 0 | OK |
| 11_mahabharata-striparva.jsonl | 468 | 122 | 122 | 122 | 0 | OK |
| 12_mahabharata-shantiparva.jsonl | 25523 | 12692 | 12692 | 12692 | 0 | OK |
| 13_mahabharata-anushasanaparva.jsonl | 13074 | 6537 | 6537 | 6537 | 0 | OK |
| 14_mahabharata-ashvamedhikaparva.jsonl | 1917 | 517 | 517 | 517 | 0 | OK |
| 15_mahabharata-ashramavasikaparva.jsonl | 644 | 162 | 162 | 162 | 0 | OK |
| 16_mahabharata-mausalaparva.jsonl | 261 | 42 | 42 | 42 | 0 | OK |
| 17_mahabharata-mahaprasthanikaparva.jsonl | 113 | 26 | 26 | 26 | 0 | OK |
| 18_mahabharata-svargarohanikaparva.jsonl | 177 | 28 | 28 | 28 | 0 | OK |

Family schema — sa key set (15 keys): author, chapter, deleted, group, html, id, lang, passage, script, seg, seq, slp1, structure, text, work
Family schema — ru key set: author, chapter, deleted, group, html, id, lang, passage, script, seg, seq, structure, text, work
- ru variant with extra keys []: documented heterogeneity (commentary-annotated ru segments)
- schema parity across siblings (no novel key-set variants): **PASS**

### Sample parity (first · middle · last group, per file)

- `01_mahabharata-adiparva:1.1.0` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'nārāyaṇaṃ namaskṛtya naraṃ caiva narottamam । devīṃ sarasvatīṃ caiva tato jayamudīrayet ॥0…'
  - ru: 'Поклонившись Нараяне и Наре, величайшему из мужей, а также богине Сарасвати, должно затем …'
- `01_mahabharata-adiparva:1.223.4` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'jyeṣṭhastrātā bhavati vai jyeṣṭho muñcati kṛcchrataḥ । jyeṣṭhaścenna prajānāti kanīyānkiṃ …'
  - ru: 'Старший (брат) становится спасителем, старший вызволяет (младшего) из беды. И если старший…'
- `01_mahabharata-adiparva:1.99.6-17` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'dharmayuktasya dharmātmanpiturāsīttarī mama । sā kadācidahaṃ tatra gatā prathamayauvane ॥6…'
  - ru: 'Была у моего отца, преданного закону, лодка, о справедливый! Однажды в первой еще молодост…'
- `02_mahabharata-sabhaparva:2.1.1-2` — sa_ok=True ru_ok=True → **PASS**
  - sa: "tato'bravīnmayaḥ pārthaṃ vāsudevasya sannidhau । prāñjaliḥ ślakṣṇayā vācā pūjayitvā punaḥ …"
  - ru: 'Тогда в присутствии Васудевы Майя сказал Партхе, обратившись к нему с кроткими словами и с…'
- `02_mahabharata-sabhaparva:2.51.10-11` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'sarvathā putra balibhirvigrahaṃ te na rocaye । vairaṃ vikāraṃ sṛjati tadvai śastramanāyasa…'
  - ru: 'Я никогда, о сын, не одобрял твоей вражды с сильными. Враждебность порождает ответные дейс…'
- `02_mahabharata-sabhaparva:2.9.18-25` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tathā samudrāścatvāro nadī bhāgīrathī ca yā । kālindī vidiśā veṇṇā narmadā vegavāhinī ॥18॥…'
  - ru: 'Также и четыре океана, и река Бхагиратхи, и (реки) Калинди, Видиша, Венна и Нармада, быстр…'
- `03_mahabharata-aranyakaparva:3.1.1-7` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'evaṃ dyūtajitāḥ pārthāḥ kopitāśca durātmabhiḥ । dhārtarāṣṭraiḥ sahāmātyairnikṛtyā dvijasat…'
  - ru: 'Итак, нечестивые сыновья Дхритараштры с советниками своими плутовски обыграли Партхов в ко…'
- `03_mahabharata-aranyakaparva:3.259.25` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'gandharvadevāsurato yakṣarākṣasatastathā । sarpakinnarabhūtebhyo na me bhūyātparābhavaḥ ॥2…'
  - ru: 'Пусть не смогут меня одолеть ни гандхарвы, ни боги, ни асуры, ни якши, ни ракшасы, ни демо…'
- `03_mahabharata-aranyakaparva:3.99.8-11` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tāndṛṣṭvā dravato bhītānsahasrākṣaḥ purandaraḥ । vṛtre vivardhamāne ca kaśmalaṃ mahadāviśa…'
  - ru: 'Тысячеокий Разрушитель городов, видя, что они бегут в страхе, а Вритра торжествует, впал в…'
- `04_mahabharata-virataparva:4.1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kathaṃ virāṭanagare mama pūrvapitāmahāḥ । ajñātavāsamuṣitā duryodhanabhayārditāḥ ॥1॥'
  - ru: 'Как жили мои предки, оставаясь неузнанными, в городе (царя) Вираты, мучимые страхом перед …'
- `04_mahabharata-virataparva:4.39.21-23` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tataḥ pārthaṃ sa vairāṭirabhyavādayadantikāt । ahaṃ bhūmiñjayo nāma nāmnāhamapi cottaraḥ ॥…'
  - ru: 'Тогда, (подойдя) ближе к Партхе, тот сын Вираты почтительно приветствовал его (и сказал): …'
- `04_mahabharata-virataparva:4.9.8-13` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'pañcānāṃ pāṇḍuputrāṇāṃ jyeṣṭho rājā yudhiṣṭhiraḥ । tasyāṣṭaśatasāhasrā gavāṃ vargāḥ śataṃ …'
  - ru: 'Среди пятерых сыновей Панду царь Юдхиштхира — старший. У него было (много) видов скота: од…'
- `05_mahabharata-udyogaparva:5.1.1-9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kṛtvā vivāhaṃ tu kurupravīrāstadābhimanyormuditasvapakṣāḥ । viśramya catvāryuṣasaḥ pratītā…'
  - ru: 'Отпраздновав свадьбу Абхиманью, могучие потомки Куру вместе с восторженными своими сторонн…'
- `05_mahabharata-udyogaparva:5.196.11-19` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'te samena pathā yātvā yotsyamānā mahārathāḥ । kurukṣetrasya paścārdhe vyavatiṣṭhanta daṃśi…'
  - ru: 'И те могучие воины на колесницах, облаченные в доспехи, двигаясь по ровному пути, располож…'
- `05_mahabharata-udyogaparva:5.99.9-16` — sa_ok=True ru_ok=True → **PASS**
  - sa: "suvarṇacūḍo nāgāśī dāruṇaścaṇḍatuṇḍakaḥ । analaścānilaścaiva viśālākṣo'tha kuṇḍalī ॥9॥ kāś…"
  - ru: '(Вот их имена): Суварначуда, Нагашин, Даруна и Чандатундака, Анала и Анила, Вишалакша и Ку…'
- `06_mahabharata-bhishmaparva:6.1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kathaṃ yuyudhire vīrāḥ kurupāṇḍavasomakāḥ । pārthivāśca mahābhāgā nānādeśasamāgatāḥ ॥1॥'
  - ru: 'Как сражались герои — куру, Пандавы, Сомаки и [другие] цари, мужи великих судеб, сошедшиес…'
- `06_mahabharata-bhishmaparva:6.33.43` — sa_ok=False ru_ok=True → **FAIL**
  - sa: "pitāsi lokasya carācarasya tvamasya pūjyaśca gururgarīyān । БхГ 11.43 na tvatsamo'styabhya…"
  - ru: 'Ты — отец мира движущегося и недвижного, тот, кого чтить ему надлежит, и величайший учител…'
- `06_mahabharata-bhishmaparva:6.99.44-47` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tataḥ pravavṛte yuddhaṃ kurūṇāṃ pāṇḍavaiḥ saha । akṣadyūtakṛtaṃ rājansughoraṃ vaiśasaṃ tad…'
  - ru: 'Затем продолжилась битва куру с пандавами, о царь, тогдашней игрою в кости порожденная ужа…'
- `07_mahabharata-dronaparva:7.1.1-4` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tamapratimasattvaujobalavīryaparākramam । hataṃ devavrataṃ śrutvā pāñcālyena śikhaṇḍinā ॥1…'
  - ru: 'Услышав о том, что Деваврата, несравненный в мощи и стойкости своей, в силе, доблести и мо…'
- `07_mahabharata-dronaparva:7.170.15-23` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'prāduścakre tato drauṇirastraṃ nārāyaṇaṃ tadā । abhisandhāya pāṇḍūnāṃ pāñcālānāṃ ca vāhinī…'
  - ru: 'Тогда, нацеливаясь в войско пандавов и панчалов, сын Дроны вызвал к действию оружие Нараян…'
- `07_mahabharata-dronaparva:7.99.9-15` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'rathaiśca bahudhā chinnairdhvajaiścaiva viśāṃ pate । hayaiśca kanakāpīḍaiḥ patitaistatra m…'
  - ru: 'Из-за множества разбитых колесниц и срубленных знамен, о владыка народов, из-за павших там…'
- `08_mahabharata-karnaparva:8.1.1-3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tato droṇe hate rājanduryodhanamukhā nṛpāḥ । bhṛśamudvignamanaso droṇaputramupāgaman ॥1॥ t…'
  - ru: 'И вот, когда сражен был Дрона, о царь, владыки людей, возглавляемые Дурьодханой, явились, …'
- `08_mahabharata-karnaparva:8.33.55-56` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tathā tu vitate vyomni nisvanaṃ śuśruvurjanāḥ । vimānairapsaraḥsaṅghairgītavāditranisvanai…'
  - ru: 'И тогда услышали люди разлившийся в бескрайнем небе звук — то был звук пения и музыки, шум…'
- `08_mahabharata-karnaparva:8.9.5-10` — sa_ok=True ru_ok=True → **PASS**
  - sa: "vadhyamāne bale tasminsūtaputreṇa māriṣa । nakulo'bhyadravattūrṇaṃ sūtaputraṃ mahāraṇe ॥5॥…"
  - ru: 'когда Сын суты истреблял то войско, о почтенный, стремительно обрушился на него средь битв…'
- `09_mahabharata-shalyaparva:9.1.1-3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'evaṃ nipātite karṇe samare savyasācinā । alpāvaśiṣṭāḥ kuravaḥ kimakurvata vai dvija ॥1॥ ud…'
  - ru: 'После того как Карна был так сокрушен в сражении Савьясачином, что же делали кауравы, оста…'
- `09_mahabharata-shalyaparva:9.37.19-27` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'gayasya yajamānasya gayeṣveva mahākratum । āhūtā saritāṃ śreṣṭhā gayayajñe sarasvatī ॥19॥ …'
  - ru: 'В то время как (царь) Гайя совершал великое жертвоприношение в Гае, лучшая из рек, Сарасва…'
- `09_mahabharata-shalyaparva:9.9.8-12` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'prāvartata mahāraudraḥ saṅgrāmaḥ śoṇitodakaḥ । samārchaccitrasenena nakulo yuddhadurmadaḥ …'
  - ru: 'Накула, непобедимый в бою, сразился с Читрасеной. Оба они, превосходные лучники, нападая д…'
- `10_mahabharata-sauptikaparva:10.1.1-6` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tataste sahitā vīrāḥ prayātā dakṣiṇāmukhāḥ । upāstamayavelāyāṃ śibirābhyāśamāgatāḥ ॥1॥ vim…'
  - ru: 'В предзакатный час те герои, шедшие вместе, обратив свои лица к югу, приблизились к лагерю…'
- `10_mahabharata-sauptikaparva:10.3.1-8` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kṛpasya vacanaṃ śrutvā dharmārthasahitaṃ śubham । aśvatthāmā mahārāja duḥkhaśokasamanvitaḥ…'
  - ru: 'Выслушав благую речь Крипы, сообразную с дхармой и артхой, впал в тоску Ашваттхаман от (об…'
- `10_mahabharata-sauptikaparva:10.9.59` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'vaiśampāyana uvāca । iti śrutvā sa nṛpatiḥ putrajñātivadhaṃ tadā । niḥśvasya dīrghamuṣṇaṃ …'
  - ru: 'Вайшампаяна сказал: Услышав такое о гибели своих сыновей и родичей, тот царь долго и жарко…'
- `11_mahabharata-striparva:11.1.1-3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'hate duryodhane caiva hate sainye ca sarvaśaḥ । dhṛtarāṣṭro mahārājaḥ śrutvā kimakaronmune…'
  - ru: 'Когда пал Дурьодхана и все войско было перебито, что предпринял, прослышав (об этом), вели…'
- `11_mahabharata-striparva:11.24.1-3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'somadattasutaṃ paśya yuyudhānena pātitam । vitudyamānaṃ vihagairbahubhirmādhavāntike ॥1॥ p…'
  - ru: 'Смотри, вот рядом — сын Сомадатты, сраженный Ююдханой; (тело) его клюют стаи птиц. Тут же …'
- `11_mahabharata-striparva:11.9.5-16` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'gāndhārī caiva śokārtā bharturvacanacoditā । saha kuntyā yato rājā saha strībhirupādravat …'
  - ru: 'А Гандхари, мучимая горем, повинуясь велению супруга, вместе с Кунти и другими женщинами п…'
- `12_mahabharata-shantiparva:12.1.1-12` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kṛtodakāste suhṛdāṃ sarveṣāṃ pāṇḍunandanāḥ । viduro dhṛtarāṣṭraśca sarvāśca bharatastriyaḥ…'
  - ru: 'Сыновья Панду, Видура, Дхритараштра и все женщины бхаратов совершили поминальное возлияние…'
- `12_mahabharata-shantiparva:12.267.27` — sa_ok=True ru_ok=False → **FAIL**
  - sa: 'jantuṣvekatameṣvevaṃ bhāvā ye vidhimāsthitāḥ । bhāvayorīpsitaṃ nityaṃ pratyakṣagamanaṃ dva…'
  - ru: '…'
- `12_mahabharata-shantiparva:12.99.9` — sa_ok=True ru_ok=False → **FAIL**
  - sa: 'kṣatradharme sthito bhūtvā yathāśāstraṃ yathāvidhi । udīkṣamāṇaḥ pṛtanāṃ jayāmi yudhi vāsa…'
  - ru: '…'
- `13_mahabharata-anushasanaparva:13.1.1` — sa_ok=True ru_ok=False → **FAIL**
  - sa: 'śamo bahuvidhākāraḥ sūkṣma uktaḥ pitāmaha । na ca me hṛdaye śāntirasti kṛtvedamīdṛśam ॥1॥'
  - ru: '…'
- `13_mahabharata-anushasanaparva:13.2.92` — sa_ok=True ru_ok=False → **FAIL**
  - sa: 'pātraṃ tvatithimāsādya śīlāḍhyaṃ yo na pūjayet । sa dattvā sukṛtaṃ tasya kṣapayeta hyanarc…'
  - ru: '…'
- `13_mahabharata-anushasanaparva:13.99.9` — sa_ok=True ru_ok=False → **FAIL**
  - sa: 'tasmāttāṃste pravakṣyāmi taḍāge ye guṇāḥ smṛtāḥ । yā ca tatra phalāvāptirṛṣibhiḥ samudāhṛt…'
  - ru: '…'
- `14_mahabharata-ashvamedhikaparva:14.1.1-3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kṛtodakaṃ tu rājānaṃ dhṛtarāṣṭraṃ yudhiṣṭhiraḥ । puraskṛtya mahābāhuruttatārākulendriyaḥ ॥…'
  - ru: 'Когда царь Дхритараштра совершил возлияния воды (для покойного Бхишмы), мощнодланный Юдхиш…'
- `14_mahabharata-ashvamedhikaparva:14.48.14-24` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'kiṃ svideveha dharmāṇāmanuṣṭheyatamaṃ smṛtam । vyāhatāmiva paśyāmo dharmasya vividhāṃ gati…'
  - ru: 'Какую из обязанностей в этом мире прежде всего исполнять следует? Путь дхармы столь развет…'
- `14_mahabharata-ashvamedhikaparva:14.96.9-15` — sa_ok=True ru_ok=True → **PASS**
  - sa: "sākṣāddṛṣṭo'si me krodha gaccha tvaṃ vigatajvaraḥ । na mamāpakṛtaṃ te'dya na manyurvidyate…"
  - ru: '«Воочию я увидел тебя, о Кродха! Ступай же бестрепетно, ибо нет на тебе отныне греха предо…'
- `15_mahabharata-ashramavasikaparva:15.1.1-3` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'prāpya rājyaṃ mahābhāgāḥ pāṇḍavā me pitāmahāḥ । kathamāsanmahārāje dhṛtarāṣṭre mahātmani ॥…'
  - ru: 'Обретя свое царство, как обошлись с великим царем Дхритараштрой, могучим душою, предки мои…'
- `15_mahabharata-ashramavasikaparva:15.33.33-37` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ityukto dharmarājaḥ sa vinivṛtya tataḥ punaḥ । rājño vaicitravīryasya tatsarvaṃ pratyaveda…'
  - ru: 'Услышав это, Царь праведности вернулся в обитель и поведал обо всём царственному сыну Вичи…'
- `15_mahabharata-ashramavasikaparva:15.9.7-12` — sa_ok=True ru_ok=True → **PASS**
  - sa: "tato'bravīnmahārāja kuntīputramupahvare । niṣaṇṇaṃ pāṇinā pṛṣṭhe saṃspṛśannambikāsutaḥ ॥7॥…"
  - ru: 'И тут сказал сын Амбики (стоявшему) подле него в печали сыну Кунти, коснувшись рукой его с…'
- `16_mahabharata-mausalaparva:16.1.1-6` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'ṣaṭtriṃśe tvatha samprāpte varṣe kauravanandanaḥ । dadarśa viparītāni nimittāni yudhiṣṭhir…'
  - ru: 'С наступлением тридцать шестого года (правления) Юдхиштхира, радость кауравов, стал замеча…'
- `16_mahabharata-mausalaparva:16.6.8-15` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'tāṃ sa vṛṣṇyandhakajalāṃ hayamīnāṃ rathoḍupām । vāditrarathaghoṣaughāṃ veśmatīrthamahāgrah…'
  - ru: 'Уподобилась Дварака грозной реке Вайтарани, влекомой арканами Времени, только водами (этой…'
- `16_mahabharata-mausalaparva:16.9.7-11` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'yaḥ sa meghavapuḥ śrīmānbṛhatpaṅkajalocanaḥ । sa kṛṣṇaḥ saha rāmeṇa tyaktvā dehaṃ divaṃ ga…'
  - ru: 'Осеняемый Шри, Кришна, тело которого - точно (грозовое) облако, а глаза - как огромные лот…'
- `17_mahabharata-mahaprasthanikaparva:17.1.1` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'evaṃ vṛṣṇyandhakakule śrutvā mausalamāhavam । pāṇḍavāḥ kimakurvanta tathā kṛṣṇe divaṃ gate…'
  - ru: 'Что предприняли Пандавы, услышав такое о битве на палицах меж вришниями и андхаками, когда…'
- `17_mahabharata-mahaprasthanikaparva:17.2.6` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'pakṣapāto mahānasyā viśeṣeṇa dhanañjaye । tasyaitatphalamadyaiṣā bhuṅkte puruṣasattama ॥6॥'
  - ru: 'Особенно сильной была ее благосклонность к (Арджуне) Завоевателю богатств, так что теперь …'
- `17_mahabharata-mahaprasthanikaparva:17.3.9` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'anāryamāryeṇa sahasranetra śakyaṃ kartuṃ duṣkarametadārya । mā me śriyā saṅgamanaṃ tayāstu…'
  - ru: 'О достойный Тысячеокий! Не подобает достойному совершать столь недостойное, злое деяние. Н…'
- `18_mahabharata-svargarohanikaparva:18.1.1-2` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'svargaṃ triviṣṭapaṃ prāpya mama pūrvapitāmahāḥ । pāṇḍavā dhārtarāṣṭrāśca kāni sthānāni bhe…'
  - ru: 'В каких местах пребывали предки мои Пандавы и сыновья Дхритараштры после того, как достигл…'
- `18_mahabharata-svargarohanikaparva:18.3.21-27` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'karmaṇāṃ tāta puṇyānāṃ jitānāṃ tapasā svayam । dānānāṃ ca mahābāho phalaṃ prāpnuhi pāṇḍava…'
  - ru: 'О Пандава мощнорукий! Обрети же плод благих деяний, что были самолично совершены (тобой) б…'
- `18_mahabharata-svargarohanikaparva:18.5.7-15` — sa_ok=True ru_ok=True → **PASS**
  - sa: 'gantavyaṃ karmaṇāmante sarveṇa manujādhipa । śṛṇu guhyamidaṃ rājandevānāṃ bharatarṣabha । …'
  - ru: 'Услышь, о царь, бык-бхарата, владыка людей, эту тайну богов - что надлежит пройти каждому …'

### Structural problems (18 files)

- `01_mahabharata-adiparva.jsonl`: L3: id mismatch '01_mahabharata-adiparva:1.1.0.comm1'; L3: group mismatch '01_mahabharata-adiparva:1.1.0'; L3: unexpected seg 'comm1'; L4: id mismatch '01_mahabharata-adiparva:1.1.0.comm2'; L4: group mismatch '01_mahabharata-adiparva:1.1.0'
- `02_mahabharata-sabhaparva.jsonl`: L1: chapter '1' != book 2; L3: id mismatch '02_mahabharata-sabhaparva:2.1.1-2.comm1'; L3: group mismatch '02_mahabharata-sabhaparva:2.1.1-2'; L3: unexpected seg 'comm1'; L4: id mismatch '02_mahabharata-sabhaparva:2.1.1-2.comm2'
- `03_mahabharata-aranyakaparva.jsonl`: L1: chapter '1' != book 3; L3: id mismatch '03_mahabharata-aranyakaparva:3.1.1-7.comm1'; L3: group mismatch '03_mahabharata-aranyakaparva:3.1.1-7'; L3: unexpected seg 'comm1'; L4: id mismatch '03_mahabharata-aranyakaparva:3.1.1-7.comm2'
- `04_mahabharata-virataparva.jsonl`: L1: chapter '1' != book 4; L3: id mismatch '04_mahabharata-virataparva:4.1.1.comm1'; L3: group mismatch '04_mahabharata-virataparva:4.1.1'; L3: unexpected seg 'comm1'; L4: id mismatch '04_mahabharata-virataparva:4.1.1.comm2'
- `05_mahabharata-udyogaparva.jsonl`: L1: chapter '1' != book 5; L3: id mismatch '05_mahabharata-udyogaparva:5.1.1-9.comm1'; L3: group mismatch '05_mahabharata-udyogaparva:5.1.1-9'; L3: unexpected seg 'comm1'; L4: id mismatch '05_mahabharata-udyogaparva:5.1.1-9.comm2'

