import { formatLocalBusinessOsmTagValue } from '#src-core/utils/localBusinessOsmLabels'

/**
 * Famille de tag OSM (cle) pour chaque type de commerce (valeur).
 * Aligne sur les filtres d'import OSM (amenity, shop, craft, office, ...).
 */
export const LOCAL_BUSINESS_OSM_TAG_BY_TYPE: Record<string, string> = {
  restaurant: 'amenity',
  cafe: 'amenity',
  bar: 'amenity',
  pub: 'amenity',
  fast_food: 'amenity',
  bank: 'amenity',
  pharmacy: 'amenity',
  dentist: 'amenity',
  doctors: 'amenity',
  clinic: 'amenity',
  veterinary: 'amenity',
  driving_school: 'amenity',
  car_wash: 'amenity',
  car_rental: 'amenity',
  fuel: 'amenity',
  bicycle_rental: 'amenity',
  marketplace: 'amenity',
  hotel: 'tourism',
  guest_house: 'tourism',
  motel: 'tourism',
  hostel: 'tourism',
  camp_site: 'tourism',
  museum: 'tourism',
  attraction: 'tourism',
  fitness_centre: 'leisure',
  sports_centre: 'leisure',
  golf_course: 'leisure',
  spa: 'leisure',
}

/**
 * Libelles francais des types OSM (valeur du tag : shop=*, amenity=*, etc.).
 * Liste elargie pour couvrir les commerces courants en France.
 */
export const LOCAL_BUSINESS_OSM_TYPE_LABELS: Record<string, string> = {
  ...buildAmenityLabels(),
  ...buildShopLabels(),
  ...buildCraftLabels(),
  ...buildOfficeLabels(),
  ...buildHealthcareLabels(),
  ...buildTourismLabels(),
  ...buildLeisureLabels(),
}

/**
 * Item de filtre / select pour un type OSM.
 */
export type LocalBusinessOsmTypeSelectItem = {
  label: string
  value: string
}

/**
 * @returns {Record<string, string>} Libelles amenity.
 */
function buildAmenityLabels(): Record<string, string> {
  const types: string[] = [
    'restaurant',
    'cafe',
    'bar',
    'pub',
    'fast_food',
    'bank',
    'pharmacy',
    'dentist',
    'doctors',
    'clinic',
    'veterinary',
    'driving_school',
    'car_wash',
    'car_rental',
    'fuel',
    'bicycle_rental',
    'marketplace',
    'ice_cream',
    'biergarten',
    'food_court',
    'nightclub',
    'cinema',
    'theatre',
    'library',
    'post_office',
    'atm',
    'bureau_de_change',
    'money_transfer',
    'charging_station',
    'parking',
    'hospital',
    'nursing_home',
    'social_facility',
    'kindergarten',
    'school',
    'university',
    'college',
    'language_school',
    'music_school',
    'dancing_school',
    'prep_school',
  ]
  const labels: Record<string, string> = {
    restaurant: 'Restaurant',
    cafe: 'Cafe',
    bar: 'Bar',
    pub: 'Pub',
    fast_food: 'Restauration rapide',
    bank: 'Banque',
    pharmacy: 'Pharmacie',
    dentist: 'Dentiste',
    doctors: 'Medecin',
    clinic: 'Clinique',
    veterinary: 'Veterinaire',
    driving_school: 'Auto-ecole',
    car_wash: 'Lavage auto',
    car_rental: 'Location de vehicules',
    fuel: 'Station-service',
    bicycle_rental: 'Location de velos',
    marketplace: 'Marche couvert',
    ice_cream: 'Glacier',
    biergarten: 'Biergarten',
    food_court: 'Aire de restauration',
    nightclub: 'Discotheque',
    cinema: 'Cinema',
    theatre: 'Theatre',
    library: 'Bibliotheque',
    post_office: 'Bureau de poste',
    atm: 'Distributeur automatique',
    bureau_de_change: 'Bureau de change',
    money_transfer: 'Transfert d argent',
    charging_station: 'Borne de recharge',
    parking: 'Parking',
    hospital: 'Hopital',
    nursing_home: 'EHPAD / maison de retraite',
    social_facility: 'Etablissement social',
    kindergarten: 'Creche / maternelle',
    school: 'Ecole',
    university: 'Universite',
    college: 'Enseignement superieur',
    language_school: 'Ecole de langues',
    music_school: 'Ecole de musique',
    dancing_school: 'Ecole de danse',
    prep_school: 'Soutien scolaire',
  }
  for (const type of types) {
    if (!labels[type]) {
      labels[type] = formatLocalBusinessOsmTagValue(type)
    }
    LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] = 'amenity'
  }
  return labels
}

/**
 * @returns {Record<string, string>} Libelles shop.
 */
function buildShopLabels(): Record<string, string> {
  const entries: Array<[string, string]> = [
    ['supermarket', 'Supermarche'],
    ['convenience', 'Epicerie / suprette'],
    ['bakery', 'Boulangerie'],
    ['pastry', 'Patisserie'],
    ['butcher', 'Boucherie'],
    ['deli', 'Traiteur / epicerie fine'],
    ['seafood', 'Poissonnerie'],
    ['cheese', 'Fromagerie'],
    ['chocolate', 'Chocolaterie'],
    ['coffee', 'Torrefaction / cafe'],
    ['tea', 'Magasin de the'],
    ['wine', 'Caviste'],
    ['alcohol', 'Magasin d alcools'],
    ['beverages', 'Boissons'],
    ['farm', 'Magasin a la ferme'],
    ['greengrocer', 'Primeur'],
    ['frozen_food', 'Surgeles'],
    ['dairy', 'Cremerie'],
    ['health_food', 'Bio / alimentation saine'],
    ['organic', 'Magasin bio'],
    ['variety_store', 'Magasin a prix bas'],
    ['department_store', 'Grand magasin'],
    ['mall', 'Centre commercial'],
    ['boutique', 'Boutique'],
    ['clothes', 'Vetements'],
    ['shoes', 'Chaussures'],
    ['jewelry', 'Bijouterie'],
    ['watch', 'Horlogerie'],
    ['bag', 'Maroquinerie / sacs'],
    ['leather', 'Cuir'],
    ['tailor', 'Tailleur'],
    ['dry_cleaning', 'Pressing'],
    ['laundry', 'Laverie'],
    ['hairdresser', 'Coiffeur'],
    ['beauty', 'Institut de beaute'],
    ['cosmetics', 'Cosmetiques'],
    ['perfumery', 'Parfumerie'],
    ['chemist', 'Parapharmacie'],
    ['optician', 'Opticien'],
    ['electronics', 'Electromenager / electronique'],
    ['mobile_phone', 'Telephonie mobile'],
    ['computer', 'Informatique'],
    ['appliance', 'Electromenager'],
    ['hardware', 'Quincaillerie / bricolage'],
    ['doityourself', 'Bricolage'],
    ['paint', 'Peinture / decoration'],
    ['garden_centre', 'Jardinerie'],
    ['florist', 'Fleuriste'],
    ['pet', 'Animalerie'],
    ['toys', 'Jouets'],
    ['books', 'Librairie'],
    ['stationery', 'Papeterie'],
    ['newsagent', 'Presse / tabac'],
    ['music', 'Musique'],
    ['video', 'Video / DVD'],
    ['video_games', 'Jeux video'],
    ['games', 'Jeux'],
    ['sports', 'Articles de sport'],
    ['bicycle', 'Velo'],
    ['car', 'Concession automobile'],
    ['car_parts', 'Pieces auto'],
    ['car_repair', 'Garage / reparation auto'],
    ['tyres', 'Pneus'],
    ['furniture', 'Meubles'],
    ['houseware', 'Articles de maison'],
    ['gift', 'Cadeaux'],
    ['charity', 'Association / friperie solidaire'],
    ['second_hand', 'Depot-vente / occasion'],
    ['ticket', 'Billetterie'],
    ['travel_agency', 'Agence de voyage'],
    ['estate_agent', 'Agence immobiliere'],
    ['funeral_directors', 'Pompes funebres'],
    ['tobacco', 'Tabac'],
    ['e-cigarette', 'Cigarette electronique'],
    ['nutrition_supplements', 'Complements alimentaires'],
    ['medical_supply', 'Matériel medical'],
    ['hearing_aids', 'Audioprothese'],
    ['bed', 'Literie'],
    ['carpet', 'Moquette / sols'],
    ['curtain', 'Rideaux / stores'],
    ['fabric', 'Mercerie / tissus'],
    ['interior_decoration', 'Decoration interieure'],
    ['lighting', 'Luminaires'],
    ['kitchen', 'Cuisiniste'],
    ['bathroom_furnishing', 'Salle de bain'],
    ['tiles', 'Carrelage'],
    ['copyshop', 'Reprographie'],
    ['printing', 'Imprimerie'],
    ['photo', 'Photographie'],
    ['camera', 'Photo / camera'],
    ['art', 'Art / galeries'],
    ['craft', 'Artisanat'],
    ['religion', 'Articles religieux'],
    ['outdoor', 'Outdoor / randonnee'],
    ['fishing', 'Peche'],
    ['hunting', 'Chasse'],
    ['weapons', 'Armes'],
    ['agrarian', 'Agro-equipement'],
    ['pet_grooming', 'Toilettage'],
    ['vacant', 'Local vacant'],
  ]
  const labels: Record<string, string> = {}
  for (const [type, label] of entries) {
    labels[type] = label
    LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] = 'shop'
  }
  return labels
}

/**
 * @returns {Record<string, string>} Libelles craft.
 */
function buildCraftLabels(): Record<string, string> {
  const entries: Array<[string, string]> = [
    ['plumber', 'Plombier'],
    ['electrician', 'Electricien'],
    ['carpenter', 'Menuisier'],
    ['painter', 'Peintre'],
    ['hvac', 'Chauffage / climatisation'],
    ['roofer', 'Couvreur'],
    ['locksmith', 'Serrurier'],
    ['glazier', 'Vitrier'],
    ['photographer', 'Photographe'],
    ['builder', 'Constructeur / macon'],
    ['gardener', 'Jardinier'],
    ['handyman', 'Bricoleur / depannage'],
    ['electronics_repair', 'Reparation electronique'],
    ['shoemaker', 'Cordonnier'],
    ['tailor', 'Tailleur'],
    ['bakery', 'Boulanger (artisan)'],
    ['brewery', 'Brasserie artisanale'],
    ['winery', 'Vigneron'],
    ['cleaning', 'Nettoyage'],
    ['upholsterer', 'Tapissier'],
    ['stonemason', 'Tailleur de pierre'],
    ['scaffolder', 'Echafaudeur'],
    ['insulation', 'Isolation'],
    ['tiler', 'Carreleur'],
    ['window_construction', 'Menuiserie fenetres'],
    ['floorer', 'Pose de sols'],
    ['kitchen_builder', 'Cuisiniste (artisan)'],
  ]
  const labels: Record<string, string> = {}
  for (const [type, label] of entries) {
    labels[type] = label
    LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] = 'craft'
  }
  return labels
}

/**
 * @returns {Record<string, string>} Libelles office.
 */
function buildOfficeLabels(): Record<string, string> {
  const entries: Array<[string, string]> = [
    ['company', 'Entreprise / siege'],
    ['insurance', 'Assurance'],
    ['lawyer', 'Avocat'],
    ['accountant', 'Expert-comptable'],
    ['employment_agency', 'Agence d interim / recrutement'],
    ['estate_agent', 'Agence immobiliere'],
    ['travel_agent', 'Agence de voyage'],
    ['architect', 'Architecte'],
    ['engineering', 'Bureau d etudes'],
    ['advertising_agency', 'Agence de communication'],
    ['notary', 'Notaire'],
    ['financial', 'Conseil financier'],
    ['tax_advisor', 'Conseil fiscal'],
    ['consulting', 'Conseil'],
    ['ngo', 'Association / ONG'],
    ['government', 'Administration'],
    ['union', 'Syndicat'],
    ['association', 'Association'],
    ['logistics', 'Logistique'],
    ['courier', 'Messagerie / coursier'],
    ['it', 'Informatique / SSII'],
    ['surveyor', 'Geometre'],
    ['property_management', 'Gestion locative'],
  ]
  const labels: Record<string, string> = {}
  for (const [type, label] of entries) {
    labels[type] = label
    LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] = 'office'
  }
  return labels
}

/**
 * @returns {Record<string, string>} Libelles healthcare.
 */
function buildHealthcareLabels(): Record<string, string> {
  const entries: Array<[string, string]> = [
    ['doctor', 'Medecin'],
    ['dentist', 'Dentiste'],
    ['physiotherapist', 'Kinesitherapeute'],
    ['psychotherapist', 'Psychologue / therapeute'],
    ['laboratory', 'Laboratoire d analyses'],
    ['optometrist', 'Optometriste'],
    ['podiatrist', 'Podologue'],
    ['speech_therapist', 'Orthophoniste'],
    ['occupational_therapist', 'Ergotherapeute'],
    ['midwife', 'Sage-femme'],
    ['nurse', 'Infirmier'],
    ['vaccination_centre', 'Centre de vaccination'],
    ['blood_donation', 'Don du sang'],
    ['alternative', 'Medecine alternative'],
    ['beauty', 'Soins esthetiques medicaux'],
  ]
  const labels: Record<string, string> = {}
  for (const [type, label] of entries) {
    labels[type] = label
    LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] = 'healthcare'
  }
  return labels
}

/**
 * @returns {Record<string, string>} Libelles tourism.
 */
function buildTourismLabels(): Record<string, string> {
  const entries: Array<[string, string]> = [
    ['hotel', 'Hotel'],
    ['guest_house', 'Chambre d hotes'],
    ['motel', 'Motel'],
    ['hostel', 'Auberge de jeunesse'],
    ['camp_site', 'Camping'],
    ['museum', 'Musee'],
    ['attraction', 'Attraction touristique'],
    ['information', 'Office de tourisme'],
    ['viewpoint', 'Point de vue'],
    ['theme_park', 'Parc d attractions'],
    ['gallery', 'Galerie'],
    ['apartment', 'Location saisonniere'],
    ['chalet', 'Chalet'],
  ]
  const labels: Record<string, string> = {}
  for (const [type, label] of entries) {
    labels[type] = label
    LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] = 'tourism'
  }
  return labels
}

/**
 * @returns {Record<string, string>} Libelles leisure.
 */
function buildLeisureLabels(): Record<string, string> {
  const entries: Array<[string, string]> = [
    ['fitness_centre', 'Salle de sport'],
    ['sports_centre', 'Complexe sportif'],
    ['golf_course', 'Golf'],
    ['spa', 'Spa'],
    ['swimming_pool', 'Piscine'],
    ['stadium', 'Stade'],
    ['pitch', 'Terrain de sport'],
    ['playground', 'Aire de jeux'],
    ['dance', 'Ecole de danse'],
    ['bowling_alley', 'Bowling'],
    ['escape_game', 'Escape game'],
    ['amusement_arcade', 'Salle d arcades'],
  ]
  const labels: Record<string, string> = {}
  for (const [type, label] of entries) {
    labels[type] = label
    LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] = 'leisure'
  }
  return labels
}

/**
 * Libelle francais d un type OSM (valeur du tag).
 * @param {string | null | undefined} osmType - Valeur OSM (ex. bakery, restaurant).
 * @param {string | null | undefined} [legacyCategoryTag] - Ancienne cle de tag (shop, amenity) si pas de sous-type.
 * @returns {string} Libelle affichable.
 */
export const getLocalBusinessOsmTypeLabel: (
  osmType: string | null | undefined,
  legacyCategoryTag?: string | null | undefined,
) => string = (osmType: string | null | undefined, legacyCategoryTag?: string | null | undefined): string => {
  const type: string = (osmType ?? '').trim()
  if (type) {
    return LOCAL_BUSINESS_OSM_TYPE_LABELS[type] ?? formatLocalBusinessOsmTagValue(type)
  }
  const tag: string = (legacyCategoryTag ?? '').trim()
  if (!tag) {
    return '-'
  }
  const legacyLabels: Record<string, string> = {
    amenity: 'Commerce / service (amenity)',
    shop: 'Commerce (shop)',
    craft: 'Artisan (craft)',
    office: 'Bureau (office)',
    healthcare: 'Sante (healthcare)',
    tourism: 'Tourisme',
    leisure: 'Loisirs',
    other: 'Autre',
  }
  return legacyLabels[tag] ?? formatLocalBusinessOsmTagValue(tag)
}

/**
 * Cle de tag OSM (amenity, shop, ...) pour un type donne.
 * @param {string | null | undefined} osmType - Valeur OSM.
 * @returns {string | null} Cle de tag ou null.
 */
export const getLocalBusinessOsmTagFamily: (osmType: string | null | undefined) => string | null = (
  osmType: string | null | undefined,
): string | null => {
  const type: string = (osmType ?? '').trim()
  if (!type) {
    return null
  }
  return LOCAL_BUSINESS_OSM_TAG_BY_TYPE[type] ?? null
}

/**
 * Options triees pour filtres et selects (types OSM connus).
 * @returns {LocalBusinessOsmTypeSelectItem[]} Liste label / value.
 */
export const buildLocalBusinessOsmTypeFilterItems: () => LocalBusinessOsmTypeSelectItem[] =
  (): LocalBusinessOsmTypeSelectItem[] =>
    Object.entries(LOCAL_BUSINESS_OSM_TYPE_LABELS)
      .map(
        ([value, label]: [string, string]): LocalBusinessOsmTypeSelectItem => ({
          value,
          label,
        }),
      )
      .sort((a: LocalBusinessOsmTypeSelectItem, b: LocalBusinessOsmTypeSelectItem): number =>
        a.label.localeCompare(b.label, 'fr'),
      )
